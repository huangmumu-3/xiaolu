"""
回望系统 - 定期主动提起历史话题
"我记得你三周前说过..."
"""
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv
import openai

load_dotenv()


class Lookback:
    """回望 - 主动提起历史话题"""

    def __init__(self, db, graph=None):
        self.db = db
        self.graph = graph
        self.client = openai.OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )

    # ─── 1. 找到值得回望的历史事件 ────────────────────────

    def find_lookback_candidates(self) -> List[Dict]:
        """找到值得主动提起的历史事件"""
        candidates = []

        # 1. 有待跟进但超过3天没提的事项
        three_days_ago = (datetime.now() - timedelta(days=3)).isoformat()
        rows = self.db.conn.execute("""
            SELECT * FROM followups
            WHERE status = 'pending' AND created_at < ?
            ORDER BY urgency DESC, created_at ASC
            LIMIT 5
        """, (three_days_ago,)).fetchall()

        for row in rows:
            candidates.append({
                'type': 'followup',
                'topic': row['topic'],
                'context': row['context'],
                'created_at': row['created_at'],
                'id': row['id'],
                'days_ago': (datetime.now() - datetime.fromisoformat(row['created_at'])).days
            })

        # 2. 重要记忆（7天前、30天前的里程碑）
        for days in [7, 14, 30, 90]:
            start = (datetime.now() - timedelta(days=days+3)).isoformat()
            end = (datetime.now() - timedelta(days=days-3)).isoformat()
            rows = self.db.conn.execute("""
                SELECT * FROM memories
                WHERE created_at BETWEEN ? AND ?
                AND importance >= 7
                ORDER BY importance DESC
                LIMIT 2
            """, (start, end)).fetchall()

            for row in rows:
                candidates.append({
                    'type': 'memory',
                    'topic': row['event_summary'],
                    'emotion': row['emotion'],
                    'created_at': row['created_at'],
                    'days_ago': days,
                    'importance': row['importance']
                })

        return candidates

    def generate_lookback_message(self, candidate: Dict) -> str:
        """生成回望消息"""
        days = candidate.get('days_ago', 0)
        time_desc = self._days_to_desc(days)

        if candidate['type'] == 'followup':
            prompt = f"""你是小陆，一个陪伴用户的朋友。

{time_desc}，用户提到了「{candidate['topic']}」：
"{candidate['context'][:100]}"

现在你想主动问问后续。生成一句温暖的问候（30字以内）：
- 用"我记得你{time_desc}提到..."开头
- 自然地问"后来怎么样了？"
- 不要评判，只是关心

只输出这句话。"""
        else:
            prompt = f"""你是小陆，一个陪伴用户的朋友。

{time_desc}，用户经历了：「{candidate['topic']}」（情绪：{candidate.get('emotion', '')}）

你想主动提起这件事，看看用户现在的感受。生成一句温暖的话（30字以内）：
- 用"我记得你{time_desc}..."开头
- 可以问"现在回想起来，感觉怎么样？"
- 温暖，不评判

只输出这句话。"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return f"我记得你{time_desc}提到「{candidate['topic'][:20]}」，后来怎么样了？"

    def _days_to_desc(self, days: int) -> str:
        if days <= 1:
            return "昨天"
        elif days <= 7:
            return f"{days}天前"
        elif days <= 14:
            return "上周"
        elif days <= 30:
            return f"{days // 7}周前"
        elif days <= 60:
            return "上个月"
        else:
            return f"{days // 30}个月前"

    def get_due_lookback(self) -> Optional[Dict]:
        """获取当前最应该回望的一条"""
        candidates = self.find_lookback_candidates()
        if not candidates:
            return None

        # 优先级：followup > 重要记忆，时间越久越优先
        candidates.sort(key=lambda x: (
            0 if x['type'] == 'followup' else 1,
            -x.get('days_ago', 0)
        ))

        top = candidates[0]
        message = self.generate_lookback_message(top)
        return {
            'candidate': top,
            'message': message
        }
