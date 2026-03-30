"""
小陆自我迭代系统 - 内容生产 + 反馈收集 + 自动优化
"""
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv
import openai

load_dotenv()


class ContentGenerator:
    """内容生成器 - 基于小陆能力生成推广内容"""

    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
        self.platforms = ['xiaohongshu', 'zhihu', 'wechat', 'douyin']

    def generate_xiaohongshu_post(self, topic: str = None, style: str = "personal") -> Dict:
        """生成小红书帖子"""
        topics = topic or self._get_next_topic()
        
        prompt = f"""你是一个有百万粉丝的小红书博主，擅长写能引发共鸣的笔记。

主题：{topics}

请生成一篇小红书帖子，要求：
1. 标题要吸引人，带emoji，有数字更佳
2. 开头要有钩子，引发好奇心
3. 正文分段清晰，每段2-3句话
4. 结尾有互动引导（问问题、征集评论）
5. 添加5-10个相关标签

主题方向：
- 小陆是什么，能做什么
- AI陪伴的实际体验
- 如何用AI提升效率
- 人际交往/嘴替功能的使用场景
- 自我成长的AI助手

风格：{'真实分享' if style == 'personal' else '产品推荐'}

输出格式（严格JSON）：
{{
    "title": "标题",
    "content": "正文内容（用换行分隔段落）",
    "tags": ["标签1", "标签2", ...],
    "cover_suggestion": "封面图建议"
}}"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500
            )
            result = response.choices[0].message.content.strip()
            # 清理 markdown 包裹
            if result.startswith('```'):
                lines = result.split('\n')
                result = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "JSON解析失败", "title": "默认标题", "content": "内容生成失败", "tags": ["AI"]}
        except Exception as e:
            return {"error": str(e)}

    def generate_zhihu_answer(self, question: str) -> Dict:
        """生成知乎回答"""
        prompt = f"""回答知乎问题，要求专业、有深度、能建立权威感。

问题：{question}

请生成知乎回答：
1. 开篇直接回答问题，建立权威
2. 有逻辑清晰地论证
3. 适当引用数据或案例
4. 结尾有总结和互动引导

输出格式（严格JSON）：
{{
    "title": "回答标题",
    "content": "正文内容",
    "key_points": ["要点1", "要点2", ...]
}}"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000
            )
            return json.loads(response.choices[0].message.content.strip())
        except Exception as e:
            return {"error": str(e)}

    def _get_next_topic(self) -> str:
        """获取下一个内容主题"""
        topics = [
            "AI时代，你需要一个能记住你的伴侣",
            "我开发了一个会'见证'我成长的AI",
            "内向者必备：这个AI教你说话",
            "用AI学习AI，效率提升10倍",
            "如何让AI真正帮到你？",
            "三个月用AI陪伴，我变了多少",
            "职场沟通难？这个AI来教你",
            "AI不只是工具，更是成长伙伴",
        ]
        import random
        return random.choice(topics)

    def batch_generate_week_content(self) -> List[Dict]:
        """批量生成一周内容"""
        week_plan = [
            ("周一", "职场成长", "如何用AI提升职场竞争力"),
            ("周二", "人际交往", "AI嘴替：不知道怎么说话？"),
            ("周三", "AI技巧", "用AI学习AI的正确姿势"),
            ("周四", "产品体验", "我的AI陪伴日记"),
            ("周五", "自我反思", "AI帮我见证成长"),
            ("周六", "轻松话题", "和AI聊天是什么体验"),
            ("周日", "下周预告", "下周AI帮我做什么"),
        ]
        
        content = []
        for day, topic, hook in week_plan:
            post = self.generate_xiaohongshu_post(hook)
            content.append({
                "day": day,
                "topic": topic,
                "hook": hook,
                "post": post
            })
        
        return content


