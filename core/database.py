"""
数据库模块 - 存储对话和记忆
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


class CompanionDB:
    def __init__(self, db_path: str = "./data/companion.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        # 对话记录
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        # 重要事件（AI 提取的关键记忆）
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_summary TEXT NOT NULL,
                emotion TEXT,
                importance INTEGER DEFAULT 5,
                created_at TEXT NOT NULL,
                related_conv_id INTEGER,
                FOREIGN KEY (related_conv_id) REFERENCES conversations(id)
            )
        """)

        # 待跟进事项（见证者系统用）
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS followups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                context TEXT,
                urgency TEXT DEFAULT 'normal',
                followup_at TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL
            )
        """)

        # 话题统计（见证者用）
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS topic_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                count INTEGER DEFAULT 1,
                last_seen TEXT NOT NULL
            )
        """)

        # 每日总结
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                summary TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # 指导模式设置
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS guidance_settings (
                user_id TEXT PRIMARY KEY,
                guidance_enabled INTEGER DEFAULT 0,
                updated_at TEXT
            )
        """)

        self.conn.commit()

    def save_conversation(self, user_input: str, ai_response: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO conversations (user_input, ai_response, timestamp) VALUES (?, ?, ?)",
            (user_input, ai_response, datetime.now().isoformat())
        )
        self.conn.commit()
        return cur.lastrowid

    def save_memory(self, summary: str, emotion: str, importance: int, conv_id: int):
        self.conn.execute(
            "INSERT INTO memories (event_summary, emotion, importance, created_at, related_conv_id) VALUES (?, ?, ?, ?, ?)",
            (summary, emotion, importance, datetime.now().isoformat(), conv_id)
        )
        self.conn.commit()

    def get_recent_conversations(self, limit: int = 10):
        return self.conn.execute(
            "SELECT * FROM conversations ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()

    def get_memories(self, limit: int = 20):
        return self.conn.execute(
            "SELECT * FROM memories ORDER BY importance DESC, created_at DESC LIMIT ?", (limit,)
        ).fetchall()

    def close(self):
        self.conn.close()
