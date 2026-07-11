import sqlite3
import os
import datetime
from jarvis.logger import logger

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "jarvis_memory.db")

class MemoryManager:
    def __init__(self):
        self.conn = None
        self._init_db()

    def _init_db(self):
        try:
            self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
            cursor = self.conn.cursor()
            
            # Conversation History Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    role TEXT,
                    message TEXT
                )
            """)
            
            # User Profiles & Preferences Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            # Notes Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    title TEXT PRIMARY KEY,
                    content TEXT,
                    timestamp TEXT
                )
            """)
            self.conn.commit()
            logger.info(f"[Memory] SQLite database initialized at {DB_FILE}")
        except Exception as e:
            logger.error(f"[Memory] SQLite initialization failed: {e}")

    def add_note(self, title: str, content: str):
        try:
            cursor = self.conn.cursor()
            ts = datetime.datetime.now().isoformat()
            cursor.execute("INSERT OR REPLACE INTO notes (title, content, timestamp) VALUES (?, ?, ?)", (title, content, ts))
            self.conn.commit()
        except Exception as e:
            logger.error(f"[Memory] Failed to save note: {e}")

    def get_all_notes(self) -> list:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT title, content FROM notes ORDER BY timestamp DESC")
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"[Memory] Failed to load notes: {e}")
            return []

    def delete_note(self, title: str):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM notes WHERE title = ?", (title,))
            self.conn.commit()
        except Exception as e:
            logger.error(f"[Memory] Failed to delete note: {e}")

    def add_message(self, role: str, message: str):
        try:
            cursor = self.conn.cursor()
            ts = datetime.datetime.now().isoformat()
            cursor.execute("INSERT INTO conversation (timestamp, role, message) VALUES (?, ?, ?)", (ts, role, message))
            self.conn.commit()
        except Exception as e:
            logger.error(f"[Memory] Failed to add message: {e}")

    def get_recent_messages(self, limit: int = 15) -> list:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT role, message FROM conversation ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            # Order them chronologically for context
            return rows[::-1]
        except Exception as e:
            logger.error(f"[Memory] Failed to retrieve messages: {e}")
            return []

    def clear_history(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM conversation")
            self.conn.commit()
            logger.info("[Memory] Conversation history cleared.")
        except Exception as e:
            logger.error(f"[Memory] Failed to clear history: {e}")

    def set_preference(self, key: str, value: str):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO preferences (key, value) VALUES (?, ?)", (key, value))
            self.conn.commit()
        except Exception as e:
            logger.error(f"[Memory] Failed to save preference {key}: {e}")

    def get_preference(self, key: str, default: str = None) -> str:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT value FROM preferences WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default
        except Exception as e:
            logger.error(f"[Memory] Failed to fetch preference {key}: {e}")
            return default

    def close(self):
        if self.conn:
            self.conn.close()

_memory_manager = None

def get_memory() -> MemoryManager:
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
