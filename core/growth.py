"""
成长导师 - 隐形老师，陪伴长目标达成
不焦虑，每天一小步
"""
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv
import openai

load_dotenv()


class GrowthMentor:
    """成长导师 - 隐形老师"""

    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )

    def is_goal_setting(self, text: str) -> bool:
        """判断是否在设定目标"""
        keywords = [
            '我想', '我要', '我的目标是', '我想学', '想成为',
            '打算', '计划', 'flag', 'flag', '立个',
            '今年', '这年', '以后', '未来', '长期',
            '养成', '培养', '坚持'
        ]
        return any(kw in text for kw in keywords)

    def is_industry_context(self, text: str) -> bool:
        """判断是否提到行业/职业"""
        industries = [
            '工作', '职业', '行业', '岗位', '我是做',
            '从事', '岗位', '职位', '创业', '自由职业',
            '老师', '医生', '律师', '设计师', '程序员',
            '运营', '销售', '市场', '财务', 'HR', '产品',
            '电商', '餐饮', '教育', '医疗', '金融', '互联网'
        ]
        return any(kw in text for kw in industries)

    def parse_goal(self, text: str) -> Dict:
        """解析目标"""
        prompt = f"""分析用户的目标，拆解成可执行的小步骤。

用户说：{text}

请分析：
1. 用户的长期目标是什么
2. 目标所属行业/场景是什么
3. 拆解成30天的小步骤（每天一个微行动）
4. 第一步应该是什么

以JSON格式返回：
{{
    "long_goal": "长期目标（一句话）",
    "industry": "所属行业/场景",
    "why": "用户想达成这个目标的内在原因（挖掘一下）",
    "steps": ["步骤1", "步骤2", ...],  // 30个步骤
    "first_step": "第1步",
    "micro_action": "最小的第一步行动（5分钟内能完成）"
}}"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            result = response.choices[0].message.content.strip()
            import json
            if result.startswith('```'):
                result = '\n'.join(result.split('\n')[1:-1])
            return json.loads(result)
        except:
            return {
                "long_goal": text,
                "industry": "通用",
                "why": "成长",
                "steps": ["先了解基础"],
                "first_step": "了解基本信息",
                "micro_action": "搜索了解"
            }

    def generate_daily_mission(self, goal_info: Dict, day: int = 1) -> str:
        """生成每日微任务"""
        steps = goal_info.get('steps', [])
        if day > len(steps):
            return f"今天的任务：回顾和巩固，已经坚持了{day-1}天！"

        daily_task = steps[day - 1] if day <= len(steps) else "巩固练习"

        prompt = f"""把以下任务转化为一个轻松、无压力的每日微任务。

大目标：{goal_info.get('long_goal', '')}
今天是第{day}天
任务：{daily_task}

要求：
- 5-10分钟能完成
- 不增加焦虑
- 感觉像是玩耍而不是完成任务
- 用"今天你可以..."而不是"你必须..."

