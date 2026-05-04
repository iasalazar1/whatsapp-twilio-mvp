import os
from datetime import datetime
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
MEDIA_DIR = os.getenv("MEDIA_DIR", "media")


def ensure_media_dir():
    os.makedirs(MEDIA_DIR, exist_ok=True)


def guess_extension(content_type: str) -> str:
    mapping = {
        "audio/ogg": ".ogg",
        "audio/mpeg": ".mp3",
        "audio/mp3": ".mp3",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/mp4": ".m4a",
        "audio/aac": ".aac",
        "video/mp4": ".mp4",
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "application/pdf": ".pdf",
    }
    return mapping.get(content_type, "")


def build_filename(phone: str, content_type: str) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_phone = phone.replace("whatsapp:", "").replace("+", "").replace(":", "_")
    ext = guess_extension(content_type)
    return f"{timestamp}_{safe_phone}{ext}"


def download_twilio_media(media_url: str, phone: str, content_type: str):
    ensure_media_dir()

    filename = build_filename(phone, content_type)
    filepath = os.path.join(MEDIA_DIR, filename)

    response = requests.get(
        media_url,
        auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
        timeout=30
    )
    response.raise_for_status()

    with open(filepath, "wb") as f:
        f.write(response.content)

    return {
        "filepath": filepath,
        "filename": filename,
        "content_type": content_type,
        "size_bytes": len(response.content)
    }


def is_audio_content(content_type: str) -> bool:
    return (content_type or "").startswith("audio/")
