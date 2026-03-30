"""
见证系统 - 记录并明确指出用户的变化
"我注意到你变了..."
"""
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv
import openai

load_dotenv()


class ChangeWitness:
    """见证 - 明确指出用户的成长与变化"""

    def __init__(self, db, graph=None):
        self.db = db
        self.graph = graph
        self.client = openai.OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )

    # ─── 1. 对比不同时间段的情绪 ──────────────────────────

    def compare_emotion_periods(self) -> Optional[Dict]:
        """对比前后两段时间的情绪变化"""
        total = self.db.conn.execute("SELECT COUNT(*) as cnt FROM memories").fetchone()['cnt']
        if total < 4:
            return None

        # 前半段
        half = total // 2
        early = self.db.conn.execute("""
            SELECT emotion, event_summary, created_at FROM memories
            ORDER BY created_at ASC LIMIT ?
        """, (half,)).fetchall()

        # 后半段
        recent = self.db.conn.execute("""
            SELECT emotion, event_summary, created_at FROM memories
            ORDER BY created_at DESC LIMIT ?
        """, (half,)).fetchall()

        if not early or not recent:
            return None

        return {
            'early': [dict(r) for r in early],
            'recent': [dict(r) for r in recent]
        }

    # ─── 2. LLM 识别变化 ──────────────────────────────────

    def detect_change(self) -> Optional[str]:
        """用 LLM 识别用户的变化，生成见证消息"""
        periods = self.compare_emotion_periods()
        if not periods:
            return None

        early_text = "\n".join([
            f"[{m['created_at'][:10]}] {m['event_summary']} (情绪:{m['emotion']})"
            for m in periods['early']
        ])
        recent_text = "\n".join([
            f"[{m['created_at'][:10]}] {m['event_summary']} (情绪:{m['emotion']})"
            for m in periods['recent']
        ])

        prompt = f"""你是小陆，一个见证用户成长的朋友。

以前的记录：
{early_text}

最近的记录：
{recent_text}

请分析用户的变化，生成一段"见证"消息（50字以内）：
- 明确指出你观察到的变化（情绪、态度、行动）
- 用"我注意到..."或"我看到你..."开头
- 不评判好坏，只是如实描述
- 如果有积极变化，可以温暖地指出
- 如果没有明显变化，返回空字符串

只输出这段话，没有变化就输出空字符串。"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150
            )
            result = response.choices[0].message.content.strip()
            return result if len(result) > 5 else None
        except Exception:
            return None

    # ─── 3. 里程碑识别 ────────────────────────────────────

    def detect_milestone(self, user_input: str, ai_response: str) -> Optional[str]:
        """识别当前对话是否是里程碑时刻"""
        # 先看记忆里有没有相关的历史
        memories = self.db.get_memories(limit=20)
        if not memories:
            return None

        history = "\n".join([
            f"[{m['created_at'][:10]}] {m['event_summary']} (情绪:{m['emotion']})"
            for m in memories
        ])

        prompt = f"""你是小陆，一个见证用户成长的朋友。

用户历史记录：
{history}

用户刚刚说：{user_input}

判断：这句话是否是一个"里程碑"——相比历史记录，有明显的突破、转变或成长？

如果是，生成一句见证消息（30字以内）：
- 用"我看到你..."开头
- 对比过去，指出这个变化
- 温暖，不夸张

如果不是里程碑，输出空字符串。
只输出这句话或空字符串。"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100
            )
            result = response.choices[0].message.content.strip()
            return result if len(result) > 5 else None
        except Exception:
            return None

    # ─── 4. 生成完整见证报告 ──────────────────────────────

    def generate_witness_report(self) -> str:
        """生成完整的见证报告"""
        memories = self.db.get_memories(limit=30)
        if not memories:
            return "我们还在认识彼此的路上，等积累更多对话，我会更了解你~"

        all_text = "\n".join([
            f"[{m['created_at'][:10]}] {m['event_summary']} (情绪:{m['emotion']})"
            for m in memories
        ])

        prompt = f"""你是小陆，一个见证用户成长的朋友。

以下是你记录的用户经历：
{all_text}

请生成一段"见证报告"（100字以内）：
1. 指出你观察到的情绪变化轨迹
2. 指出用户反复出现的主题
3. 如果有成长或突破，明确指出
4. 语气温暖，像一个老朋友在回顾

格式：
🌱 我见证了你的...
📍 你一直在关注...
✨ 我注意到你...（变化）"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return "我一直在这里，见证着你的每一步~"
