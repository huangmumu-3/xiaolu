"""
意见箱 - 收集用户反馈，帮助改进小陆
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import threading
from core.database import CompanionDB

feedback_bp = Blueprint('feedback', __name__)

# 全局意见数据库
feedback_db_lock = threading.Lock()
feedback_db = None


def get_feedback_db():
    """获取意见数据库"""
    global feedback_db
    if feedback_db is None:
        feedback_db = CompanionDB('./data/feedback.db')
        feedback_db.conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                type TEXT DEFAULT 'suggestion',
                content TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                reply TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        """)
        feedback_db.conn.commit()
    return feedback_db


@feedback_bp.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """提交意见"""
    data = request.json
    user_id = data.get('user_id', 'anonymous')
    content = data.get('content', '').strip()
    feedback_type = data.get('type', 'suggestion')

    if not content:
        return jsonify({'success': False, 'message': '内容不能为空'}), 400

    if len(content) < 5:
        return jsonify({'success': False, 'message': '内容太短了，请多说一些'}), 400

    db = get_feedback_db()
    db.conn.execute(
        """INSERT INTO feedback (user_id, type, content, created_at)
           VALUES (?, ?, ?, ?)""",
        (user_id, feedback_type, content, datetime.now().isoformat())
    )
    db.conn.commit()

    return jsonify({
        'success': True,
        'message': '感谢你的反馈！我会认真看的 💌'
    })


@feedback_bp.route('/api/feedback', methods=['GET'])
def get_feedback_list():
    """获取意见列表（仅管理员）"""
    user_id = request.args.get('user_id')
    feedback_type = request.args.get('type')
    status = request.args.get('status')

    db = get_feedback_db()

    query = "SELECT * FROM feedback WHERE 1=1"
    params = []

    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)

    if feedback_type:
        query += " AND type = ?"
        params.append(feedback_type)

    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY created_at DESC LIMIT 50"

    rows = db.conn.execute(query, params).fetchall()

    return jsonify([{
        'id': r['id'],
        'type': r['type'],
        'content': r['content'],
        'status': r['status'],
        'reply': r['reply'],
        'created_at': r['created_at']
    } for r in rows])


@feedback_bp.route('/api/feedback/<int:fid>', methods=['GET'])
def get_feedback_detail(fid):
    """获取单条意见"""
    db = get_feedback_db()
    row = db.conn.execute(
        "SELECT * FROM feedback WHERE id = ?", (fid,)
    ).fetchone()

    if not row:
        return jsonify({'error': '未找到'}), 404

    return jsonify(dict(row))


@feedback_bp.route('/api/feedback/<int:fid>/reply', methods=['POST'])
def reply_feedback(fid):
    """回复意见"""
    data = request.json
    reply = data.get('reply', '').strip()

    db = get_feedback_db()
    db.conn.execute(
        "UPDATE feedback SET reply = ?, status = 'replied', updated_at = ? WHERE id = ?",
        (reply, datetime.now().isoformat(), fid)
    )
    db.conn.commit()

    return jsonify({'success': True})


@feedback_bp.route('/api/feedback/<int:fid>/resolve', methods=['POST'])
def resolve_feedback(fid):
    """标记为已处理"""
    db = get_feedback_db()
    db.conn.execute(
        "UPDATE feedback SET status = 'resolved', updated_at = ? WHERE id = ?",
        (datetime.now().isoformat(), fid)
    )
    db.conn.commit()

    return jsonify({'success': True})
