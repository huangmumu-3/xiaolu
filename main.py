"""
AI 伴侣 - 小陆
支持：终端对话、Telegram、微信、主动关心、时间回望、见证者
"""
import os
import argparse
from dotenv import load_dotenv
from core.engine import CompanionEngine

load_dotenv()


def run_terminal():
    """终端交互模式"""
    print("=" * 50)
    print("  AI 伴侣 - 小陆")
    print("  见证你的变化，陪伴你的成长")
    print("=" * 50)

    engine = CompanionEngine()
    proactive_enabled = os.getenv("PROACTIVE_ENABLED", "false").lower() == "true"

    if proactive_enabled:
        print("\n✨ 主动关心模式已开启")

    print("\n命令：")
    print("  /review       - 查看本周回顾")
    print("  /monthly      - 查看本月回顾")
    print("  /followups    - 查看待跟进事项")
    print("  /past N个月前 - 查看过去某个时间段")
    print("  /trend 话题   - 查看话题变化趋势")
    print("  /stuck        - 查看反复纠结的卡点")
    print("  /guidance     - 开启/关闭指导模式")
    print("  /lookback     - 主动提起历史话题")
    print("  /witness      - 查看你的变化见证")
    print("  /quit         - 退出\n")

    try:
        while True:
            # 检查主动关心
            proactive_msg = engine.proactive_check()
            if proactive_msg:
                print(f"\n小陆: {proactive_msg}")

            # 检查见证者提醒
            witness_msgs = engine.witness_check()
            for msg in witness_msgs:
                print(f"\n💭 见证提醒: {msg}")

            user_input = input("\n你: ").strip()

            if user_input.lower() in ['quit', '/quit', '退出']:
                print("\n小陆: 期待下次见面 :)")
                break

            # 命令处理
            if user_input == '/review':
                print("\n📅 生成周回顾中...")
                review_text = engine.review.generate_weekly_review()
                print(f"\n{review_text}")
                continue
            elif user_input == '/monthly':
                print("\n📅 生成月回顾中...")
                review_text = engine.review.generate_monthly_review()
                print(f"\n{review_text}")
                continue
            elif user_input == '/followups':
                pending = engine.witness.get_pending_followups()
                if pending:
                    print("\n📋 待跟进事项：")
                    for p in pending:
                        print(f"  • {p['topic']} - {p['context'][:50]}...")
                else:
                    print("\n📋 暂时没有待跟进的事项")
                continue
            elif user_input.startswith('/past') or '个月前' in user_input or '周前' in user_input:
                result = engine.query_past(user_input)
                print(f"\n{result}")
                continue
            elif user_input.startswith('/trend'):
                topic = user_input.replace('/trend', '').strip()
                if topic:
                    result = engine.get_topic_trend(topic)
                    print(f"\n{result}")
                else:
                    print("用法：/trend 话题名（如 /trend 工作）")
                continue
            elif user_input == '/stuck':
                result = engine.guidance.get_stuck_points_report(engine.user_id)
                print(f"\n{result}")
                continue
            elif user_input == '/guidance':
                current = engine.guidance.is_guidance_enabled(engine.user_id)
                if current:
                    engine.guidance.set_guidance_enabled(engine.user_id, False)
                    print("\n🔕 指导模式已关闭，我只会陪伴，不会主动分析了")
                else:
                    engine.guidance.set_guidance_enabled(engine.user_id, True)
                    print("\n🔔 指导模式已开启")
                    print("   当我发现你反复纠结某个话题时，会温和地和你聊聊")
                    print("   随时可以用 /guidance 关闭")
                continue
            elif user_input == '/lookback':
                result = engine.lookback.get_due_lookback()
                if result:
                    print(f"\n💭 {result['message']}")
                else:
                    print("\n暂时没有需要回望的话题")
                continue
            elif user_input == '/witness':
                result = engine.change_witness.generate_witness_report()
                print(f"\n{result}")
                continue

            if not user_input:
                continue

            response = engine.chat(user_input)
            print(f"\n小陆: {response}")

    except KeyboardInterrupt:
        print("\n\n小陆: 期待下次见面 :)")
    finally:
        engine.close()


def run_telegram():
    """Telegram 模式"""
    from flask import Flask, request, jsonify
    import requests

    engine = CompanionEngine()

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("❌ 请先设置 TELEGRAM_BOT_TOKEN")
        return

    app = Flask(__name__)

    def send_message(chat_id, text):
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text})

    @app.route(f"/{bot_token}", methods=["POST"])
    def telegram_webhook():
        update = request.get_json()
        
        if "message" not in update:
            return "ok"
        
        msg = update["message"]
        if "text" not in msg:
            return "ok"

        chat_id = msg["chat"]["id"]
        user_text = msg["text"]

        # 处理命令
        if user_text == "/review":
            review = engine.review.generate_weekly_review()
            send_message(chat_id, f"📅 周回顾：\n\n{review}")
        elif user_text == "/monthly":
            review = engine.review.generate_monthly_review()
            send_message(chat_id, f"📅 月回顾：\n\n{review}")
        elif user_text == "/followups":
            pending = engine.witness.get_pending_followups()
            if pending:
                text = "📋 待跟进事项：\n\n"
                for p in pending:
                    text += f"• {p['topic']}\n  {p['context'][:50]}...\n\n"
                send_message(chat_id, text)
            else:
                send_message(chat_id, "📋 暂时没有待跟进的事项")
        elif user_text == "/start":
            send_message(chat_id, "你好！我是小陆～\n随时可以和我聊聊，我会记住你说的话，也会见证你的变化。")
        else:
            response = engine.chat(user_text)
            send_message(chat_id, response)

        return "ok"

    port = int(os.getenv("PORT", 5000))
    print(f"📱 Telegram Bot 运行中，端口: {port}")
    app.run(host="0.0.0.0", port=port)


def main():
    parser = argparse.ArgumentParser(description="AI 伴侣 - 小陆")
    parser.add_argument(
        "--mode",
        choices=["terminal", "telegram"],
        default="terminal",
        help="运行模式"
    )
    args = parser.parse_args()

    if args.mode == "telegram":
        run_telegram()
    else:
        run_terminal()


if __name__ == "__main__":
    main()