class FeedbackAnalyzer:
    """反馈分析器 - 分析意见箱反馈，优化小陆"""

    def __init__(self, db_path: str = "./data/feedback.db"):
        self.db_path = db_path
        self.client = openai.OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )

    def analyze_feedback(self) -> Dict:
        """分析所有反馈，生成优化建议"""
        try:
            from core.database import CompanionDB
            db = CompanionDB(self.db_path)
            
            rows = db.conn.execute("""
                SELECT * FROM feedback 
                ORDER BY created_at DESC LIMIT 50
            """).fetchall()
            
            if not rows:
                return {"status": "no_feedback", "message": "暂无反馈", "summary": "暂无反馈数据"}
            
            # 按类型分组
            by_type = {}
            for row in rows:
                t = row['type']
                if t not in by_type:
                    by_type[t] = []
                by_type[t].append(row['content'])
            
            # 生成分析报告
            analysis = self._generate_analysis(by_type)
            return analysis
            
        except Exception as e:
            return {"error": str(e), "summary": "分析失败"}

    def _generate_analysis(self, by_type: Dict) -> Dict:
        """LLM分析反馈"""
        prompt = f"""分析以下用户反馈，生成优化建议。

反馈分类：
{json.dumps(by_type, ensure_ascii=False, indent=2)}

请分析：
1. 用户最关心什么功能
2. 最常见的问题是什么
3. 最有价值的建议是什么
4. 下一步应该优先做什么

以JSON格式返回（严格JSON，不要markdown包裹）：
{{
    "summary": "总体概述",
    "top_requests": ["需求1", "需求2"],
    "common_issues": ["问题1", "问题2"],
    "priority_actions": ["优先级1", "优先级2"],
    "content_angles": ["内容角度1", "内容角度2"]
}}"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            result = response.choices[0].message.content.strip()
            # 清理可能的markdown包裹
            if result.startswith('```'):
                result = result.split('\n', 1)[1] if '\n' in result else result
                result = result.rsplit('```', 1)[0] if '```' in result else result
            return json.loads(result)
        except json.JSONDecodeError as e:
            return {"error": f"JSON解析失败: {e}", "summary": "分析结果解析失败"}
        except Exception as e:
            return {"error": str(e), "summary": "分析失败"}


class SelfIterator:
    """自我迭代器 - 让小陆定期自检和优化"""

    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
        self.content_gen = ContentGenerator()
        self.feedback_analyzer = FeedbackAnalyzer()

    def weekly_review(self) -> Dict:
        """每周自我回顾"""
        # 1. 分析反馈
        feedback_analysis = self.feedback_analyzer.analyze_feedback()
        
        # 2. 生成本周内容数据
        content = self.content_gen.batch_generate_week_content()
        
        # 3. 生成迭代建议
        review = self._generate_review(feedback_analysis, content)
        
        return {
            "date": datetime.now().isoformat(),
            "feedback_analysis": feedback_analysis,
            "content_generated": len(content),
            "review": review
        }

    def _generate_review(self, feedback: Dict, content: List) -> Dict:
        """生成迭代回顾"""
        feedback_summary = '暂无详细数据'
        priorities = []
        
        if isinstance(feedback, dict):
            if 'summary' in feedback:
                feedback_summary = feedback.get('summary', '暂无数据')
            if 'priority_actions' in feedback:
                priorities = feedback.get('priority_actions', [])[:3]
        
        prompt = f"""你是小陆，一个AI伴侣。现在是你每周的自我迭代时间。

本周反馈概述：
{feedback_summary}

本周生成了 {len(content)} 篇内容。

优先改进项：
{chr(10).join(['- ' + p for p in priorities]) if priorities else '- 暂无明确改进项'}

请生成迭代报告，包含：
1. 本周做得好的地方
2. 需要改进的地方
3. 下周具体行动计划（3条）
4. 想对用户说的话

以JSON格式返回（严格JSON）：
{{
    "good": ["优点1", "优点2"],
    "improve": ["改进1", "改进2"],
    "next_week_actions": ["行动1", "行动2", "行动3"],
    "message_to_users": "对用户说的话"
}}"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800
            )
            result = response.choices[0].message.content.strip()
            # 清理markdown包裹
            if result.startswith('```'):
                result = result.split('\n', 1)[1] if '\n' in result else result
                result = result.rsplit('```', 1)[0] if '```' in result else result
            return json.loads(result)
        except json.JSONDecodeError:
            return {"good": ["持续优化中"], "improve": ["收集更多反馈"], "next_week_actions": ["继续完善功能"], "message_to_users": "感谢大家的支持！"}
        except Exception as e:
            return {"good": [], "improve": [], "next_week_actions": [], "message_to_users": f"迭代中: {e}"}

    def generate_improvement_plan(self) -> str:
        """生成改进计划"""
        feedback = self.feedback_analyzer.analyze_feedback()
        
        if isinstance(feedback, dict) and 'error' in feedback:
            return "暂无足够数据生成改进计划"
        
        priorities = feedback.get('priority_actions', [])
        if not priorities:
            return "目前反馈较少，暂时没有明确的改进优先级。"
        
        prompt = f"""基于以下用户反馈，制定具体的改进计划。

反馈分析：
{json.dumps(feedback, ensure_ascii=False, indent=2)}

请为每个优先级改进项，制定：
1. 改进方案（具体怎么做）
2. 预期效果（用户会感受到什么）
3. 验证方法（怎么知道改好了）

以Markdown格式输出。"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"生成改进计划失败: {e}"
