"""
AI知识助手 - 快速、带人味地解释AI概念
"""
import os
import random
from typing import Dict, List, Optional
from dotenv import load_dotenv
import openai

load_dotenv()


class AIKnowledgeGuide:
    """AI知识引导 - 快速掌握AI概念"""

    # 知识库：常见AI概念的快速解释
    KNOWLEDGE_BASE = {
        'ai引擎': {
            'simple': 'AI引擎就像是AI的"大脑"，负责思考和生成回答。不同的引擎有不同的特点：',
            'levels': [
                '🧠 GPT-4：最聪明，知识最丰富，但贵且慢',
                '💡 GPT-3.5：够用，便宜快速，适合日常',
                '🇨🇳 DeepSeek：国产，便宜，中文好',
                '🇨🇳 文心一言：百度出品，中文场景强',
            ],
            'analogy': '就像不同的发动机，动力、耗油、适用场景不同'
        },
        '提示词': {
            'simple': '提示词就是你和AI说话的"方式"。说得好，AI就答得好：',
            'rules': [
                '📌 具体 > 模糊："写一封求职邮件" > "帮我写信"',
                '📌 角色 > 空泛："你是一位资深HR" > "你很专业"',
                '📌 格式 > 无要求："用表格呈现" > "列出来"',
            ],
            'analogy': '就像点外卖，说清楚你要什么，店家才能给对'
        },
        '大模型': {
            'simple': '大模型就是"读了很多书的AI"，见过海量文本，所以懂得多：',
            'points': [
                '📚 读了多少：参数越多，通常懂得越多',
                '🎯 专长不同：有的擅长写作，有的擅长代码',
                '💰 成本差异：能力强的通常更贵',
            ],
            'analogy': '就像一个读过万卷书的人，什么话题都能聊两句'
        },
        'rag': {
            'simple': 'RAG就是让AI"查资料后再回答"，减少瞎编：',
            'steps': [
                '1️⃣ 把你的资料切碎存起来',
                '2️⃣ 用户问问题时，先找相关资料',
                '3️⃣ 把资料和问题一起给AI',
                '4️⃣ AI基于真实资料回答',
            ],
            'analogy': '就像考试时让你先翻书，再答题'
        },
        'agent': {
            'simple': 'Agent就是AI能"自己动手做事"，不只是回答问题：',
            'abilities': [
                '🔍 自动搜索信息',
                '📝 自动执行任务',
                '🔄 根据结果调整行动',
                '📋 多步骤协作',
            ],
            'analogy': '就像一个能自己干活的助理，不只是回答问题'
        },
        'token': {
            'simple': 'Token是AI计算字词的方式，大约1个中文=2个token：',
            'tips': [
                '💡 一次对话大约消耗几百到几千token',
                '💡 DeepSeek便宜，GPT贵',
                '💡 想省钱就说清楚你要什么，少废话',
            ],
            'analogy': '就像按字数收费的小说，写得短就便宜'
        },
        'fine_tuning': {
            'simple': 'Fine-tuning就是"专门训练"一个AI，让它更懂某个领域：',
            'when': [
                '✅ 需要特定风格（如客服话术）',
                '✅ 需要专有知识（如公司产品）',
                '❌ 通用问题不需要',
            ],
            'cost': '训练一次要几千到几万，谨慎使用'
        },
    }

    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )

    def is_ai_concept_question(self, text: str) -> bool:
        """判断是否是AI概念问题"""
        ai_keywords = [
            '是什么', '什么是', '什么意思', '哪个是',
            '为什么', '怎么理解', '如何理解',
            '原理', '机制', '架构', '流程', '核心优势', '特点'
        ]
        ai_terms = [
            'ai', '人工智能', '大模型', '模型', '引擎', 'agent', 'agent',
            'rag', 'fine-tune', 'fine-tuning', 'token', 'tokens',
            '提示词', 'prompt', 'prompting', '机器学习', '深度学习',
            '神经网络', 'nlp', 'gpt', 'llm', 'openai', 'deepseek',
            'embedding', '向量', '知识库', 'copilot', 'claude',
            'openclaw', '工作流', 'workflow', 'langchain', 'langchain',
            '微调', '训练', '智能体', 'embedding', '幻觉'
        ]
        
        has_ai_term = any(term in text.lower() for term in ai_terms)
        has_ai_question = any(kw in text for kw in ai_keywords)
        
        # 避免过度触发（当用户明确在说学AI应用时）
        if '行业' in text and 'AI' in text:
            return False
        
        return has_ai_term and has_ai_question

    def get_quick_explanation(self, concept: str) -> Optional[Dict]:
        """快速获取概念解释"""
        concept_lower = concept.lower()
        
        for key, value in self.KNOWLEDGE_BASE.items():
            if key in concept_lower or concept_lower in key:
                return {
                    'simple': value['simple'],
                    'content': value.get('levels') or value.get('rules') or value.get('points') or value.get('steps') or value.get('abilities') or value.get('tips') or value.get('when'),
                    'analogy': value.get('analogy', ''),
                    'type': list(value.keys())[1]
                }
        
        return None

    def generate_explanation(self, question: str) -> str:
        """生成解释"""
        # 先检查知识库
        explanation = self.get_quick_explanation(question)
        
        if explanation:
            return self.format_knowledge_response(explanation, question)
        
        # 用LLM生成
        return self.generate_with_llm(question)

    def format_knowledge_response(self, exp: Dict, question: str) -> str:
        """格式化知识回复"""
        response = f"{exp['simple']}\n\n"
        
        content = exp.get('content', [])
        if content:
            if exp.get('type') == 'levels':
                response += '\n'.join(content) + '\n\n'
            elif exp.get('type') == 'rules':
                for rule in content:
                    response += rule + '\n'
                response += '\n'
            elif exp.get('type') == 'points':
                for point in content:
                    response += point + '\n'
                response += '\n'
            elif exp.get('type') == 'steps':
                for step in content:
                    response += step + '\n'
                response += '\n'
            elif exp.get('type') == 'abilities':
                for ability in content:
                    response += ability + '\n'
                response += '\n'
            elif exp.get('type') == 'tips':
                for tip in content:
                    response += tip + '\n'
                response += '\n'
        
        if exp.get('analogy'):
            response += f"💭 打个比方：{exp['analogy']}\n"
        
        # 添加使用建议
        response += self.get_usage_tip(question)
        
        return response

    def get_usage_tip(self, question: str) -> str:
        """获取使用建议"""
        tips = [
            "\n\n---\n💡 想知道更多？问我就行~",
            "\n\n---\n有具体想用的场景吗？可以告诉我",
            "\n\n---\n想深入了解某个点？继续问~",
        ]
        return random.choice(tips)

    def generate_with_llm(self, question: str) -> str:
        """用LLM生成解释"""
        prompt = f"""你是小陆，一个用大白话解释AI概念的伙伴。

用户问：{question}

请用最简单的方式解释：
1. 一句话说明白
2. 打个比方（用生活例子）
3. 一个具体例子
4. 实际应用场景

要求：
- 像朋友聊天，不像教科书
- 不超过200字
- 让人觉得"原来如此" """

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400
            )
            result = response.choices[0].message.content.strip()
            
            # 添加使用建议
            result += self.get_usage_tip(question)
            
            return result
        except:
            return "这个问题我也想多了解一些，我们可以一起查~"


class IndustryAIContext:
    """行业AI应用上下文"""

    INDUSTRY_AI_TIPS = {
        '非技术': [
            'AI不是要取代你，是帮你省时间',
            '学会"指挥"AI，比学会"使用"AI更重要',
            '先把重复的事交给AI',
            'AI辅助决策，不是AI做决定',
        ],
        '技术': [
            'GitHub Copilot是程序员的AI助手',
            'AI写的代码要review，不能直接用',
            '会用prompt比会训练模型更实用',
            'AI是效率工具，不是炫技工具',
        ]
    }

    @classmethod
    def get_tip_for_user(self, text: str) -> Optional[str]:
        """根据用户背景给提示"""
        is_tech = any(t in text for t in ['程序员', '开发', '工程师', '代码'])
        tips = self.INDUSTRY_AI_TIPS['技术'] if is_tech else self.INDUSTRY_AI_TIPS['非技术']
        return random.choice(tips)
