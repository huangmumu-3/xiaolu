"""
时间回望模块 - 生成周期性总结
"""
from datetime import datetime, timedelta
from core.database import CompanionDB
from collections import Counter
import re


class TimeReflection:
    def __init__(self, db: CompanionDB):
        self.db = db

    def get_weekly_summary(self) -> dict:
        """生成本周总结"""
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()

        # 获取本周对话
        conversations = self.db.conn.execute(
            "SELECT * FROM conversations WHERE timestamp >= ? ORDER BY timestamp",
            (week_ago,)
        ).fetchall()

        if not conversations:
            return {"has_data": False}

        # 提取关键词（简单版：统计高频词）
        all_text = " ".join([c["user_input"] for c in conversations])
        words = re.findall(r'[\u4e00-\u9fff]{2,}', all_text)  # 中文词
        top_topics = Counter(words).most_common(5)

        # 获取本周记忆
        memories = self.db.conn.execute(
            "SELECT * FROM memories WHERE created_at >= ? ORDER BY importance DESC",
            (week_ago,)
        ).fetchall()

        # 情绪统计
        emotions = [m["emotion"] for m in memories if m["emotion"]]
        emotion_count = Counter(emotions)

        return {
            "has_data": True,
            "period": "本周",
            "conversation_count": len(conversations),
            "top_topics": [t[0] for t in top_topics[:3]],
            "main_emotion": emotion_count.most_common(1)[0][0] if emotion_count else "平静",
            "important_events": [m["event_summary"] for m in memories[:3]]
        }

    def format_summary(self, summary: dict) -> str:
        """格式化总结为文本"""
        if not summary["has_data"]:
            return "这周我们还没有聊过天呢 :)"

        text = f"📅 {summary['period']}回顾\n\n"
        text += f"我们聊了 {summary['conversation_count']} 次。\n\n"

        if summary["top_topics"]:
            text += f"你提到最多的是：{' / '.join(summary['top_topics'])}\n\n"

        if summary["main_emotion"]:
            text += f"整体情绪：{summary['main_emotion']}\n\n"

        if summary["important_events"]:
            text += "重要的事：\n"
            for i, event in enumerate(summary["important_events"], 1):
                text += f"{i}. {event}\n"

        return text
