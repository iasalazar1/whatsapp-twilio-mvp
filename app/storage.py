import os
import sqlite3
from datetime import datetime

DB_PATH = os.getenv("SQLITE_PATH", "data/app.db")

MEDIA_STATUS_PENDING = "pending"
MEDIA_STATUS_DOWNLOADED = "downloaded"
MEDIA_STATUS_FAILED = "failed"
MEDIA_STATUS_TRANSCRIBING = "transcribing"
MEDIA_STATUS_TRANSCRIBED = "transcribed"
MEDIA_STATUS_TRANSCRIPTION_FAILED = "transcription_failed"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_states (
        phone TEXT PRIMARY KEY,
        state TEXT NOT NULL,
        servicio TEXT,
        fecha TEXT,
        hora TEXT,
        nombre TEXT,
        updated_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT NOT NULL,
        nombre TEXT,
        servicio TEXT,
        fecha TEXT,
        hora TEXT,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS message_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT,
        direction TEXT NOT NULL,
        body TEXT,
        num_media INTEGER DEFAULT 0,
        media_content_type TEXT,
        media_url TEXT,
        media_local_path TEXT,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS mediafiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT NOT NULL,
        messagelog_id INTEGER,
        media_url TEXT,
        media_content_type TEXT,
        local_path TEXT,
        size_bytes INTEGER,
        processing_status TEXT NOT NULL,
        error_message TEXT,
        transcript_text TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (messagelog_id) REFERENCES message_logs(id)
    )
    """)

    conn.commit()
    conn.close()


def now_iso():
    return datetime.utcnow().isoformat()


def get_user_state(phone: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_states WHERE phone = ?", (phone,))
    row = cur.fetchone()
    conn.close()

    if row:
        return dict(row)

    return {
        "phone": phone,
        "state": "inicio",
        "servicio": None,
        "fecha": None,
        "hora": None,
        "nombre": None,
        "updated_at": now_iso()
    }


def save_user_state(phone: str, state: str, servicio=None, fecha=None, hora=None, nombre=None):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO user_states (phone, state, servicio, fecha, hora, nombre, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(phone) DO UPDATE SET
        state=excluded.state,
        servicio=excluded.servicio,
        fecha=excluded.fecha,
        hora=excluded.hora,
        nombre=excluded.nombre,
        updated_at=excluded.updated_at
    """, (
        phone,
        state,
        servicio,
        fecha,
        hora,
        nombre,
        now_iso()
    ))

    conn.commit()
    conn.close()


def reset_user_state(phone: str):
    save_user_state(
        phone=phone,
        state="inicio",
        servicio=None,
        fecha=None,
        hora=None,
        nombre=None
    )


def create_appointment(phone: str, nombre: str, servicio: str, fecha: str, hora: str, status: str = "solicitada"):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO appointments (phone, nombre, servicio, fecha, hora, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        phone,
        nombre,
        servicio,
        fecha,
        hora,
        status,
        now_iso()
    ))

    conn.commit()
    conn.close()


def log_message(
    phone: str,
    direction: str,
    body: str,
    num_media: int = 0,
    media_content_type: str = None,
    media_url: str = None,
    media_local_path: str = None
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO message_logs (
        phone, direction, body, num_media, media_content_type, media_url, media_local_path, created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        phone,
        direction,
        body,
        num_media,
        media_content_type,
        media_url,
        media_local_path,
        now_iso()
    ))

    message_log_id = cur.lastrowid
    conn.commit()
    conn.close()
    return message_log_id


def create_mediafile(
    phone: str,
    messagelog_id: int = None,
    media_url: str = None,
    media_content_type: str = None,
    local_path: str = None,
    size_bytes: int = None,
    processing_status: str = "pending",
    error_message: str = None,
    transcript_text: str = None
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO mediafiles (
        phone, messagelog_id, media_url, media_content_type, local_path,
        size_bytes, processing_status, error_message, transcript_text, created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        phone,
        messagelog_id,
        media_url,
        media_content_type,
        local_path,
        size_bytes,
        processing_status,
        error_message,
        transcript_text,
        now_iso()
    ))

    mediafile_id = cur.lastrowid
    conn.commit()
    conn.close()
    return mediafile_id


def list_appointments(limit: int = 50):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT id, phone, nombre, servicio, fecha, hora, status, created_at
    FROM appointments
    ORDER BY id DESC
    LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def list_user_states(limit: int = 50):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT phone, state, servicio, fecha, hora, nombre, updated_at
    FROM user_states
    ORDER BY updated_at DESC
    LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def list_message_logs(limit: int = 100):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT id, phone, direction, body, num_media, media_content_type, media_url, media_local_path, created_at
    FROM message_logs
    ORDER BY id DESC
    LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def list_mediafiles(limit: int = 100):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT id, phone, messagelog_id, media_url, media_content_type, local_path,
           size_bytes, processing_status, error_message, transcript_text, created_at
    FROM mediafiles
    ORDER BY id DESC
    LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def list_pending_mediafiles(limit: int = 20):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT id, phone, messagelog_id, media_url, media_content_type, local_path,
           size_bytes, processing_status, error_message, transcript_text, created_at
    FROM mediafiles
    WHERE processing_status IN ('downloaded', 'pending')
    ORDER BY id ASC
    LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_mediafile_processing(
    mediafile_id: int,
    processing_status: str,
    transcript_text: str = None,
    error_message: str = None
):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    UPDATE mediafiles
    SET processing_status = ?,
        transcript_text = ?,
        error_message = ?
    WHERE id = ?
    """, (
        processing_status,
        transcript_text,
        error_message,
        mediafile_id
    ))
    conn.commit()
    conn.close()

def get_mediafile_by_id(mediafile_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT id, phone, messagelog_id, media_url, media_content_type, local_path,
           size_bytes, processing_status, error_message, transcript_text, created_at
    FROM mediafiles
    WHERE id = ?
    """, (mediafile_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None



