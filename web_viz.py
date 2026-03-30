"""
Web 可视化 API - 小陆记忆、时间线、话题统计
"""
from flask import Blueprint, request, jsonify
from core.engine import CompanionEngine
import os

viz_bp = Blueprint('viz', __name__)


def get_engine(openid):
    """获取该用户的引擎实例"""
    return CompanionEngine(user_id=openid)


# ─── 1. 记忆时间线 API ─────────────────────────────────

@viz_bp.route('/api/timeline', methods=['GET'])
def get_timeline():
    """获取记忆时间线"""
    openid = request.args.get('openid', 'default')
    engine = get_engine(openid)
    
    memories = engine.db.get_memories(limit=50)
    result = []
    
    for m in memories:
        result.append({
            'id': m['id'],
            'summary': m['event_summary'],
            'emotion': m['emotion'],
            'importance': m['importance'],
            'created_at': m['created_at'][:10] if m['created_at'] else ''
        })
    
    engine.close()
    return jsonify(result)


# ─── 2. 话题统计 API ────────────────────────────────────

@viz_bp.route('/api/topics', methods=['GET'])
def get_topics():
    """获取话题统计"""
    openid = request.args.get('openid', 'default')
    engine = get_engine(openid)
    
    # 从 Neo4j 获取
    if engine.graph:
        try:
            topics = engine.graph.get_most_discussed_topics(openid, limit=15)
            if topics:
                engine.close()
                return jsonify(topics)
        except Exception:
            pass
    
    # 从 SQLite 获取
    rows = engine.db.conn.execute("""
        SELECT keyword, SUM(count) as count 
        FROM topic_stats 
        GROUP BY keyword 
        ORDER BY count DESC 
        LIMIT 15
    """).fetchall()
    
    result = [{'topic': r['keyword'], 'count': r['count']} for r in rows]
    engine.close()
    return jsonify(result)


# ─── 3. 情绪变化 API ───────────────────────────────────

@viz_bp.route('/api/emotions', methods=['GET'])
def get_emotions():
    """获取情绪变化趋势"""
    openid = request.args.get('openid', 'default')
    engine = get_engine(openid)
    
    memories = engine.db.get_memories(limit=100)
    
    # 按周分组
    from collections import defaultdict
    weeks = defaultdict(list)
    
    for m in memories:
        if m['created_at']:
            # 提取周
            date_str = m['created_at'][:10]
            import re
            match = re.match(r'(\d{4})-(\d{2})-(\d{2})', date_str)
            if match:
                year, month, day = match.groups()
                week = f"{year}-{int(month):02d}-W"
                from datetime import datetime
                d = datetime(int(year), int(month), int(day))
                week_num = (d.day - 1) // 7 + 1
                week_key = f"{year}-{int(month):02d}月第{week_num}周"
                weeks[week_key].append(m['emotion'])
    
    result = []
    for week, emotions in sorted(weeks.items()):
        emotion_count = defaultdict(int)
        for e in emotions:
            emotion_count[e] += 1
        top_emotion = max(emotion_count.items(), key=lambda x: x[1])[0] if emotion_count else '平静'
        result.append({
            'week': week,
            'emotion': top_emotion,
            'count': len(emotions)
        })
    
    engine.close()
    return jsonify(result)


# ─── 4. 见证报告 API ───────────────────────────────────

@viz_bp.route('/api/witness', methods=['GET'])
def get_witness():
    """获取见证报告"""
    openid = request.args.get('openid', 'default')
    engine = get_engine(openid)
    
    report = engine.change_witness.generate_witness_report()
    engine.close()
    
    return jsonify({'report': report})


# ─── 5. 卡点分析 API ───────────────────────────────────

@viz_bp.route('/api/stuck', methods=['GET'])
def get_stuck():
    """获取卡点分析"""
    openid = request.args.get('openid', 'default')
    engine = get_engine(openid)
    engine.guidance.set_guidance_enabled(openid, True)
    
    stuck = engine.guidance.get_stuck_points_report(openid)
    engine.close()
    
    return jsonify({'report': stuck})


# ─── 6. 历史回顾 API ───────────────────────────────────

@viz_bp.route('/api/review', methods=['GET'])
def get_review():
    """获取周/月回顾"""
    openid = request.args.get('openid', 'default')
    period = request.args.get('period', 'week')
    engine = get_engine(openid)
    
    if period == 'month':
        review = engine.review.generate_monthly_review()
    else:
        review = engine.review.generate_weekly_review()
    
    engine.close()
    return jsonify({'review': review})


# ─── 7. 回望消息 API ───────────────────────────────────

@viz_bp.route('/api/lookback', methods=['GET'])
def get_lookback():
    """获取回望消息"""
    openid = request.args.get('openid', 'default')
    engine = get_engine(openid)
    
    result = engine.lookback.get_due_lookback()
    engine.close()
    
    if result:
        return jsonify({
            'has_lookback': True,
            'message': result['message'],
            'topic': result['candidate'].get('topic', '')
        })
    return jsonify({'has_lookback': False})


# ─── 8. 统计数据概览 API ───────────────────────────────

@viz_bp.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计数据概览"""
    openid = request.args.get('openid', 'default')
    engine = get_engine(openid)
    
    # 对话数
    conv_count = engine.db.conn.execute(
        "SELECT COUNT(*) as cnt FROM conversations"
    ).fetchone()['cnt']
    
    # 记忆数
    mem_count = engine.db.conn.execute(
        "SELECT COUNT(*) as cnt FROM memories"
    ).fetchone()['cnt']
    
    # 待跟进数
    followup_count = len(engine.witness.get_pending_followups())
    
    # 指导模式
    guidance_on = engine.guidance.is_guidance_enabled(openid)
    
    engine.close()
    
    return jsonify({
        'conversations': conv_count,
        'memories': mem_count,
        'followups': followup_count,
        'guidance_enabled': guidance_on
    })
