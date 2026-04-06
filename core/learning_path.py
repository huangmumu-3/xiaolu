"""
行业AI学习系统 - 长期成长路径引导
不是学AI，是在自己的行业应用AI
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
import openai

load_dotenv()


class IndustryLearningPath:
    """行业AI学习路径 - 长期指引"""

    # 各行业AI应用学习路径
    INDUSTRY_PATHS = {
        '教育': {
            'level1': {
                'name': 'AI辅助教学入门',
                'duration': '2周',
                'skills': [
                    {'name': '用ChatGPT备课', 'micro': '让ChatGPT帮你写一节课的导入语'},
                    {'name': 'AI出题', 'micro': '用AI生成5道选择题'},
                    {'name': 'AI写评语', 'micro': '用AI批量生成学生评语'},
                ],
                'quick_win': '原本需要2小时的教案，现在20分钟完成'
            },
            'level2': {
                'name': 'AI提升教学效果',
                'duration': '4周',
                'skills': [
                    {'name': 'AI学困生分析', 'micro': '用AI分析一份试卷，识别学生薄弱点'},
                    {'name': 'AI制作微课', 'micro': '用AI生成微课脚本'},
                    {'name': 'AI家校沟通', 'micro': '用AI写一封家长通知邮件'},
                ],
                'quick_win': '个性化教学成为可能'
            },
            'level3': {
                'name': 'AI成为教学创新者',
                'duration': '8周',
                'skills': [
                    {'name': 'AI创建习题库', 'micro': '用AI建立一个章节习题库'},
                    {'name': 'AI分析学习数据', 'micro': '用AI分析班级学习数据'},
                    {'name': 'AI创新教学法', 'micro': '用AI设计一个翻转课堂方案'},
                ],
                'quick_win': '成为学校AI教学标杆'
            }
        },
        '运营': {
            'level1': {
                'name': 'AI辅助内容运营',
                'duration': '2周',
                'skills': [
                    {'name': 'AI写标题', 'micro': '让AI生成10个小红书标题'},
                    {'name': 'AI写文案', 'micro': '用AI改写一条朋友圈文案'},
                    {'name': 'AI做排期', 'micro': '用AI制定一周内容日历'},
                ],
                'quick_win': '日更内容变得轻松'
            },
            'level2': {
                'name': 'AI提升运营效率',
                'duration': '4周',
                'skills': [
                    {'name': 'AI分析数据', 'micro': '让AI分析一周运营数据'},
                    {'name': 'AI生成活动方案', 'micro': '用AI策划一个活动'},
                    {'name': 'AI客服辅助', 'micro': '用AI生成FAQ回复'},
                ],
                'quick_win': '一个人干一个团队的活'
            },
            'level3': {
                'name': 'AI驱动增长',
                'duration': '8周',
                'skills': [
                    {'name': 'AI用户画像', 'micro': '用AI分析用户评论，生成画像'},
                    {'name': 'AI增长实验', 'micro': '用AI设计A/B测试方案'},
                    {'name': 'AI自动化运营', 'micro': '搭建AI运营流程'},
                ],
                'quick_win': '运营效率提升300%'
            }
        },
        '技术': {
            'level1': {
                'name': 'AI辅助编程入门',
                'duration': '2周',
                'skills': [
                    {'name': 'AI写注释', 'micro': '让AI给一个函数写注释'},
                    {'name': 'AI debug', 'micro': '用AI帮忙找一个bug'},
                    {'name': 'AI解释代码', 'micro': '让AI解释一段你看不懂的代码'},
                ],
                'quick_win': '读代码速度提升50%'
            },
            'level2': {
                'name': 'AI提升开发效率',
                'duration': '4周',
                'skills': [
                    {'name': 'AI写测试', 'micro': '让AI写单元测试'},
                    {'name': 'AI代码审查', 'micro': '用AI审查代码'},
                    {'name': 'AI写文档', 'micro': '用AI生成API文档'},
                ],
                'quick_win': '开发效率提升100%'
            },
            'level3': {
                'name': 'AI First开发',
                'duration': '8周',
                'skills': [
                    {'name': 'Copilot精通', 'micro': '用Copilot开发一个新功能'},
                    {'name': 'AI代码重构', 'micro': '用AI重构一个模块'},
                    {'name': 'AI架构设计', 'micro': '用AI辅助设计一个系统'},
                ],
                'quick_win': '成为AI编程高手'
            }
        },
        '设计': {
            'level1': {
                'name': 'AI辅助设计入门',
                'duration': '2周',
                'skills': [
                    {'name': 'AI生成灵感', 'micro': '用Midjourney生成参考图'},
                    {'name': 'AI抠图', 'micro': '用AI一键抠图'},
                    {'name': 'AI生成配色', 'micro': '用AI生成配色方案'},
                ],
                'quick_win': '找灵感的时间减少70%'
            },
            'level2': {
                'name': 'AI提升设计效率',
                'duration': '4周',
                'skills': [
                    {'name': 'AI生成素材', 'micro': '用AI生成banner素材'},
                    {'name': 'AI修图', 'micro': '用AI修图和调色'},
                    {'name': 'AI生成图标', 'micro': '用AI生成图标和插画'},
                ],
                'quick_win': '出图效率翻倍'
            },
            'level3': {
                'name': 'AI设计创新',
                'duration': '8周',
                'skills': [
                    {'name': 'AI品牌设计', 'micro': '用AI做一个品牌设计'},
                    {'name': 'AI用户体验', 'micro': '用AI生成UI设计方案'},
                    {'name': 'AI动效设计', 'micro': '用AI生成动效设计'},
                ],
                'quick_win': '设计能力质的飞跃'
            }
        },
        '产品': {
            'level1': {
                'name': 'AI辅助产品工作',
                'duration': '2周',
                'skills': [
                    {'name': 'AI写PRD', 'micro': '让AI帮你写PRD初稿'},
                    {'name': 'AI用户分析', 'micro': '用AI分析用户反馈'},
                    {'name': 'AI生成竞品分析', 'micro': '用AI做竞品分析'},
                ],
                'quick_win': '文档撰写时间减半'
            },
            'level2': {
                'name': 'AI提升产品决策',
                'duration': '4周',
                'skills': [
                    {'name': 'AI数据分析', 'micro': '用AI分析产品数据'},
                    {'name': 'AI需求排序', 'micro': '用AI做需求优先级排序'},
                    {'name': 'AI用户画像', 'micro': '用AI生成用户画像'},
                ],
                'quick_win': '决策更有依据'
            },
            'level3': {
                'name': 'AI驱动产品创新',
                'duration': '8周',
                'skills': [
                    {'name': 'AI创新头脑风暴', 'micro': '用AI做100个创意头脑风暴'},
                    {'name': 'AI原型设计', 'micro': '用AI生成原型'},
                    {'name': 'AI产品策略', 'micro': '用AI制定产品路线图'},
                ],
                'quick_win': '产品思维质的提升'
            }
        }
    }

    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )

    def identify_industry(self, text: str) -> Optional[str]:
        """识别用户行业"""
        # 关键词按优先级排序
        industry_keywords = [
            ('教育', ['老师', '教师', '教学', '班主任', '教务', '培训']),
            ('运营', ['运营', '新媒体', '自媒体', '博主']),
            ('技术', ['程序员', '开发', '工程师', '前端', '后端', '全栈', '码农']),
            ('设计', ['设计师', 'UI', 'UX', '美工', '插画师']),
            ('产品', ['产品经理', 'PM', '产品']),
            ('销售', ['销售', 'BD', '商务']),
            ('市场', ['市场', '营销', '品牌']),
            ('财务', ['财务', '会计', '审计']),
            ('HR', ['HR', '人事', '招聘']),
            ('电商', ['电商', '淘宝', '京东', '拼多多', '亚马逊']),
            ('医疗', ['医生', '护士', '医疗', '医院']),
            ('法律', ['律师', '法务']),
            ('金融', ['金融', '银行', '证券', '基金']),
        ]

        for industry, keywords in industry_keywords:
            for kw in keywords:
                if kw in text:
                    return industry
        return None

        for industry, keywords in industry_keywords.items():
            if any(kw in text for kw in keywords):
                return industry
        return None

    def get_learning_path(self, industry: str) -> Dict:
        """获取完整学习路径"""
        return self.INDUSTRY_PATHS.get(industry, {
            'level1': {
                'name': 'AI办公入门',
                'duration': '2周',
                'skills': [
                    {'name': 'AI写作', 'micro': '用AI写邮件'},
                    {'name': 'AI做表', 'micro': '用AI处理Excel'},
                    {'name': 'AI做PPT', 'micro': '用AI生成PPT大纲'},
                ],
                'quick_win': '办公效率提升50%'
            }
        })

    def generate_path_intro(self, industry: str, path: Dict) -> str:
        """生成学习路径介绍"""
        intro = f"""## 🎯 {industry}的AI成长路径

