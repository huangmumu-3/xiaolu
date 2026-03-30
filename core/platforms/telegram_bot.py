"""
Telegram Bot 接入
"""
import os
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram 机器人"""

    def __init__(self, engine):
        self.engine = engine
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.bot_token and self.chat_id)

        if not self.enabled:
            logger.info("Telegram 未配置（TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID 未设置）")
        else:
            logger.info("✅ Telegram Bot 已配置")

    def send_message(self, text: str) -> bool:
        """发送消息"""
        if not self.enabled:
            return False

        import requests
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }

        try:
            resp = requests.post(url, data=data, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Telegram 发送失败: {e}")
            return False

    def set_webhook(self, webhook_url: str) -> bool:
        """设置 Webhook"""
        if not self.enabled:
            return False

        import requests
        
        url = f"https://api.telegram.org/bot{self.bot_token}/setWebhook"
        data = {"url": webhook_url}

        try:
            resp = requests.post(url, json=data, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Telegram Webhook 设置失败: {e}")
            return False

    def handle_update(self, update: dict) -> Optional[str]:
        """处理更新"""
        if "message" not in update:
            return None

        message = update["message"]
        if "text" not in message:
            return None

        user_text = message["text"]
        response = self.engine.chat(user_text)
        return response