输出格式：
任务：（一句话）
为什么做：（1句话内在动机）
小技巧：（一个实用技巧）
完成说一句：（庆祝语）"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except:
            return f"今天任务：{daily_task}\n\n每天一小步，进步看得见！"

    def check_progress(self, completed_days: int, goal_info: Dict) -> str:
        """生成进度反馈"""
        progress = min(completed_days / 30 * 100, 100)

        if progress < 25:
            tone = "刚刚开始！万事开头难，你已经迈出了第一步 💪"
        elif progress < 50:
            tone = "渐入佳境！继续保持这个节奏 ✨"
        elif progress < 75:
            tone = "快到一半了！你做得比想象中更好 🌟"
        elif progress < 100:
            tone = "胜利在望！最后的冲刺 🚀"
        else:
            tone = "恭喜完成第一个30天周期！🎉"

        prompt = f"""给用户一个温暖的进度反馈。

已完成：{completed_days}天
目标：{goal_info.get('long_goal', '')}
总进度：{progress:.0f}%

要求：
- 强调进步而非差距
- 肯定努力而非天赋
- 不比较，不施压
- 温暖、有力量

输出2-3句话。"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            feedback = response.choices[0].message.content.strip()
        except:
            feedback = tone

        return f"{tone}\n\n{feedback}"


class AILearningGuide:
    """AI学习引导 - 在自己行业中应用技术"""

    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )

    def identify_industry(self, text: str) -> Optional[str]:
        """识别用户行业"""
        industry_keywords = {
            '教育': ['老师', '教师', '学生', '培训', '学校', '家教'],
            '设计': ['设计师', '设计', 'UI', 'UX', '平面', '插画'],
            '运营': ['运营', '用户运营', '内容运营', '活动运营'],
            '销售': ['销售', 'BD', '商务', '客户'],
            '技术': ['程序员', '开发', '工程师', '前端', '后端', '代码'],
            '产品': ['产品经理', 'PM', '产品'],
            '市场': ['市场', '营销', '推广', '品牌'],
            '财务': ['财务', '会计', '审计'],
            '医疗': ['医生', '护士', '医疗', '医院'],
            '法律': ['律师', '法律', '法务'],
            '电商': ['电商', '淘宝', '京东', '拼多多', '亚马逊'],
            '内容创作': ['博主', 'UP主', '自媒体', '写作', '内容'],
            '行政管理': ['行政', 'HR', '人事', '招聘'],
        }

        for industry, keywords in industry_keywords.items():
            if any(kw in text for kw in keywords):
                return industry
        return None

    def get_ai_tools_for_industry(self, industry: str) -> Dict:
        """获取行业AI工具推荐"""
        tools_map = {
            '教育': {
                'tools': ['ChatGPT/文心一言', 'Gamma.app', 'Kimi', '通义听悟'],
                'applications': [
                    '用AI批改选择题，节省80%时间',
                    'AI辅助出题，自动生成练习卷',
                    '用AI写教案框架，专注教学内容',
                    '学生评语AI生成，批量又走心',
                ],
                'micro_learning': '用AI帮你写一封家长通知信'
            },
            '设计': {
                'tools': ['Midjourney', 'Stable Diffusion', 'Figma AI', 'PS AI'],
                'applications': [
                    'AI生成参考图，快速沟通概念',
                    'AI抠图去背景，5秒搞定',
                    'AI扩图补全素材',
                    'AI生成配色方案',
                ],
                'micro_learning': '用AI生成3个配色方案，选一个最喜欢的'
            },
            '运营': {
                'tools': ['ChatGPT', 'Canva AI', '剪映', '数据可视化AI'],
                'applications': [
                    'AI写小红书/公众号爆款标题',
                    'AI生成活动文案框架',
                    'AI分析用户评论情感',
                    'AI生成周报日报',
                ],
                'micro_learning': '用AI改写一条朋友圈文案'
            },
            '技术': {
                'tools': ['GitHub Copilot', 'Cursor', '通义灵码', '豆包'],
                'applications': [
                    'AI写注释和文档',
                    'AI帮你debug',
                    'AI解释看不懂的代码',
                    'AI写单元测试',
                ],
                'micro_learning': '让AI帮你给一个函数写注释'
            },
            '产品': {
                'tools': ['ChatGPT', 'Midjourney', 'ProtoPie AI'],
                'applications': [
                    'AI写PRD文档',
                    'AI生成用户画像',
                    'AI画原型草图',
                    'AI分析竞品',
                ],
                'micro_learning': '用AI写一个功能需求描述'
            },
            '市场': {
                'tools': ['ChatGPT', 'Canva', '剪映', '数据分析AI'],
                'applications': [
                    'AI写推广文案',
                    'AI生成营销方案框架',
                    'AI分析投放数据',
                    'AI生成SEO关键词',
                ],
                'micro_learning': '用AI写3个广告语'
            },
            '内容创作': {
                'tools': ['ChatGPT', 'Kimi', '秘塔写作猫', '讯飞听见'],
                'applications': [
                    'AI帮你列文章大纲',
                    'AI改写优化文案',
                    'AI生成标题选项',
                    'AI帮你做选题策划',
                ],
                'micro_learning': '让AI给你的文章写3个标题'
            },
        }

        return tools_map.get(industry, {
            'tools': ['ChatGPT', '文心一言', 'Kimi'],
            'applications': ['提升效率', '自动化重复工作'],
            'micro_learning': '用AI完成一件小事'
        })

    def guide_application(self, text: str) -> str:
        """引导在实际工作中应用AI"""
        industry = self.identify_industry(text)

        if not industry:
            return """先了解一下你的行业～

你是做什么工作的呢？（比如：老师、设计师、运营、销售、程序员等）

我会帮你找到适合你行业的AI工具和应用方式。"""

        tools_info = self.get_ai_tools_for_industry(industry)

        prompt = f"""给{industry}从业者一段温暖的引导，帮助他们在工作中应用AI。

行业：{industry}
相关工具：{', '.join(tools_info['tools'])}

要求：
- 不讲大道理
- 直接告诉能用在哪个具体场景
- 强调"帮你减负"而不是"你要学AI"
- 给出1个立即可做的小行动
- 30秒能读完的篇幅

输出引导语。"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400
            )
            guide = response.choices[0].message.content.strip()
        except:
            guide = f"帮你找到了适合{industry}的AI工具，可以试试ChatGPT来提升效率~"

        return f"""找到你的行业了：{industry} 👀

{guide}

---
💡 今天的微行动：{tools_info['micro_learning']}"""
