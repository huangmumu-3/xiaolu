"""
对话引擎 - 核心对话逻辑 (DeepSeek版本)
"""
import os
import openai
from dotenv import load_dotenv
from typing import List, Dict, Optional
from datetime import datetime
from core.database import CompanionDB
from core.memory import MemoryExtractor
from core.knowledge import format_knowledge_prompt
from core.proactive import ProactiveChecker
from core.witness import Witness
from core.review import TimeReview
from prompts.persona import SYSTEM_PROMPT

load_dotenv()


class CompanionEngine:
    def __init__(self, user_id: str = None, use_graph: bool = True):
        self.user_id = user_id or "default"
        db_path = f"./data/{self.user_id}.db"
        self.client = openai.OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
        self.db = CompanionDB(db_path)
        self.memory_extractor = MemoryExtractor()
        self.proactive = ProactiveChecker()
        self.witness = Witness(self.db)
        self.review = TimeReview(self.db)
        
        # Neo4j 图数据库
        self.graph = None
        if use_graph:
            try:
                from core.graph import EventGraph
                self.graph = EventGraph()
                self.graph.create_user(self.user_id)
            except Exception as e:
                print(f"⚠️ Neo4j 连接失败，使用 SQLite 模式: {e}")

        # 指导系统
        from core.guidance import Guidance
        self.guidance = Guidance(self.db, self.graph)

        # 回望系统
        from core.lookback import Lookback
        self.lookback = Lookback(self.db, self.graph)

        # 见证系统
        from core.change_witness import ChangeWitness
        self.change_witness = ChangeWitness(self.db, self.graph)

        # 嘴替教练
        from core.coach import SpeechCoach, SocialCoach, AITutor, SkillHandler
        self.speech_coach = SpeechCoach()
        self.social_coach = SocialCoach()
        self.ai_tutor = AITutor()
        self.skill_handler = SkillHandler()
        
        # 成长导师
        from core.growth import GrowthMentor, AILearningGuide
        self.growth_mentor = GrowthMentor()
        self.ai_guide = AILearningGuide()
        
        # 人味系统
        from core.humanity import HumanityEngine
        self.humanity = HumanityEngine()
        
        # AI知识助手
        from core.ai_knowledge import AIKnowledgeGuide
        self.ai_knowledge = AIKnowledgeGuide()
        
        self.skill_handler = SkillHandler()

    def _build_context(self) -> str:
        """构建上下文：最近对话 + 重要记忆"""
        context = []

        # 最近5条对话
        recent = self.db.get_recent_conversations(limit=5)
        if recent:
            context.append("## 最近的对话")
            for conv in reversed(list(recent)):
                context.append(f"用户：{conv['user_input']}")
                context.append(f"你：{conv['ai_response']}\n")

        # 重要记忆
        memories = self.db.get_memories(limit=10)
        if memories:
            context.append("\n## 你记得的重要事情")
            for mem in memories:
                context.append(f"- {mem['event_summary']} (情绪:{mem['emotion']})")

        return "\n".join(context)

    def chat(self, user_input: str, skip_witness: bool = False, image_data: str = None) -> str:
        """处理用户输入，返回回复"""
        # ─── 嘴替检测优先 ─────────────────────────────────
        # 检测是否需要嘴替
        if not skip_witness:
            # AI知识学习系统 - 分层教学法
            if self.ai_knowledge.is_ai_learning_question(user_input):
                from core.ai_knowledge import detect_industry
                # 先检测消息中是否包含行业关键词
                detected = detect_industry(user_input)
                # 如果检测到行业，记录下来（用于后续对话）
                if detected:
                    self.ai_knowledge.set_industry(detected)
                # 优先用检测到的行业，其次用已记住的行业
                industry = detected or self.ai_knowledge.get_industry()
                if self.ai_knowledge.should_teach_learning_path(user_input):
                    return self.ai_knowledge.show_learning_path(industry)
                return self.ai_knowledge.teach_concept(user_input, industry, depth="full")
            
            # 技能安装/管理
            if self.skill_handler.is_skill_request(user_input):
                # 先尝试直接处理（安装/卸载）
                result = self.skill_handler.handle(user_input)
                if result:
                    return result
                # 如果没有具体技能名，返回列表
                return self.skill_handler.get_available_skills_text()
            
            if self.speech_coach.is_speech_request(user_input):
                history = self._get_chat_history(limit=10)
                return self.speech_coach.coach(user_input, history)
            
            if self.social_coach.is_social_request(user_input):
                history = self._get_chat_history(limit=10)
                return self.social_coach.coach(user_input, history)
            
            if self.ai_tutor.is_ai_tutor_request(user_input):
                return self.ai_tutor.coach(user_input)
            
            # 成长导师 - 目标设定
            if self.growth_mentor.is_goal_setting(user_input):
                goal_info = self.growth_mentor.parse_goal(user_input)
                self._save_goal(user_input, goal_info)
                first_action = goal_info.get('micro_action', '')
                daily = self.growth_mentor.generate_daily_mission(goal_info, 1)
                response = "好的，我帮你记住了这个目标 🎯\n\n目标：" + goal_info.get('long_goal', '') + "\n\n" + daily + "\n\n---\n💡 今天的第一步：" + first_action + "\n\n我们每天完成一小步，30天后回来看，你会发现已经走了很远。"
                return response
            
            # AI学习引导 - 在自己行业中应用
            if 'AI' in user_input or '人工智能' in user_input or '学AI' in user_input or '用AI' in user_input:
                return self.ai_guide.guide_application(user_input)
        
        # ─── 图片识别 ─────────────────────────────────────
        if image_data:
            return self._handle_image(image_data, user_input or "请描述这张图片")
        
        context = self._build_context()
        knowledge = format_knowledge_prompt(user_input)

        # 见证者：检测相关历史对话和话题重复
        witness_context = ""
        if not skip_witness:
            # 记录话题
            self.witness.track_topic(user_input)
            # 生成见证提醒
            witness_context = self.witness.generate_context_for_chat(user_input)

        # 构建完整提示
        full_prompt = context

        # 加上见证者提醒
        if witness_context:
            full_prompt += f"\n\n{witness_context}"

        full_prompt += knowledge
        full_prompt += f"\n\n用户现在说：{user_input}"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": full_prompt}
        ]

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            max_tokens=1000
        )

        ai_response = response.choices[0].message.content

        # 保存对话
        conv_id = self.db.save_conversation(user_input, ai_response)

        # 提取记忆
        memory = self.memory_extractor.extract_memory(user_input, ai_response)
        if memory.get("is_important"):
            self.db.save_memory(
                summary=memory["summary"],
                emotion=memory["emotion"],
                importance=memory["importance"],
                conv_id=conv_id
            )

        # 见证者：检测并记录需要跟进的事项
        if not skip_witness:
            followups = self.witness.detect_followup_triggers(user_input, ai_response)
            for fu in followups:
                fu_id = self.witness.add_followup(
                    topic=fu.get("topic", ""),
                    context=fu.get("context", ""),
                    urgency=fu.get("urgency", "normal")
                )

            # 写入 Neo4j
            if self.graph:
                try:
                    import uuid
                    event_id = f"evt_{conv_id}"
                    summary = memory.get("summary", user_input[:50]) if memory.get("is_important") else user_input[:50]
                    emotion = memory.get("emotion", "")
                    
                    self.graph.add_event(
                        user_id=self.user_id,
                        event_id=event_id,
                        summary=summary,
                        emotion=emotion,
                        importance=memory.get("importance", 5) if memory.get("is_important") else 3
                    )
                    self.graph.link_conversation_to_event(conv_id, event_id)
                    if emotion:
                        self.graph.link_event_to_emotion(event_id, emotion)
                    
                    # 话题关联
                    for fu_item in followups:
                        topic = fu_item.get("topic", "")
                        if topic:
                            self.graph.link_topic_mentions(event_id, topic)
                except Exception:
                    pass

        return ai_response

    def _get_chat_history(self, limit: int = 10) -> str:
        """获取聊天历史用于上下文"""
        convs = self.db.get_recent_conversations(limit=limit)
        return "\n".join([
            f"用户：{c['user_input']}\n小陆：{c['ai_response']}"
            for c in convs
        ])

    def _save_goal(self, goal_text: str, goal_info: Dict):
        """保存用户目标"""
        import json
        self.db.conn.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_text TEXT,
                goal_info TEXT,
                created_at TEXT,
                current_day INTEGER DEFAULT 1,
                status TEXT DEFAULT 'active'
            )
        """)
        self.db.conn.execute(
            "INSERT INTO goals (goal_text, goal_info, created_at) VALUES (?, ?, ?)",
            (goal_text, json.dumps(goal_info, ensure_ascii=False), datetime.now().isoformat())
        )
        self.db.conn.commit()

    def _handle_image(self, image_data: str, user_input: str) -> str:
        """处理用户发送的图片"""
        import base64
        
        prompt = f"""用户发送了一张图片，并说："{user_input}"

