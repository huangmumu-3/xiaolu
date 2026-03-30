"""
见证者系统 - 主动记住并提起用户的变化
"""
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv
import openai

load_dotenv()


class Witness:
    """见证者 - 见证用户成长的陪伴者"""

    def __init__(self, db):
        self.db = db
        self.client = openai.OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )

    # ─── 1. 跟踪待跟进事项 ───────────────────────────────
    def add_followup(self, topic: str, context: str, urgency: str = "normal") -> int:
        now = datetime.now().isoformat()
        if urgency == "high":
            followup_at = (datetime.now() + timedelta(hours=2)).isoformat()
        else:
            followup_at = (datetime.now() + timedelta(days=1)).isoformat()

        cur = self.db.conn.execute(
            """INSERT INTO followups 
               (topic, context, urgency, followup_at, status, created_at)
               VALUES (?, ?, ?, ?, 'pending', ?)""",
            (topic, context, urgency, followup_at, now)
        )
        self.db.conn.commit()
        return cur.lastrowid

    def get_due_followups(self) -> List[Dict]:
        now = datetime.now().isoformat()
        rows = self.db.conn.execute(
            """SELECT * FROM followups 
               WHERE status = 'pending' AND followup_at <= ?
               ORDER BY urgency DESC, followup_at ASC""",
            (now,)
        ).fetchall()
        return [dict(row) for row in rows]

    def mark_followup_done(self, followup_id: int):
        self.db.conn.execute(
            "UPDATE followups SET status = 'done' WHERE id = ?",
            (followup_id,)
        )
        self.db.conn.commit()

    def get_pending_followups(self) -> List[Dict]:
        rows = self.db.conn.execute(
            """SELECT * FROM followups 
               WHERE status = 'pending' 
               ORDER BY urgency DESC, followup_at ASC"""
        ).fetchall()
        return [dict(row) for row in rows]

    # ─── 2. 话题频率统计 ─────────────────────────────────
    def track_topic(self, user_input: str) -> None:
        """记录话题出现次数"""
        import re
        words = re.findall(r'[\u4e00-\u9fff]{2,}', user_input)
        if not words:
            return

        for word in words[:5]:  # 最多记录5个关键词
            # 检查是否已存在
            existing = self.db.conn.execute(
                "SELECT * FROM topic_stats WHERE keyword = ? ORDER BY last_seen DESC LIMIT 1",
                (word,)
            ).fetchone()

            if existing:
                self.db.conn.execute(
                    """UPDATE topic_stats 
                       SET count = count + 1, last_seen = ?
                       WHERE id = ?""",
                    (datetime.now().isoformat(), existing['id'])
                )
            else:
                self.db.conn.execute(
                    "INSERT INTO topic_stats (keyword, count, last_seen) VALUES (?, 1, ?)",
                    (word, datetime.now().isoformat())
                )
        self.db.conn.commit()

    def get_topic_count(self, keyword: str) -> int:
        """获取话题出现次数"""
        row = self.db.conn.execute(
            "SELECT SUM(count) as total FROM topic_stats WHERE keyword LIKE ?",
            (f"%{keyword}%",)
        ).fetchone()
        return row['total'] if row and row['total'] else 0

    def get_top_topics(self, limit: int = 5) -> List[Dict]:
        """获取高频话题"""
        rows = self.db.conn.execute(
            """SELECT keyword, SUM(count) as count, MAX(last_seen) as last_seen
               FROM topic_stats 
               GROUP BY keyword 
               ORDER BY count DESC LIMIT ?""",
            (limit,)
        ).fetchall()
        return [dict(row) for row in rows]

    def detect_repeated_topic(self, user_input: str) -> Optional[Dict]:
        """检测是否在重复聊一个话题"""
        import re
        words = re.findall(r'[\u4e00-\u9fff]{2,}', user_input)
        if not words:
            return None

        for word in words[:3]:
            count = self.get_topic_count(word)
            if count >= 2:  # 聊过2次以上
                return {
                    'keyword': word,
                    'count': count,
                    'message': f"这个话题你已经和我聊过 {count} 次了呢"
                }
        return None

    # ─── 3. 情感变化检测 ─────────────────────────────────
    def detect_emotion_change(self) -> Optional[str]:
        """检测用户情绪是否有积极变化"""
        rows = self.db.conn.execute(
            """SELECT * FROM memories 
               ORDER BY created_at DESC LIMIT 20"""
        ).fetchall()
        memories = [dict(r) for r in rows]

        if len(memories) < 2:
            return None

        positive_keywords = ['开心', '顺利', '突破', '进步', '成长', '达成', '解决', '高兴', '兴奋']
        negative_keywords = ['焦虑', '迷茫', '疲惫', '难过', '担心', '烦恼', '困惑']

        recent = memories[:5]
        older = memories[5:10] if len(memories) > 5 else []

        recent_positive = any(any(k in m['emotion'] for k in positive_keywords) for m in recent)
        recent_negative = any(any(k in m['emotion'] for k in negative_keywords) for m in recent)
        older_negative = any(any(k in m['emotion'] for k in negative_keywords) for m in older)

        # 从负面变积极
        if recent_positive and older_negative:
            latest_positive = next(m for m in recent if any(k in m['emotion'] for k in positive_keywords))
            return f"注意到你最近心情好像不错，「{latest_positive['event_summary'][:20]}」听起来是个好进展~"

        # 一直很积极
        if recent_positive and not recent_negative:
            if len(recent) >= 3:
                return "感觉你最近状态挺好的，一直有开心的事情发生呢"

        return None

    # ─── 4. 相似话题检测 ─────────────────────────────────
    def find_related_conversations(self, user_input: str, limit: int = 3) -> List[Dict]:
        import re
        words = re.findall(r'[\u4e00-\u9fff]{2,}', user_input)
        if not words:
            return []

        conversations = self.db.get_recent_conversations(limit=50)
        related = []

        for conv in conversations:
            text = conv['user_input'] + ' ' + (conv['ai_response'] or '')
            matches = sum(1 for w in words if w in text)
            if matches >= 2:
                related.append({**conv, 'matches': matches})

        related.sort(key=lambda x: -x['matches'])
        return related[:limit]

    def generate_witness_notice(self, related: List[Dict]) -> Optional[str]:
        if not related:
            return None

        history = "\n".join([
            f"[{i+1}] {c['user_input'][:80]}... (说过: {c['timestamp'][:10]})"
            for i, c in enumerate(related)
        ])

        prompt = f"""你是小陆，一个见证用户成长的陪伴者。

用户最近说了类似的话题，但之前也提过：

{history}

请生成一句温暖的提醒，引导用户回顾这段经历。
- 不要评判对错
- 可以说"我记得你之前也提到过..."
- 可以问"后来怎么样了？"或"现在感觉有什么不一样吗？"
- 30字以内，自然温暖

只输出这句话，不要解释。"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except:
            return None

    # ─── 5. 检测需要记录跟进的事项 ───────────────────────
    def detect_followup_triggers(self, user_input: str, ai_response: str) -> List[Dict]:
        prompt = f"""分析这段对话，判断是否有需要跟进的事项。

