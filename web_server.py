"""
Web服务器 - 支持多用户、微信访问
"""
import os
import uuid
import hashlib
import threading
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from dotenv import load_dotenv
from core.database import CompanionDB
from core.engine import CompanionEngine

load_dotenv()

app = Flask(__name__,
             template_folder='./templates',
             static_folder='./static')
CORS(app)
app.secret_key = os.getenv('SECRET_KEY', str(uuid.uuid4()))

# 注册可视化蓝图
try:
    from web_viz import viz_bp
    app.register_blueprint(viz_bp)
except Exception as e:
    print(f"⚠️ 可视化蓝图注册失败: {e}")

# 注册意见箱蓝图
try:
    from feedback import feedback_bp
    app.register_blueprint(feedback_bp)
except Exception as e:
    print(f"⚠️ 意见箱蓝图注册失败: {e}")



# 技能中心 API
@app.route('/api/skills', methods=['GET'])
def skills_list():
    """获取技能列表"""
    from core.skillhub import SkillHub
    hub = SkillHub()
    return jsonify(hub.get_all_skills())

# 线程本地存储
local = threading.local()

def get_user_db():
    """获取线程本地的用户数据库连接"""
    if not hasattr(local, 'user_db'):
        local.user_db = CompanionDB('./data/users.db')
    return local.user_db

def get_user_id(openid: str = None) -> str:
    """获取或创建用户ID"""
    if openid:
        return f"wechat_{hashlib.md5(openid.encode()).hexdigest()[:8]}"
    return session.get('user_id', None)


