#!/usr/bin/env python3
"""
微信启动脚本 - 使用 wxpy
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from wxpy import Bot, TEXT
from core.engine import CompanionEngine

engine = CompanionEngine()

print("="*50)
print("  小陆微信版启动中...")
print("="*50)

# 登录
bot = Bot(cache_path=True, console_qr=True)

print("\n✅ 登录成功！")

# 获取自己
myself = bot.self
print(f"登录账号: {myself.name}")

# 找到文件传输助手
file_helper = bot.file_helper

print("\n" + "-"*50)
print("📍 使用方法：")
print("   • 在微信里给自己发消息")
print("   • 或找到'文件传输助手'发消息")
print("   • 小陆会自动回复你")
print("-"*50)

@bot.register(myself, TEXT)
def reply_to_self(msg):
    print(f"\n📩 收到: {msg.text}")
    response = engine.chat(msg.text)
    print(f"📤 回复: {response}")
    return response

@bot.register(file_helper, TEXT)
def reply_to_file_helper(msg):
    print(f"\n📩 收到: {msg.text}")
    response = engine.chat(msg.text)
    print(f"📤 回复: {response}")
    return response

# 保持运行
print("\n⏳ 小陆正在运行中，等待消息...")
bot.join()
