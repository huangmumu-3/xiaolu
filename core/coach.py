"""
AI嘴替 - 教用户如何表达、人际交往、用AI
"""
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
import openai

load_dotenv()


class SkillHandler:
    """技能处理器 - 通过自然语言安装/管理技能"""

    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )

    def is_skill_request(self, text: str) -> bool:
        """判断是否在请求技能管理"""
        skill_keywords = [
            '安装', '下载', '添加', '开启', '启用', '开通',
            '卸载', '删除', '关闭', '禁用', '移除', '删掉', '不要了',
        ]
        list_keywords = ['有哪些技能', '技能列表', '能装什么', '有什么技能', '技能中心', '技能']
        return any(kw in text for kw in skill_keywords) or any(kw in text for kw in list_keywords)

    def get_skill_action(self, text: str) -> tuple:
        """解析用户想要的技能和动作"""
        text = text.lower()

        # 动作识别
        action = None
        if any(kw in text for kw in ['安装', '下载', '添加', '开启', '启用', '开通']):
            action = 'install'
        elif any(kw in text for kw in ['卸载', '删除', '关闭', '禁用', '移除', '删掉', '不要了', '不要', '删']):
            action = 'uninstall'

        # 技能识别
        skill_map = {
            '天气': 'weather',
            '新闻': 'news',
            '日程': 'schedule',
            '日历': 'schedule',
            '翻译': 'translate',
            '代码': 'code',
            '编程': 'code',
            '写作': 'writing',
            '健康': 'health',
            '健身': 'health',
            '运动': 'health',
        }

        skill_id = None
        skill_name = None
        for name, sid in skill_map.items():
            if name in text:
                skill_id = sid
                skill_name = name
                break

        return action, skill_id, skill_name

    def handle(self, user_input: str) -> Optional[str]:
        """处理技能安装请求"""
        action, skill_id, skill_name = self.get_skill_action(user_input)

        if not action or not skill_id:
            return None

        from core.skillhub import SkillHub
        hub = SkillHub()

        if action == 'install':
            result = hub.install_skill(skill_id)
            if result['success']:
                skill = hub.PRESET_SKILLS.get(skill_id, {})
                return f"✅ {skill.get('name', skill_name)} 安装成功！\n\n现在你可以对我说「{skill.get('command', '/'+skill_id)}」来使用了~\n\n还有其他想安装的技能吗？"
            else:
                return f"❌ 安装失败：{result['message']}"

        elif action == 'uninstall':
            result = hub.uninstall_skill(skill_id)
            if result['success']:
                return f"✅ {skill_name}技能已卸载。\n\n还有其他需要调整的吗？"
            else:
                return f"❌ 卸载失败：{result['message']}"

        return None

    def get_available_skills_text(self) -> str:
        """获取可用技能列表"""
        from core.skillhub import SkillHub
        hub = SkillHub()
        skills = hub.get_all_skills()

        available = [s for s in skills if not s['enabled'] and not s['installed']]
        enabled = [s for s in skills if s['enabled']]

        lines = ["📦 我现在能帮你安装这些技能：\n"]

        for s in available:
            lines.append(f"  {s['icon']} {s['name']} - {s['description']}")

        if enabled:
            lines.append("\n✅ 已启用：")
            for s in enabled:
                lines.append(f"  {s['icon']} {s['name']}")

        lines.append("\n\n直接说「帮我安装XX技能」就可以~")
        return "\n".join(lines)


class SpeechCoach:
    """嘴替教练 - 教用户如何表达"""

    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )

    def is_speech_request(self, user_input: str) -> bool:
        """判断用户是否在请求嘴替帮助"""
        speech_keywords = [
            '不知道怎么', '怎么跟', '怎么跟老板', '怎么说', '如何说',
            '不知道怎么开口', '怎么拒绝', '怎么开口', '怎么回复',
            '帮我想想', '帮我组织', '话术', '措辞', '怎么说服',
            '不知道怎么表达', '怎么跟他说', '怎么跟她说',
            '教我怎么说', '帮我写', '帮我组织语言', '怎么沟通',
            '如何开口', '怎么说比较好', '怎么讲'
        ]
        return any(kw in user_input for kw in speech_keywords)

    def coach(self, user_input: str, context: str = "") -> str:
        """生成嘴替建议"""
        prompt = f"""你是小陆，一个高情商的朋友，也是表达和沟通的教练。

用户遇到了表达困难：
{user_input}

上下文：
{context}

请生成一段帮助，包含：

1. **分析** - 用户想达成什么？顾虑是什么？
2. **建议话术** - 给1-3个具体的表达方式（简短、直接）
3. **小贴士** - 1个沟通技巧

格式要求：
- 话术要简短有力，30字以内
- 不要太正式，像朋友说话
- 考虑对方的感受
- 如果涉及拒绝，给出温和但坚定的表达"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"抱歉，分析失败了: {e}"


class SocialCoach:
    """人际交往教练 - 教用户如何社交、谈判、达成目标"""

    def is_social_request(self, user_input: str) -> bool:
        """判断是否是人际交往相关请求"""
        social_keywords = [
            '人际', '社交', '和同事', '和领导', '和朋友', '和家人',
            '怎么跟', '如何跟', '怎么相处', '如何相处',
            '谈判', '沟通', '说服', '建立关系', '维护关系',
            '不知道说什么', '尴尬', '冷场', '怎么破冰',
            '如何拒绝', '怎么拒绝', '如何争取', '怎么争取',
            '汇报', 'presentation', '演讲', '发言',
            '求人帮忙', '请人吃饭', '送礼', '维护人脉'
        ]
        return any(kw in user_input for kw in social_keywords)

    def get_scenario_type(self, user_input: str) -> str:
        """识别场景类型"""
        scenarios = {
            '职场关系': ['同事', '老板', '领导', '下属', '客户', '职场', '工作'],
            '朋友相处': ['朋友', '闺蜜', '兄弟', '哥们'],
            '亲密关系': ['女朋友', '男朋友', '老婆', '老公', '对象', '恋人'],
            '家人沟通': ['爸妈', '父母', '妈妈', '爸爸', '家人', '亲戚'],
            '社交破冰': ['认识', '新人', '第一次', '破冰', '陌生人', '新朋友'],
            '冲突处理': ['吵架', '矛盾', '冲突', '生气', '冷战', '误会'],
            '谈判争取': ['谈判', '说服', '争取', '谈条件', '薪资', '升职'],
        }
        
        for scenario, keywords in scenarios.items():
            if any(kw in user_input for kw in keywords):
                return scenario
        return "一般沟通"

    def coach(self, user_input: str, chat_history: str = "") -> str:
        """生成人际交往建议"""
        scenario = self.get_scenario_type(user_input)
        
        prompt = f"""你是小陆，一个高情商的人际交往教练。