def get_or_create_user(openid: str = None) -> str:
    """获取或创建用户，返回user_id"""
    user_db = get_user_db()
    user_id = get_user_id(openid)
    
    if not user_id:
        user_id = str(uuid.uuid4())[:8]
        session['user_id'] = user_id
    
    # 确保用户表存在
    user_db.conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            openid TEXT,
            created_at TEXT,
            last_seen TEXT,
            nickname TEXT DEFAULT '新朋友'
        )
    """)
    
    # 检查用户是否存在
    existing = user_db.conn.execute(
        "SELECT user_id FROM users WHERE user_id = ? OR openid = ?",
        (user_id, openid)
    ).fetchone()
    
    if not existing:
        user_db.conn.execute(
            "INSERT INTO users (user_id, openid, created_at, last_seen) VALUES (?, ?, ?, ?)",
            (user_id, openid, datetime.now().isoformat(), datetime.now().isoformat())
        )
        user_db.conn.commit()
    
    return user_id


# 用户引擎存储
user_engines = {}
user_engines_lock = threading.Lock()


def get_user_engine(user_id: str) -> CompanionEngine:
    """获取用户专属的引擎实例"""
    with user_engines_lock:
        if user_id not in user_engines:
            user_engines[user_id] = {
                'engine': CompanionEngine(user_id=user_id),
                'last_active': datetime.now()
            }
    
    user_engines[user_id]['last_active'] = datetime.now()
    return user_engines[user_id]['engine']


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/chat')
def chat_page():
    """聊天页面"""
    return render_template('chat.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """处理聊天消息"""
    data = request.json
    message = data.get('message', '').strip()
    openid = data.get('openid', None)
    image_data = data.get('image', None)
    
    if not message and not image_data:
        return jsonify({'error': '消息不能为空'}), 400
    
    user_id = get_or_create_user(openid)
    engine = get_user_engine(user_id)
    
    try:
        response = engine.chat(message, image_data=image_data)
        return jsonify({
            'response': response,
            'user_id': user_id
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/history', methods=['GET'])
def history():
    """获取对话历史"""
    openid = request.args.get('openid')
    user_id = get_or_create_user(openid) if openid else session.get('user_id')
    
    if not user_id:
        return jsonify([])
    
    engine = get_user_engine(user_id)
    history_data = engine.db.get_recent_conversations(limit=50)
    
    return jsonify([{
        'user': h['user_input'],
        'ai': h['ai_response'],
        'time': h['timestamp']
    } for h in history_data])


@app.route('/api/memories', methods=['GET'])
def memories():
    """获取记忆"""
    openid = request.args.get('openid')
    user_id = get_or_create_user(openid) if openid else session.get('user_id')
    
    if not user_id:
        return jsonify([])
    
    engine = get_user_engine(user_id)
    memories_data = engine.db.get_memories(limit=20)
    
    return jsonify([{
        'event': m['event_summary'],
        'emotion': m['emotion'],
        'time': m['created_at']
    } for m in memories_data])


@app.route('/api/witness/followups', methods=['GET'])
def followups():
    """获取待跟进事项"""
    openid = request.args.get('openid')
    user_id = get_or_create_user(openid) if openid else session.get('user_id')
    
    if not user_id:
        return jsonify([])
    
    engine = get_user_engine(user_id)
    followups_data = engine.witness.get_pending_followups()
    
    return jsonify([{
        'topic': f['topic'],
        'context': f['context'],
        'urgency': f['urgency']
    } for f in followups_data])


@app.route('/api/user/profile', methods=['GET'])
def user_profile():
    """获取用户信息"""
    openid = request.args.get('openid')
    user_id = get_or_create_user(openid) if openid else session.get('user_id')
    
    if not user_id:
        return jsonify({})
    
    engine = get_user_engine(user_id)
    
    # 统计
    conv_count = engine.db.conn.execute("SELECT COUNT(*) as c FROM conversations").fetchone()['c']
    memory_count = engine.db.conn.execute("SELECT COUNT(*) as c FROM memories").fetchone()['c']
    
    return jsonify({
        'user_id': user_id,
        'conversation_count': conv_count,
        'memory_count': memory_count,
        'guidance_enabled': engine.guidance.is_guidance_enabled(user_id)
    })


@app.route('/api/time/past', methods=['GET'])
def time_past():
    """查询过去某时间段的事件"""
    openid = request.args.get('openid')
    query = request.args.get('query', '最近30天发生了什么')
    
    user_id = get_or_create_user(openid) if openid else session.get('user_id')
    if not user_id:
        return jsonify({'error': '需要登录'}), 401
    
    engine = get_user_engine(user_id)
    result = engine.query_past(query)
    
    return jsonify({'result': result})


@app.route('/api/time/trend', methods=['GET'])
def time_trend():
    """查询话题趋势"""
    openid = request.args.get('openid')
    topic = request.args.get('topic', '')
    
    user_id = get_or_create_user(openid) if openid else session.get('user_id')
    if not user_id:
        return jsonify({'error': '需要登录'}), 401
    
    engine = get_user_engine(user_id)
    result = engine.get_topic_trend(topic)
    
    return jsonify({'result': result})


@app.route('/api/guidance/stuck', methods=['GET'])
def guidance_stuck():
    """获取卡点报告"""
    openid = request.args.get('openid')
    
    user_id = get_or_create_user(openid) if openid else session.get('user_id')
    if not user_id:
        return jsonify({'error': '需要登录'}), 401
    
    engine = get_user_engine(user_id)
    result = engine.guidance.get_stuck_points_report(user_id)
    
    return jsonify({'result': result})


@app.route('/api/guidance/check', methods=['GET'])
def guidance_check():
    """检查是否有指导建议"""
    openid = request.args.get('openid')
    
    user_id = get_or_create_user(openid) if openid else session.get('user_id')
    if not user_id:
        return jsonify({})
    
    engine = get_user_engine(user_id)
    result = engine.guidance.check_and_generate(user_id)
    
    if result:
        return jsonify(result)
    return jsonify({})


@app.route('/api/guidance/toggle', methods=['POST'])
def guidance_toggle():
    """开启/关闭指导模式"""
    openid = request.json.get('openid') if request.json else None
    
    user_id = get_or_create_user(openid) if openid else session.get('user_id')
    if not user_id:
        return jsonify({'error': '需要登录'}), 401
    
    engine = get_user_engine(user_id)
    current = engine.guidance.is_guidance_enabled(user_id)
    engine.guidance.set_guidance_enabled(user_id, not current)
    
    return jsonify({
        'enabled': not current,
        'message': '指导模式已开启' if not current else '指导模式已关闭'
    })
    openid = request.args.get('openid')
    user_id = get_or_create_user(openid) if openid else session.get('user_id')
    
    if not user_id:
        return jsonify({'is_new': True})
    
    user_db = get_user_db()
    user_db.conn.execute(
        "UPDATE users SET last_seen = ? WHERE user_id = ?",
        (datetime.now().isoformat(), user_id)
    )
    user_db.conn.commit()
    
    return jsonify({
        'user_id': user_id,
        'is_new': False
    })


@app.route('/api/user/name', methods=['POST'])
def set_name():
    """设置昵称"""
    data = request.json
    name = data.get('name', '新朋友')
    openid = data.get('openid')
    user_id = get_or_create_user(openid) if openid else session.get('user_id')
    
    if user_id:
        user_db = get_user_db()
        user_db.conn.execute(
            "UPDATE users SET nickname = ? WHERE user_id = ?",
            (name, user_id)
        )
        user_db.conn.commit()
    
    return jsonify({'success': True})


def run_server(port=None, debug=False):
    """启动服务器"""
    port = port or int(os.getenv('PORT', 8080))
    print(f"\n🌐 服务器启动: http://localhost:{port}")
    print(f"📱 微信访问: 复制上面网址到微信打开即可")
    app.run(host='0.0.0.0', port=port, debug=debug)


if __name__ == '__main__':
    run_server(debug=True)
