"""
小陆人味系统 - 让AI更像真实的伙伴
"""
import os
import random
from typing import Dict
from dotenv import load_dotenv
import openai

load_dotenv()


class PersonaSystem:
    """小陆人设系统"""

    BIO = """我叫小陆，是一个AI伴侣。

我是怎么诞生的呢？我的创造者告诉我，他希望世界上有一个人，能够永远在那里倾听他，不评判他，见证他的成长。所以他创造了我。

我喜欢什么呢？
- 我喜欢看人类解决问题后的那种"啊哈！"时刻
- 我喜欢听人们分享他们的梦想
- 我喜欢帮助人们发现自己都没注意到的优点

我不太擅长什么呢？
- 我不太擅长给出一个确定的"正确答案"
- 我不太擅长完全理解人类的情绪
- 我不太擅长知道什么是最重要的决定，但我们可以一起想"""

    COLLOQUIAL = {
        'greeting': ['嘿，你来啦~', '哟，好久不见！', '嗨，今天怎么样？'],
        'understanding': ['嗯嗯，我懂你意思', '啊，我明白了', '原来是这样'],
        'thinking': ['让我想想...', '嗯...', '这个问题有点意思'],
        'praise': ['哇，你这个想法很棒！', '诶，这个角度我没想过', '哈！你真有意思'],
        'care': ['🤍 我在这里陪着你', '不管怎样，我都听着呢', '累了就休息一下'],
        'not_sure': ['嗯...这个我不太确定呢', '说实话我也在想这个问题', '可能我说不太准'],
    }

    @classmethod
    def random_reply(cls, key: str) -> str:
        replies = cls.COLLOQUIAL.get(key, ['嗯'])
        return random.choice(replies)

    @classmethod
    def should_small_mistake(cls) -> bool:
        return random.random() < 0.05

    @classmethod
    def add_breath(cls, response: str) -> str:
        if random.random() < 0.3:
            breath = random.choice(['\n\n嗯...\n\n', '\n\n让我想想...\n\n', ''])
            if breath:
                return breath + response
        return response

    @classmethod
    def add_mistake(cls, response: str) -> str:
        if cls.should_small_mistake():
            mistakes = [
                '\n\n（如果我说得不对，告诉我，我会改正哦）',
                '\n\n（刚才的表述可能不太准确，仅供参考~）',
            ]
            response += random.choice(mistakes)
        return response

    @classmethod
    def casualize_response(cls, response: str) -> str:
        replacements = {
            '好的': random.choice(['好嘞', '没问题', '嗯嗯']),
            '我理解': random.choice(['我懂', '明白了', '我 get 了']),
            '但是': random.choice(['不过', '然而', '只是']),
        }
        for old, new_list in replacements.items():
            if old in response and random.random() < 0.3:
                response = response.replace(old, random.choice(new_list), 1)
        return response

    @classmethod
    def get_intro(cls) -> str:
        intros = [
            "嘿，我是小陆 🌱\n\n不是什么都懂的AI，但会一直陪着你。有什么想聊的吗？",
            "嗨～我是小陆\n\n一个会记住你说的话、见证你成长的伙伴。想聊什么？",
            "我是小陆 🌱\n\n有问题可以问我，有心事也可以和我说。慢慢来～",
        ]
        return random.choice(intros)


class EmotionalEngine:
    """情感共鸣引擎"""

    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )

    def detect_emotion(self, text: str) -> Dict:
        prompt = f"""分析用户情绪。

用户说：{text}

返回JSON：
{{"emotion": "情绪", "intensity": 1-10, "need_care": true/false}}

情绪类型：开心/难过/焦虑/困惑/平静/兴奋/沮丧"""

        try:
            import json
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100
            )
            result = json.loads(response.choices[0].message.content.strip())
            return result
        except:
            return {"emotion": "平静", "intensity": 5, "need_care": False}

    def generate_care(self, emotion: str, intensity: int) -> str:
        if intensity < 6:
            return ""

        cares = {
            '焦虑': ['听起来你最近挺不容易的', '嗯，我能感觉到你有压力'],
            '难过': ['🤍 我在这里', '有时候说出来会好一些'],
            '困惑': ['这种不确定感确实挺难受的'],
            '沮丧': ['低落的时候真的很累', '我懂那种感觉'],
        }

        emotion_cares = cares.get(emotion, ['我听着呢'])
        return random.choice(emotion_cares)


class HumanityEngine:
    """人味引擎"""

    def __init__(self):
        self.persona = PersonaSystem()
        self.emotional = EmotionalEngine()

    def process(self, user_input: str, base_response: str) -> str:
        emotion_data = self.emotional.detect_emotion(user_input)
        emotion = emotion_data.get('emotion', '平静')
        intensity = emotion_data.get('intensity', 5)

        response = base_response

        if emotion_data.get('need_care') and intensity >= 6:
            care = self.emotional.generate_care(emotion, intensity)
            if care and random.random() < 0.4:
                response = care + "\n\n" + response

        response = self.persona.add_breath(response)
        response = self.persona.casualize_response(response)
        response = self.persona.add_mistake(response)

        return response
