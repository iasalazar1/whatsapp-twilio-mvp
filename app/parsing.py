import re
import unicodedata


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def _normalize_base_text(text: str) -> str:
    text = text.strip().lower()
    text = _strip_accents(text)
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_date_text(text: str) -> str | None:
    value = _normalize_base_text(text)

    if value == "hoy":
        return "today"

    if value == "manana":
        return "tomorrow"

    weekdays = {
        "lunes": "weekday:0",
        "martes": "weekday:1",
        "miercoles": "weekday:2",
        "jueves": "weekday:3",
        "viernes": "weekday:4",
        "sabado": "weekday:5",
        "domingo": "weekday:6",
    }

    return weekdays.get(value)


def normalize_time_text(text: str) -> str | None:
    value = _normalize_base_text(text)

    m = re.fullmatch(r"(\d{1,2})\s*(am|pm)", value)
    if m:
        hour = int(m.group(1))
        suffix = m.group(2)

        if hour < 1 or hour > 12:
            return None

        if suffix == "am":
            hour = 0 if hour == 12 else hour
        else:
            hour = 12 if hour == 12 else hour + 12

        return f"{hour:02d}:00"

    m = re.fullmatch(r"(\d{1,2}):(\d{2})\s*(am|pm)", value)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))
        suffix = m.group(3)

        if hour < 1 or hour > 12 or minute < 0 or minute > 59:
            return None

        if suffix == "am":
            hour = 0 if hour == 12 else hour
        else:
            hour = 12 if hour == 12 else hour + 12

        return f"{hour:02d}:{minute:02d}"

    m = re.fullmatch(r"(\d{1,2}):(\d{2})", value)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))

        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            return None

        return f"{hour:02d}:{minute:02d}"

    return None
