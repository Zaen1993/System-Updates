"""
media/database.py
قاعدة بيانات SQLite محلية لتسجيل الصور التي تم إرسالها من المعرض
لمنع إعادة إرسالها مرة أخرى.
"""

import os
import sqlite3
import threading

class DatabaseManager:
    """
    إدارة قاعدة بيانات SQLite لتخزين مسارات الصور المرسلة وتواريخها.
    """

    def __init__(self, db_path=None):
        if db_path is None:
            # تخزين قاعدة البيانات داخل مجلد التطبيق الخاص
            db_path = os.path.join(os.getcwd(), "data", "sent_images.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.lock = threading.Lock()
        self._create_tables()

    def _create_tables(self):
        """إنشاء الجداول اللازمة إذا لم تكن موجودة."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sent_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    sent_date TEXT NOT NULL,
                    source TEXT DEFAULT 'gallery'
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            conn.commit()
            conn.close()

    def is_image_sent(self, file_path):
        """التحقق مما إذا كانت الصورة قد أُرسلت سابقاً."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM sent_images WHERE file_path = ?", (file_path,))
            result = cursor.fetchone() is not None
            conn.close()
            return result

    def mark_as_sent(self, file_path, source='gallery'):
        """تسجيل الصورة كمرسلة."""
        from datetime import datetime
        sent_date = datetime.now().isoformat()
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO sent_images (file_path, sent_date, source) VALUES (?, ?, ?)",
                    (file_path, sent_date, source)
                )
                conn.commit()
            except sqlite3.IntegrityError:
                # موجود بالفعل
                pass
            finally:
                conn.close()

    def get_unsent_images(self, limit=25):
        """
        الحصول على قائمة بالصور غير المرسلة من المعرض (حتى limit).
        يفترض أننا نمرر قائمة بكل الصور 🔞 المكتشفة، ثم نستبعد المرسلة.
        لكن هذه الدالة ترجع فقط المسارات المسجلة كمرسلة، لذا نستخدمها للتصفية.
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT file_path FROM sent_images")
            sent_paths = {row[0] for row in cursor.fetchall()}
            conn.close()
            return sent_paths

    def reset_all(self):
        """مسح قاعدة البيانات (للتجربة أو عند الطلب)."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sent_images")
            cursor.execute("DELETE FROM settings")
            conn.commit()
            conn.close()

    def set_setting(self, key, value):
        """تخزين إعداد (مثل آخر وقت إرسال)."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
            conn.commit()
            conn.close()

    def get_setting(self, key, default=None):
        """استرداد إعداد."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else default
