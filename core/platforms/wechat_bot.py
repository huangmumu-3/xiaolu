"""
微信接入 (itchat)
"""
import os
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class WeChatBot:
    """微信机器人（基于 itchat）"""

    def __init__(self, engine):
        self.engine = engine
        self.enabled = os.getenv("WECHAT_ENABLED", "false").lower() == "true"
        self.auto_reply = os.getenv("WECHAT_AUTO_REPLY", "true").lower() == "true"
        self.reply_only_when_mentioned = os.getenv("WECHAT_REPLY_ONLY_MENTIONED", "false").lower() == "true"

        if not self.enabled:
            logger.info("微信未启用（WECHAT_ENABLED=false）")
        else:
            logger.info("✅ 微信 Bot 已配置")

    def start(self):
        """启动微信机器人"""
        if not self.enabled:
            logger.info("微信未启用，跳过启动")
            return

        try:
            import itchat
        except ImportError:
            logger.error("需要安装 itchat: pip install itchat")
            return

        @itchat.msg_register(itchat.content.TEXT)
        def handle_text(msg):
            # 跳过自己发送的消息
            if msg['FromUserName'] == itchat.originInstance.UserName:
                return

            user_text = msg['Text']
            
            # 如果需要 @ 才回复，检查消息前缀
            if self.reply_only_when_mentioned:
                if not user_text.startswith('@小陆'):
                    return
                user_text = user_text.replace('@小陆', '').strip()

            # 获取回复
            response = self.engine.chat(user_text)
            
            # 回复消息
            itchat.send(response, msg['FromUserName'])

        # 登录（会弹出二维码需要扫描）
        logger.info("正在登录微信，请扫描弹出的二维码...")
        itchat.auto_login(hotReload=True)
        itchat.run()

    def send_message_to_friend(self, friend_name: str, text: str) -> bool:
        """主动给好友发消息"""
        if not self.enabled:
            return False

        try:
            import itchat
            friends = itchat.search_friends(name=friend_name)
            if friends:
                itchat.send(text, toUserName=friends[0]['UserName'])
                return True
        except Exception as e:
            logger.error(f"微信发送失败: {e}")
        
        return False

    def send_proactive_care(self, message: str):
        """发送主动关心消息"""
        friend_name = os.getenv("WECHAT_CARE_FRIEND")
        if friend_name:
            self.send_message_to_friend(friend_name, message)
