import sqlite3
import datetime
from core.logging_config import logger

def setup_db():
    conn = sqlite3.connect("classification_logs.db")
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS classification_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        text_length INTEGER,
        label TEXT,
        confidence REAL
    )
    ''')
    conn.commit()
    conn.close()

def log_classification(text_length: int, label: str, confidence: float):
    try:
        conn = sqlite3.connect("classification_logs.db")
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO classification_logs (timestamp, text_length, label, confidence)
            VALUES (?, ?, ?, ?)
        ''', (timestamp, text_length, label, confidence))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Database logging error: {e}")
