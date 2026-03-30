"""
主动关心系统 - 定时问候、关心工作状态
"""
import os
import time
from datetime import datetime, timedelta
from threading import Thread, Event
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# 可配置的问候模板
PROACTIVE_MESSAGES = {
    "morning": [
        "早上好呀~ 昨晚睡得好吗？今天有什么计划？",
        "新的一天开始了，今天感觉怎么样？",
        "早安！今天工作有什么安排吗？",
    ],
    "afternoon": [
        "下午好~ 工作顺利吗？有没有遇到什么困难？",
        "现在有空吗？聊聊今天过得怎么样？",
        "工作了一整天，感觉累不累？",
    ],
    "evening": [
        "晚上好~ 今天做了什么有趣的事吗？",
        "一天结束了，有什么想分享的吗？",
        "今晚有什么安排？我陪你聊聊~",
    ],
    "work_check": [
        "今天工作怎么样？有没有什么让你头疼的事？",
        "工作上还顺利吗？有什么想聊聊的？",
        "最近工作压力大吗？有什么我可以帮你的？",
    ],
    "care": [
        "最近怎么样？有什么让你烦心的事吗？",
        "我一直在呢，有什么想说的都可以告诉我~",
        "今天有什么好事或者烦心事想分享吗？",
    ],
}


class ProactiveChecker:
    """主动关心检查器"""

    def __init__(self, check_interval: int = 1800):  # 默认30分钟
        self.check_interval = check_interval  # 秒
        self.enabled = os.getenv("PROACTIVE_ENABLED", "false").lower() == "true"
        self.last_check = datetime.now()
        self.last_care = datetime.now() - timedelta(hours=6)  # 上次关心时间
        self.consecutive_checks = 0  # 连续检查次数
        self._stop_event = Event()
        self._thread: Optional[Thread] = None

    def should_remind(self) -> bool:
        """判断是否应该主动发送关心"""
        if not self.enabled:
            return False

        now = datetime.now()
        elapsed = (now - self.last_check).total_seconds()

        # 每30分钟检查一次
        if elapsed < self.check_interval:
            return False

        self.last_check = now

        # 每2小时发送一次关心（4次检查后）
        self.consecutive_checks += 1
        if self.consecutive_checks >= 4:
            self.consecutive_checks = 0
            self.last_care = now
            return True

        return False

    def get_care_message(self) -> str:
        """获取一条关心消息"""
        import random
        hour = datetime.now().hour

        if 6 <= hour < 12:
            category = "morning"
        elif 12 <= hour < 18:
            category = "afternoon"
        else:
            category = "evening"

        # 混合一些工作相关的关心
        messages = PROACTIVE_MESSAGES[category] + PROACTIVE_MESSAGES["work_check"]

        return random.choice(messages)

    def start(self):
        """启动后台检查线程"""
        if not self.enabled or self._thread:
            return

        def run():
            while not self._stop_event.is_set():
                if self.should_remind():
                    # 这里会被主循环检查并发送
                    pass
                time.sleep(60)  # 每分钟检查一次

        self._thread = Thread(target=run, daemon=True)
        self._thread.start()

    def stop(self):
        """停止后台检查"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)

    def check_and_get_message(self) -> Optional[str]:
        """检查是否应该发送关心，返回消息内容"""
        if not self.enabled:
            return None

        elapsed = (datetime.now() - self.last_check).total_seconds()
        if elapsed < self.check_interval:
            return None

        elapsed_since_care = (datetime.now() - self.last_care).total_seconds()
        if elapsed_since_care < self.check_interval * 4:
            return None

        self.last_check = datetime.now()
        self.last_care = datetime.now()
        return self.get_care_message()