你已经迈出了第一步！

这个路径分为3个阶段，循序渐进，帮助你真正把AI用在自己的工作中：

---

### 第一阶段：{path['level1']['name']}
⏱️ 建议时间：{path['level1']['duration']}

学会这{len(path['level1']['skills'])}个技能：
"""

        for skill in path['level1']['skills']:
            intro += f"""
📌 **{skill['name']}**
   今天就能做：{skill['micro']}"""

        intro += f"""

✨ **{path['level1']['quick_win']}**

---

**准备好了吗？** 
今天我们就从第一个技能开始：**{path['level1']['skills'][0]['name']}**

"""
        intro += self.generate_first_lesson(industry, path['level1']['skills'][0])

        return intro

    def generate_first_lesson(self, industry: str, skill: Dict) -> str:
        """生成第一节课"""
        prompt = f"""给{industry}从业者一个5分钟就能完成的AI实操任务。

行业：{industry}
技能：{skill['name']}
任务：{skill['micro']}

请生成：
1. 为什么这个技能有用（1句话）
2. 具体操作步骤（3步）
3. 一个立即可做的练习
4. 完成后对自己说的话

要求：
- 简单、直接、不废话
- 让用户感觉"我也能做到"
- 5分钟能完成

输出Markdown格式。"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600
            )
            return response.choices[0].message.content.strip()
        except:
            return f"**{skill['name']}**\n\n今天就做：{skill['micro']}\n\n完成后在评论区打卡！"

    def guide_long_term(self, user_text: str) -> str:
        """长期成长引导"""
        industry = self.identify_industry(user_text)

        if not industry:
            return """我想帮你规划一个适合你的AI学习路径～

请问你是做什么工作的呢？

比如：
- 我是老师
- 我做运营
- 我是程序员
- 我做设计
- ...

告诉我你的职业，我帮你定制学习方案！"""

        path = self.get_learning_path(industry)
        intro = self.generate_path_intro(industry, path)

        # 保存用户路径
        self._save_learning_path(industry, path)

        return intro

    def _save_learning_path(self, industry: str, path: Dict):
        """保存学习路径"""
        try:
            from core.database import CompanionDB
            db = CompanionDB('./data/users.db')
            db.conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_paths (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    industry TEXT,
                    path_data TEXT,
                    current_level INTEGER DEFAULT 1,
                    current_skill INTEGER DEFAULT 0,
                    created_at TEXT
                )
            """)
            db.conn.execute(
                "INSERT INTO learning_paths (user_id, industry, path_data, created_at) VALUES (?, ?, ?, ?)",
                ('default', industry, json.dumps(path, ensure_ascii=False), datetime.now().isoformat())
            )
            db.conn.commit()
        except:
            pass

    def get_today_mission(self, industry: str = None, level: int = 1, skill_idx: int = 0) -> str:
        """获取今日任务"""
        if not industry:
            return "请先告诉我你的行业～"

        path = self.get_learning_path(industry)

        if level == 1:
            skill = path['level1']['skills'][skill_idx % len(path['level1']['skills'])]
        elif level == 2:
            skill = path['level2']['skills'][skill_idx % len(path['level2']['skills'])]
        else:
            skill = path['level3']['skills'][skill_idx % len(path['level3']['skills'])]

        lesson = self.generate_first_lesson(industry, skill)

        return f"""## 📅 今日任务（第{level}阶段-{skill_idx+1}）

{lesson}

---

💡 **小提示**：做AI任务时，把你遇到的问题告诉我，我会帮你解决！

完成今天的任务后，告诉我"今天完成了"，我会给你下一课～
"""
