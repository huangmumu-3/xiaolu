"""
导出模块 - 生成对话记录 PDF
"""
from datetime import datetime
from core.database import CompanionDB
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm


class ConversationExporter:
    def __init__(self, db: CompanionDB):
        self.db = db

    def export_to_pdf(self, output_path: str, days: int = 30) -> str:
        """导出最近N天的对话为PDF"""
        from datetime import timedelta
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        conversations = self.db.conn.execute(
            "SELECT * FROM conversations WHERE timestamp >= ? ORDER BY timestamp",
            (start_date,)
        ).fetchall()

        if not conversations:
            return None

        # 创建PDF
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4

        # 标题
        c.setFont("Helvetica-Bold", 16)
        c.drawString(2*cm, height - 2*cm, f"AI Companion - Conversation History")
        c.setFont("Helvetica", 10)
        c.drawString(2*cm, height - 2.5*cm, f"Export Date: {datetime.now().strftime('%Y-%m-%d')}")

        y = height - 4*cm

        for conv in conversations:
            timestamp = datetime.fromisoformat(conv["timestamp"]).strftime("%Y-%m-%d %H:%M")

            # 检查是否需要换页
            if y < 3*cm:
                c.showPage()
                y = height - 2*cm

            # 用户输入
            c.setFont("Helvetica-Bold", 10)
            c.drawString(2*cm, y, f"[{timestamp}] You:")
            y -= 0.5*cm

            c.setFont("Helvetica", 9)
            self._draw_wrapped_text(c, conv["user_input"], 2.5*cm, y, width - 4*cm)
            y -= self._get_text_height(conv["user_input"], width - 4*cm) + 0.5*cm

            # AI回复
            c.setFont("Helvetica-Bold", 10)
            c.drawString(2*cm, y, "AI:")
            y -= 0.5*cm

            c.setFont("Helvetica", 9)
            self._draw_wrapped_text(c, conv["ai_response"], 2.5*cm, y, width - 4*cm)
            y -= self._get_text_height(conv["ai_response"], width - 4*cm) + 1*cm

        c.save()
        return output_path

    def _draw_wrapped_text(self, c, text, x, y, max_width):
        """绘制自动换行文本"""
        lines = self._wrap_text(text, max_width)
        for line in lines:
            c.drawString(x, y, line)
            y -= 0.4*cm
        return y

    def _wrap_text(self, text, max_width):
        """文本换行"""
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + " " + word if current_line else word
            if len(test_line) * 0.2*cm < max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)
        return lines

    def _get_text_height(self, text, max_width):
        """计算文本高度"""
        lines = self._wrap_text(text, max_width)
        return len(lines) * 0.4*cm