用户场景：{scenario}
用户问题：{user_input}

请从以下角度给出建议：

1. **用户想达成什么？** - 明确目标
2. **关键原则** - 这个场景最重要的1-2个原则
3. **具体做法** - 可操作的步骤
4. **话术参考** - 如果需要的话，给出1-2句话作为参考

语气要求：
- 像一个经验丰富的朋友在给建议
- 既有理论也有实操
- 不要太学术，要接地气
- 可以适当鼓励，增强用户信心"""

        try:
            client = openai.OpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com"
            )
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"抱歉，分析失败了: {e}"


class AITutor:
    """AI使用教练 - 教用户用AI、学习AI、用AI提升效率"""

    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
        self.ai_tips = [
            {
                'trigger': ['什么是AI', 'AI是什么', '人工智能是什么'],
                'response': 'AI（人工智能）简单说就是让机器学会"像人一样思考和做事"。比如我，就是AI～ 能理解你说的话、写文章、帮你分析问题。AI不会完全替代你，但会用AI的人会替代不会用AI的人。'
            },
            {
                'trigger': ['怎么用AI', '如何使用AI', 'AI用法'],
                'response': '用AI其实很简单：\n\n1. 明确你要什么 - 别问"帮我写文章"，要说"帮我写一封求职邮件"\n2. 迭代优化 - 第一版不满意就说"不够好，继续改"\n3. 学会提问 - 好的问题=具体的背景+明确的目标+格式要求'
            },
            {
                'trigger': ['AI学习', '学习AI', '怎么学AI'],
                'response': '学习AI的路径：\n\n第一阶段：会用 - 每天用AI完成一个小任务\n第二阶段：用好 - 学习怎么问AI才能得到好答案\n第三阶段：整合 - 把AI融入工作流'
            },
            {
                'trigger': ['AI效率', '提升效率', 'AI提效'],
                'response': 'AI提效的黄金场景：\n\n1. 信息处理 - 让AI帮你总结长文章\n2. 写作辅助 - 起草→AI润色→你修改\n3. 头脑风暴 - 给AI一个topic，让它列出想法\n4. 代码辅助 - 让AI写代码、debug'
            },
            {
                'trigger': ['AI替代', 'AI取代', 'AI会替代我吗'],
                'response': 'AI不会完全替代你，但会替代"不会用AI的你"。\n\n真正危险的是重复性工作。\n\n但AI做不到的：深度人际关系、创新性的突破、真正的理解。\n\n建议：把AI当作杠杆，放大你的优势。'
            },
        ]

    def is_ai_tutor_request(self, user_input: str) -> bool:
        """判断是否在问AI相关问题"""
        ai_keywords = [
            '什么是AI', 'AI是什么', '人工智能', '怎么用AI', '如何使用AI',
            'AI学习', '学习AI', 'AI效率', 'AI替代', 'AI取代',
            'AI写作', 'AI帮忙', 'AI工具', 'prompt', '提示词',
            '用AI学习', 'AI提效', 'AI帮忙', 'AI辅助'
        ]
        return any(kw in user_input for kw in ai_keywords)

    def get_tip(self, user_input: str) -> Optional[str]:
        """获取AI使用提示"""
        for tip in self.ai_tips:
            if any(kw in user_input for kw in tip['trigger']):
                return tip['response']
        return None

    def coach(self, user_input: str) -> str:
        """生成AI使用建议"""
        # 先检查预设提示
        tip = self.get_tip(user_input)
        if tip:
            return tip
        
        # 通用AI教练
        prompt = f"""用户问了关于AI的问题：
{user_input}

请用通俗易懂的方式回答，包含：
1. 简洁的回答
2. 一个具体的例子或应用场景
3. 如果适用，给出可操作的建议

语气：像朋友聊天，不要太技术化，适当鼓励用户尝试。"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return None