用户：{user_input}
小陆：{ai_response}

判断标准：
- 用户做了某个决定（换工作、创业、搬家等）→ 需要跟进"后来怎么样了"
- 用户表达了担忧或计划 → 需要跟进"进展如何"
- 用户提到了问题但还没解决 → 需要跟进"解决了吗"

以JSON格式返回：
{{"followups": [{{"topic": "...", "context": "...", "urgency": "normal"}}, ...]}}
如果没有，返回空列表。"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            import json
            result = json.loads(response.choices[0].message.content)
            return result.get("followups", [])
        except:
            return []

    # ─── 6. 综合检查 ─────────────────────────────────────
    def check_and_get_witness_messages(self) -> List[str]:
        messages = []

        # 到期跟进
        due = self.get_due_followups()
        for item in due[:2]:
            msg = f"你之前提到「{item['topic']}」...后来怎么样了？"
            messages.append(msg)
            self.mark_followup_done(item['id'])

        # 情感变化
        emotion_msg = self.detect_emotion_change()
        if emotion_msg:
            messages.append(emotion_msg)

        return messages

    def generate_context_for_chat(self, user_input: str) -> str:
        """为聊天生成见证者上下文"""
        parts = []

        # 1. 话题重复提醒
        repeated = self.detect_repeated_topic(user_input)
        if repeated:
            parts.append(f"💡 {repeated['message']}")

        # 2. 相关历史对话
        related = self.find_related_conversations(user_input)
        if related:
            notice = self.generate_witness_notice(related)
            if notice:
                parts.append(f"👁️ {notice}")

        return "\n".join(parts) if parts else ""
