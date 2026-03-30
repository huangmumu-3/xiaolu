#!/bin/bash
# 快速启动脚本

echo "🚀 AI 伴侣 - 小陆"
echo ""
echo "请选择运行模式："
echo "1) 终端对话"
echo "2) Streamlit Web 界面"
echo "3) Flask API 服务"
echo ""
read -p "输入选项 (1-3): " choice

case $choice in
    1)
        python3 main.py
        ;;
    2)
        streamlit run app.py
        ;;
    3)
        python3 main.py --mode web
        ;;
    *)
        echo "无效选项"
        exit 1
        ;;
esac
