"""
指导系统 - 渐进开放指导
触发条件：
1. 数据积累 >= 30天
2. 同一话题重复抱怨 >= 3次
形式："我注意到一个模式，想和你聊聊"
"""
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv
import openai

load_dotenv()


class Guidance:
    """渐进式指导系统"""

    def __init__(self, db, graph=None):
        self.db = db
        self.graph = graph
        self.client = openai.OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )

    def is_guidance_enabled(self, user_id: str) -> bool:
        """检查指导模式是否开启"""
        row = self.db.conn.execute(
            "SELECT guidance_enabled FROM guidance_settings WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        # 默认关闭，需要积累够才开启
        if row is None:
            return False
        return bool(row['guidance_enabled'])

    def set_guidance_enabled(self, user_id: str, enabled: bool):
        """设置指导模式"""
        now = datetime.now().isoformat()
        self.db.conn.execute("""
            INSERT OR REPLACE INTO guidance_settings (user_id, guidance_enabled, updated_at)
            VALUES (?, ?, ?)
        """, (user_id, int(enabled), now))
        self.db.conn.commit()

    # ─── 1. 数据积累检查 ──────────────────────────────────

    def check_data_readiness(self, user_id: str) -> Dict:
        """检查是否满足指导开启条件"""
        # 总对话天数
        row = self.db.conn.execute(
            "SELECT COUNT(DISTINCT DATE(timestamp)) as days FROM conversations"
        ).fetchone()
        total_days = row['days'] if row else 0

        # 总对话次数
        row = self.db.conn.execute(
            "SELECT COUNT(*) as count FROM conversations"
        ).fetchone()
        total_convs = row['count'] if row else 0

        # 总记忆条数
        row = self.db.conn.execute(
            "SELECT COUNT(*) as count FROM memories"
        ).fetchone()
        total_memories = row['count'] if row else 0

        # 第一条对话时间
        row = self.db.conn.execute(
            "SELECT MIN(timestamp) as first FROM conversations"
        ).fetchone()
        first_conversation = row['first'] if row else None

        days_since_start = 0
        if first_conversation:
            start = datetime.fromisoformat(first_conversation)
            days_since_start = (datetime.now() - start).days

        return {
            'total_days': total_days,
            'total_conversations': total_convs,
            'total_memories': total_memories,
            'days_since_start': days_since_start,
            'ready': days_since_start >= 30 and total_convs >= 20,
            'progress': min(1.0, days_since_start / 30)
        }

    def should_offer_guidance(self, user_id: str) -> bool:
        """是否应该向用户开放指导模式"""
        readiness = self.check_data_readiness(user_id)
        if not readiness['ready']:
            return False
        # 已开启则不需要再提醒
        return not self.is_guidance_enabled(user_id)

    # ─── 2. 卡点检测 ──────────────────────────────────────

    def detect_stuck_points(self, user_id: str) -> List[Dict]:
        """检测用户重复抱怨的卡点"""
        stuck_points = []

        # 方式1：话题统计（SQLite）
        rows = self.db.conn.execute("""
            SELECT keyword, SUM(count) as total, MAX(last_seen) as last_seen
            FROM topic_stats
            GROUP BY keyword
            HAVING total >= 2
            ORDER BY total DESC
            LIMIT 10
        """).fetchall()

        for row in rows:
            stuck_points.append({
                'topic': row['keyword'],
                'mention_count': row['total'],
                'last_seen': row['last_seen'],
                'source': 'sqlite'
            })

        # 方式2：Neo4j话题节点
        if self.graph:
            try:
                result = self.graph.get_most_discussed_topics(user_id, limit=5)
                for r in result:
                    # 避免重复
                    existing = [s['topic'] for s in stuck_points]
                    if r['topic'] not in existing and r.get('count', 0) >= 2:
                        stuck_points.append({
                            'topic': r['topic'],
                            'mention_count': r['count'],
                            'last_seen': None,
                            'source': 'neo4j'
                        })
            except Exception:
                pass

        # 方式3：LLM 分析近30天对话模式
        conversations = self.db.conn.execute(
            "SELECT user_input, timestamp FROM conversations ORDER BY timestamp DESC LIMIT 100"
        ).fetchall()

        if conversations:
            conv_text = "\n".join([
                f"[{c['timestamp'][:10]}] {c['user_input']}"
                for c in conversations[:50]
            ])

            prompt = f"""分析这些对话，找出用户反复纠结的话题。

对话记录：
{conv_text}

请识别用户反复提到（2次以上）的烦恼、纠结或未解决的问题。

以JSON格式返回（严格JSON）：
{{"stuck_points": [
  {{"topic": "话题关键词", "count": 出现次数, "pattern": "用户纠结的具体模式"}}
]}}
如果找不到明显卡点，返回 {{"stuck_points": []}}"""

            try:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500
                )
                import json
                # 清理可能的markdown包裹
                if text.startswith('```'):
                    text = text.split('\n', 1)[1] if '\n' in text else text
                    text = text.rsplit('```', 1)[0] if '```' in text else text
                result = json.loads(text)
                llm_points = result.get("stuck_points", [])
                for p in llm_points:
                    existing = [s['topic'] for s in stuck_points]
                    if p['topic'] not in existing and p.get('count', 0) >= 2:
                        stuck_points.append({
                            'topic': p['topic'],
                            'mention_count': p.get('count', 3),
                            'last_seen': None,
                            'pattern': p.get('pattern', ''),
                            'source': 'llm'
                        })
            except Exception:
                pass

        return stuck_points

    # ─── 3. 生成指导对话 ──────────────────────────────────

    def generate_guidance_message(self, user_id: str, stuck_point: Dict) -> str:
        """生成指导消息（不是"你应该"，而是"我注意到一个模式"）"""
        topic = stuck_point['topic']
        count = stuck_point.get('mention_count', stuck_point.get('count', 0))
        pattern = stuck_point.get('pattern', '')

        # 找到相关对话
        conversations = self.db.conn.execute(
            "SELECT user_input, ai_response, timestamp FROM conversations ORDER BY timestamp ASC"
        ).fetchall()

        related = []
        for c in conversations:
            if topic in c['user_input'] or topic in c['ai_response']:
                related.append(f"[{c['timestamp'][:10]}] 用户：{c['user_input'][:60]}")

        history_context = "\n".join(related[-5:]) if related else ""

        prompt = f"""你是小陆，一个陪伴用户很久的朋友。你注意到了用户反复纠结的事情。

话题：{topic}
提到次数：{count}次
纠结模式：{pattern}

相关对话记录：
{history_context}

请生成一段"指导式"对话开头（50字以内）：
- ❌ 不要说"你应该..."
- ❌ 不要给直接建议
- ✅ 用"我注意到..."开头
- ✅ 表达关心，不带评判
- ✅ 用提问引导用户自己思考
- ✅ 可以温和地指出重复的模式

只输出这段话，不要解释。"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return f"我注意到「{topic}」是你反复提到的事情，你已经聊了{count}次了...想和我聊聊这个吗？"

    # ─── 4. 综合检查 ──────────────────────────────────────

    def check_and_generate(self, user_id: str) -> Optional[Dict]:
        """综合检查，返回指导建议"""
        # 检查是否已开启
        if not self.is_guidance_enabled(user_id):
            if self.should_offer_guidance(user_id):
                readiness = self.check_data_readiness(user_id)
                return {
                    'type': 'offer',
                    'message': f"我们已经聊了{readiness['days_since_start']}天、{readiness['total_conversations']}次对话了。我发现有些话题你反复提到，想和我聊聊吗？（你可以随时关闭这个功能）",
                    'readiness': readiness
                }
            return None

        # 使用报告逻辑检测（包含 LLM 分析）
        conversations = self.db.conn.execute(
            "SELECT user_input, timestamp FROM conversations ORDER BY timestamp ASC"
        ).fetchall()

        if not conversations:
            return None

        conv_text = "\n".join([
            f"[{c['timestamp'][:10]}] {c['user_input']}"
            for c in conversations[:50]
        ])

        prompt = f"""你是小陆。分析这些对话，找出用户反复纠结的话题。

