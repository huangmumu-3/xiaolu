"""
Streamlit Web 界面
"""
import streamlit as st
import os
from datetime import datetime
from core.engine import CompanionEngine
from core.reflection import TimeReflection
from core.change_detector import ChangeDetector
from core.exporter import ConversationExporter

# 页面配置
st.set_page_config(
    page_title="AI 伴侣 - 小陆",
    page_icon="💙",
    layout="wide"
)

# 初始化
if "engine" not in st.session_state:
    st.session_state.engine = CompanionEngine()
    st.session_state.messages = []

engine = st.session_state.engine

# 侧边栏
with st.sidebar:
    st.title("💙 小陆")
    st.caption("你的 AI 伴侣")

    st.divider()

    # 功能选择
    page = st.radio(
        "功能",
        ["💬 对话", "📅 时间回望", "📊 记忆库", "📥 导出记录"]
    )

# 主页面
if page == "💬 对话":
    st.title("💬 对话")

    # 显示历史消息
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # 用户输入
    if prompt := st.chat_input("和小陆聊聊..."):
        # 显示用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # 获取AI回复
        with st.chat_message("assistant"):
            with st.spinner("小陆正在思考..."):
                response = engine.chat(prompt)
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

elif page == "📅 时间回望":
    st.title("📅 时间回望")

    reflection = TimeReflection(engine.db)
    change_detector = ChangeDetector(engine.db)

    # 本周总结
    st.subheader("本周回顾")
    summary = reflection.get_weekly_summary()
    st.info(reflection.format_summary(summary))

    # 变化识别
    st.subheader("情绪变化")
    change = change_detector.detect_emotion_change(days_ago=30)
    change_msg = change_detector.format_change_message(change)
    if change_msg:
        st.warning(change_msg)
    else:
        st.success("情绪保持稳定 ✨")

elif page == "📊 记忆库":
    st.title("📊 记忆库")

    memories = engine.db.get_memories(limit=50)

    if memories:
        for mem in memories:
            with st.expander(f"🔖 {mem['event_summary'][:50]}..."):
                st.write(f"**完整内容**: {mem['event_summary']}")
                st.write(f"**情绪**: {mem['emotion']}")
                st.write(f"**重要性**: {'⭐' * mem['importance']}")
                st.caption(f"记录时间: {mem['created_at']}")
    else:
        st.info("还没有记忆哦，多聊聊天吧~")

elif page == "📥 导出记录":
    st.title("📥 导出对话记录")

    exporter = ConversationExporter(engine.db)

    days = st.slider("导出最近几天的对话", 7, 90, 30)

    if st.button("生成 PDF"):
        output_path = f"./data/conversation_{datetime.now().strftime('%Y%m%d')}.pdf"

        with st.spinner("正在生成 PDF..."):
            result = exporter.export_to_pdf(output_path, days=days)

        if result:
            st.success(f"✅ 导出成功！")
            with open(output_path, "rb") as f:
                st.download_button(
                    label="📥 下载 PDF",
                    data=f,
                    file_name=f"conversation_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
        else:
            st.warning("没有找到对话记录")
