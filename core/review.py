"""
时间回望系统 - 每周/每月总结
"""
import os
from datetime import datetime, timedelta
from typing import List, Dict
import openai
from dotenv import load_dotenv

load_dotenv()


class TimeReview:
    def __init__(self, db):
        self.db = db
        self.client = openai.OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )

    def get_period_conversations(self, days: int = 7) -> List[Dict]:
        """获取最近N天的对话"""
        from datetime import datetime
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        rows = self.db.conn.execute(
            "SELECT * FROM conversations WHERE timestamp > ? ORDER BY timestamp ASC",
            (cutoff,)
        ).fetchall()
        
        return [dict(row) for row in rows]

    def get_period_memories(self, days: int = 7) -> List[Dict]:
        """获取最近N天的记忆"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        rows = self.db.conn.execute(
            "SELECT * FROM memories WHERE created_at > ? ORDER BY importance DESC",
            (cutoff,)
        ).fetchall()
        
        return [dict(row) for row in rows]

    def generate_daily_summary(self) -> str:
        """生成今日总结"""
        conversations = self.get_period_conversations(days=1)
        memories = self.get_period_memories(days=1)

        if not conversations:
            return "今天还没有对话记录呢~"

        # 统计情绪
        emotion_stats = {}
        for m in memories:
            emotion = m.get('emotion', '未知')
            emotion_stats[emotion] = emotion_stats.get(emotion, 0) + 1

        prompt = f"""你是小陆，帮用户总结今天的重要时刻。

今日数据：
- 对话 {len(conversations)} 次
- 记住的重要事件 {len(memories)} 条
- 情绪分布：{emotion_stats}

重要事件：
{chr(10).join([f"• {m['event_summary']}" for m in memories[:5]])}

对话摘要：
{chr(10).join([f"用户：{c['user_input'][:50]}" for c in conversations[-5:]])}

请用温暖、简短的语气写一段总结（100字以内）：
1. 今天最重要的一件事
2. 你的感受/观察
3. 一个温柔的小问题引向明天

格式：
📋 今日小结
今天我们聊了...
我感觉...
明天可以聊聊...？"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"今天我们聊了 {len(conversations)} 次，记住了一些重要的事~"

    def generate_weekly_review(self) -> str:
        """生成周回顾"""
        conversations = self.get_period_conversations(days=7)
        memories = self.get_period_memories(days=7)

        if not conversations:
            return "这周还没有对话记录呢，我们从今天开始创造一些吧~"

        # 统计情绪分布
        emotion_stats = {}
        for m in memories:
            emotion = m.get('emotion', '未知')
            emotion_stats[emotion] = emotion_stats.get(emotion, 0) + 1

        # 构建上下文
        context_parts = []
        context_parts.append(f"这周共对话 {len(conversations)} 次")
        
        if emotion_stats:
            top_emotions = sorted(emotion_stats.items(), key=lambda x: -x[1])[:3]
            context_parts.append(f"情绪关键词：{', '.join([f'{e}({c}次)' for e, c in top_emotions])}")

        # 重要事件
        if memories:
            context_parts.append("\n这周发生的重要事情：")
            for m in memories[:5]:
                context_parts.append(f"• {m['event_summary']}")

        # 对话摘要
        conversation_texts = "\n".join([
            f"用户：{c['user_input']}\n小陆：{c['ai_response']}"
            for c in conversations[-10:]
        ])

        prompt = f"""你是一个温暖的朋友，帮用户回顾这一周。

本周统计：
{chr(10).join(context_parts)}

最近对话：
{conversation_texts}

请用温暖、共情的语气，写一段周回顾，包含：
1. 对这周的整体感受
2. 注意到用户的变化或成长
3. 一个温柔的小问题，引导用户思考下周

150字左右，用第一人称"你"称呼用户。"""

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )

        return response.choices[0].message.content

    def generate_monthly_review(self) -> str:
        """生成月回顾"""
        conversations = self.get_period_conversations(days=30)
        memories = self.get_period_memories(days=30)

        if len(conversations) < 3:
            return "这个月我们的对话还不多，等积累多一些再来做月回顾吧~"

        # 情绪趋势
        emotion_stats = {}
        for m in memories:
            emotion = m.get('emotion', '未知')
            emotion_stats[emotion] = emotion_stats.get(emotion, 0) + 1

        prompt = f"""帮用户做一个月度回顾。

这个月的数据：
- 对话 {len(conversations)} 次
- 记住的重要事件 {len(memories)} 条
- 情绪分布：{emotion_stats}

重要事件：
{chr(10).join([f"• {m['event_summary']}" for m in memories[:10]])}

请写一段温暖的月回顾：
1. 这个月的整体感受
2. 用户的成长和变化
3. 对下个月的期待和鼓励

200字左右。"""

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600
        )

        return response.choices[0].message.content

    def should_send_review(self) -> tuple[bool, str]:
        """检查是否应该发送回顾"""
        now = datetime.now()
        
        # 周回顾：每周日晚8点
        if now.weekday() == 6 and now.hour == 20:
            return True, "weekly"
        
        # 月回顾：每月最后一天晚8点
        if now.day == (now.replace(day=28) + timedelta(days=4)).day - 1 and now.hour == 20:
            # 简单判断：每月28号之后
            if now.day >= 28 and now.hour == 20:
                return True, "monthly"
        
        return False, ""

    def should_send_daily_summary(self) -> bool:
        """判断是否应该发送每日总结"""
        now = datetime.now()
        
        # 检查上次总结时间
        last_summary = self.db.conn.execute(
            "SELECT MAX(created_at) as last FROM daily_summaries"
        ).fetchone()
        
        if not last_summary or not last_summary['last']:
            return True
        
        from datetime import timedelta
        last_time = datetime.fromisoformat(last_summary['last'])
        
        # 每天只发一次，晚上9点-11点之间
        if 21 <= now.hour <= 23:
            if (now - last_time).days >= 1:
                return True
        
        return False

    def save_daily_summary(self, summary: str):
        """保存每日总结"""
        self.db.conn.execute(
            "INSERT INTO daily_summaries (summary, created_at) VALUES (?, ?)",
            (summary, datetime.now().isoformat())
        )
        self.db.conn.commit()

    def check_and_generate_review(self) -> str:
        """检查并生成回顾"""
        should_send, review_type = self.should_send_review()
        
        if not should_send:
            return ""
        
        if review_type == "weekly":
            return self.generate_weekly_review()
        elif review_type == "monthly":
            return self.generate_monthly_review()
        
        return ""
