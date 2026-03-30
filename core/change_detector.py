"""
变化识别模块 - 对比不同时间段的情绪和话题
"""
from datetime import datetime, timedelta
from core.database import CompanionDB
from collections import Counter


class ChangeDetector:
    def __init__(self, db: CompanionDB):
        self.db = db

    def detect_emotion_change(self, days_ago: int = 30) -> dict:
        """检测情绪变化"""
        now = datetime.now()
        mid_point = (now - timedelta(days=days_ago // 2)).isoformat()
        start_point = (now - timedelta(days=days_ago)).isoformat()

        # 前半段情绪
        early_emotions = self.db.conn.execute(
            "SELECT emotion FROM memories WHERE created_at >= ? AND created_at < ?",
            (start_point, mid_point)
        ).fetchall()

        # 后半段情绪
        recent_emotions = self.db.conn.execute(
            "SELECT emotion FROM memories WHERE created_at >= ?",
            (mid_point,)
        ).fetchall()

        early_count = Counter([e["emotion"] for e in early_emotions if e["emotion"]])
        recent_count = Counter([e["emotion"] for e in recent_emotions if e["emotion"]])

        return {
            "early_main": early_count.most_common(1)[0][0] if early_count else None,
            "recent_main": recent_count.most_common(1)[0][0] if recent_count else None,
            "has_change": bool(early_count and recent_count and
                              early_count.most_common(1)[0][0] != recent_count.most_common(1)[0][0])
        }

    def format_change_message(self, change: dict) -> str:
        """格式化变化消息"""
        if not change["has_change"]:
            return None

        return (f"我注意到，最近你的状态从「{change['early_main']}」"
                f"变成了「{change['recent_main']}」，发生了什么吗？")
