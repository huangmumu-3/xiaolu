"""
记忆提取器 - 从对话中提取重要事件 (DeepSeek版本)
"""
import os
import openai
import json
from dotenv import load_dotenv

load_dotenv()


class MemoryExtractor:
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )

    def extract_memory(self, user_input: str, ai_response: str) -> dict:
        """从对话中提取关键记忆"""
        prompt = f"""分析这段对话，提取关键信息。注意：只要用户提到了决定、计划、情绪变化、重要事件，就应该标记为重要。

用户：{user_input}
AI：{ai_response}

判断这段对话是否包含值得记住的信息：
- 用户做了某个决定或计划（辞职、转行、搬城市、开始某事）
- 用户表达了强烈情绪（开心、焦虑、迷茫、兴奋、难过）
- 用户提到了重要事件（工作变动、感情变化、学习新东西）
- 用户的人生状态有变化

以JSON格式返回：
{{"is_important": true或false, "summary": "一句话总结（20字以内）", "emotion": "情绪词（如焦虑/开心/迷茫/平静/兴奋）", "importance": 1到10的数字}}
如果is_important为false，返回：{{"is_important": false}}"""

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )

        try:
            text = response.choices[0].message.content.strip()
            # 清理 markdown 包裹
            if text.startswith('\`\`\`'):
                text = text.split('\n', 1)[1] if '\n' in text else text
                text = text.rsplit('\`\`\`', 1)[0] if '\`\`\`' in text else text
            result = json.loads(text)
            if result.get('is_important'):
                result.setdefault('summary', user_input[:30])
                result.setdefault('emotion', '')
                result.setdefault('importance', 5)
            return result
        except:
            return {"is_important": False}