{conv_text}

请识别反复出现（2次以上）的烦恼或纠结。以JSON返回（严格JSON）：
{{"stuck_points": [{{"topic": "话题", "count": 次数, "pattern": "纠结模式"}}]}}
找不到则返回 {{"stuck_points": []}}"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            import json
            text = response.choices[0].message.content.strip()
            if text.startswith('```'):
                text = text.split('\n', 1)[1] if '\n' in text else text
                text = text.rsplit('```', 1)[0] if '```' in text else text
            result = json.loads(text)
            stuck_points = result.get("stuck_points", [])
        except Exception:
            stuck_points = []

        if not stuck_points:
            return None

        top = stuck_points[0]
        message = self.generate_guidance_message(user_id, top)

        return {
            'type': 'guidance',
            'topic': top['topic'],
            'count': top.get('count', 0),
            'message': message,
            'all_stuck_points': stuck_points
        }

    def get_stuck_points_report(self, user_id: str) -> str:
        """获取卡点报告"""
        stuck_points = self.detect_stuck_points(user_id)

        if not stuck_points:
            # 直接用 LLM 分析所有对话
            conversations = self.db.conn.execute(
                "SELECT user_input, timestamp FROM conversations ORDER BY timestamp ASC"
            ).fetchall()

            if conversations:
                conv_text = "\n".join([
                    f"[{c['timestamp'][:10]}] {c['user_input']}"
                    for c in conversations[:50]
                ])

                prompt = f"""你是小陆。分析这些对话，找出用户反复纠结的话题。

{conv_text}

请识别反复出现（2次以上）的烦恼或纠结。以JSON返回（严格JSON）：
{{"stuck_points": [{{"topic": "话题", "count": 次数, "pattern": "纠结模式"}}]}}
找不到则返回 {{"stuck_points": []}}"""

                try:
                    response = self.client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=500
                    )
                    import json
                    text = response.choices[0].message.content.strip()
                    if text.startswith('```'):
                        text = text.split('\n', 1)[1] if '\n' in text else text
                        text = text.rsplit('```', 1)[0] if '```' in text else text
                    result = json.loads(text)
                    stuck_points = result.get("stuck_points", [])

                except Exception:
                    pass

        if not stuck_points:
            return "目前没有发现明显的卡点，你最近状态不错~"

        lines = ["🔍 我注意到你反复在聊这些话题：\n"]
        for i, sp in enumerate(stuck_points, 1):
            pattern = sp.get('pattern', '')
            line = f"{i}. 「{sp['topic']}」- 提到{sp.get('mention_count', sp.get('count', '?'))}次"
            if pattern:
                line += f"\n   模式：{pattern}"
            lines.append(line)

        lines.append("\n如果你觉得哪个话题想深入聊聊，可以告诉我~")

        return "\n".join(lines)