请仔细看这张图片，然后给出有帮助的回复。如果用户问问题，给出具体答案。
如果是文字截图，提取关键信息。
如果是图表，描述趋势和数据。
如果是聊天截图，分析对话关系。"""
        
        # 支持 base64 和 URL 两种格式
        if image_data.startswith('data:'):
            # data:image/png;base64,xxxxx
            image_data = image_data.split(',')[1]
        
        try:
            # 尝试 base64 图片
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}},
                        {"type": "text", "text": prompt}
                    ]}
                ],
                max_tokens=800
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # 如果不支持 vision，降级为文本描述
            return f"收到图片了！不过我目前还不支持看图片 😢 你能把图片里的内容描述一下吗？或者直接告诉我你想问什么~"

    def get_today_mission(self) -> str:
        """获取今日微任务"""
        import json
        rows = self.db.conn.execute(
            "SELECT * FROM goals WHERE status='active' ORDER BY created_at DESC LIMIT 1"
        ).fetchall()
        
        if not rows:
            return None
        
        row = rows[0]
        goal_info = json.loads(row['goal_info'])
        current_day = row['current_day']
        
        # 生成今日任务
        daily = self.growth_mentor.generate_daily_mission(goal_info, current_day)
        progress = self.growth_mentor.check_progress(current_day, goal_info)
        
        return {
            'day': current_day,
            'goal': goal_info.get('long_goal', ''),
            'mission': daily,
            'progress': progress
        }

    def advance_day(self) -> str:
        """推进一天"""
        import json
        rows = self.db.conn.execute(
            "SELECT * FROM goals WHERE status='active' ORDER BY created_at DESC LIMIT 1"
        ).fetchall()
        
        if not rows:
            return "暂无进行中的目标"
        
        row = rows[0]
        goal_info = json.loads(row['goal_info'])
        current_day = row['current_day'] + 1
        
        self.db.conn.execute(
            "UPDATE goals SET current_day = ? WHERE id = ?",
            (current_day, row['id'])
        )
        self.db.conn.commit()
        
        daily = self.growth_mentor.generate_daily_mission(goal_info, current_day)
        progress = self.growth_mentor.check_progress(current_day, goal_info)
        
        return progress + "\n\n" + daily

    def query_past(self, query: str) -> str:
        """查询过去的事情：'我三个月前在纠结什么'"""
        if not self.graph:
            return "图数据库未连接"

        import re
        # 解析 "N个月前"
        match = re.search(r'(\d+)\s*个?月', query)
        if match:
            months = int(match.group(1))
            return self.graph.query_past_feeling(self.user_id, query, months)

        # 解析 "N周前"
        match = re.search(r'(\d+)\s*周', query)
        if match:
            weeks = int(match.group(1))
            return self.graph.query_past_feeling(self.user_id, query, weeks // 4 or 1)

        # 解析 "最近N天"
        match = re.search(r'最近\s*(\d+)\s*天', query)
        if match:
            days = int(match.group(1))
            events = self.graph.get_events_by_period(self.user_id, days=days)
            if not events:
                return f"最近{days}天没有记录到重要事件"
            lines = [f"📅 最近{days}天的重要时刻：\n"]
            for e in events:
                lines.append(f"• {e['time'][:10]} {e['summary']}")
            return "\n".join(lines)

        return "我理解你想查询过去的事情，能具体说说想看多久以前的吗？"

    def get_topic_trend(self, topic: str) -> str:
        """获取话题趋势"""
        if not self.graph:
            return "图数据库未连接"

        trends = self.graph.get_topic_trend(self.user_id, topic)
        if not trends:
            return f"还没有关于「{topic}」的记录"

        lines = [f"📈 关于「{topic}」的变化轨迹：\n"]
        for t in trends:
            date = t['time'][:10]
            emotion = t.get('emotion', '')
            lines.append(f"• {date} [{emotion}] {t['summary']}")
        return "\n".join(lines)

    def proactive_check(self) -> str:
        """检查是否需要主动关心"""
        msg = self.proactive.check_and_get_message()
        if msg:
            return self.chat(msg, skip_witness=True)
        return None

    def witness_check(self) -> list:
        """检查见证者主动提醒"""
        return self.witness.check_and_get_witness_messages()

    def close(self):
        self.db.close()
        self.proactive.stop()
