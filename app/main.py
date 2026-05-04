import logging
import re

from app.media import download_twilio_media, is_audio_content
from fastapi import FastAPI, Form, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from app.transcription import transcribe_mediafile, transcribe_pending_mediafiles
from app.parsing import normalize_date_text, normalize_time_text

from app.storage import (
    init_db,
    get_user_state,
    save_user_state,
    reset_user_state,
    create_appointment,
    log_message,
    list_appointments,
    list_user_states,
    list_message_logs,
    list_mediafiles,
    list_pending_mediafiles,
    get_mediafile_by_id,
    list_pending_mediafiles,
    create_mediafile
)

app = FastAPI()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


def looks_like_date(text: str) -> bool:
    if not text:
        return False
    # Usamos el nuevo helper
    if normalize_date_text(text) is not None:
        return True
        
    # Mantenemos tus regex originales como respaldo para formatos dd/mm/yyyy
    value = text.strip().lower()
    if re.search(r"\b\d{1,2}[/-]\d{1,2}([/-]\d{2,4})?\b", value):
        return True
    if re.search(r"\b\d{1,2}\s+de\s+[a-záéíóúñ]+\b", value):
        return True
    return False

def looks_like_time(text: str) -> bool:
    if not text:
        return False
    # Usamos el nuevo helper
    if normalize_time_text(text) is not None:
        return True
        
    # Mantenemos tus regex como respaldo
    value = text.strip().lower()
    if re.search(r"\b\d{1,2}\s?(de la mañana|de la tarde|de la noche)\b", value):
        return True
    return False

def looks_like_name(text: str) -> bool:
    if not text:
        return False
    value = text.strip()
    if len(value) < 5:
        return False
    invalid_values = {"ok", "hola", "si", "sí", "yo", "no"}
    if value.lower() in invalid_values:
        return False
    parts = [p for p in value.split() if p.strip()]
    if len(parts) < 2:
        return False
    return True

def looks_like_service(text: str) -> bool:
    if not text:
        return False
    value = text.strip()
    if len(value) < 3:
        return False
    invalid_values = {"ok", "hola", "si", "sí", "no", "yo", "cita"}
    if value.lower() in invalid_values:
        return False
    return True

def build_twiml_message(text: str) -> Response:
    resp = MessagingResponse()
    msg = resp.message()
    msg.body(text)
    return Response(content=str(resp), media_type="application/xml")


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("Base de datos inicializada")


@app.get("/health")
def health():
    return {"status": "ok", "service": "whatsapp-mvp-sqlite"}

@app.get("/debug/appointments")
def debug_appointments(limit: int = 50):
    return {
        "count": len(list_appointments(limit)),
        "items": list_appointments(limit)
    }


@app.get("/debug/states")
def debug_states(limit: int = 50):
    return {
        "count": len(list_user_states(limit)),
        "items": list_user_states(limit)
    }


@app.get("/debug/logs")
def debug_logs(limit: int = 100):
    return {
        "count": len(list_message_logs(limit)),
        "items": list_message_logs(limit)
    }

@app.get("/debug/media")
def debug_media(limit: int = 100):
    return {
        "count": len(list_mediafiles(limit)),
        "items": list_mediafiles(limit)
    }

@app.get("/debug/media/pending")
def debug_media_pending(limit: int = 20):
    items = list_pending_mediafiles(limit)
    return {
        "count": len(items),
        "items": items
    }

@app.post("/debug/media/{mediafile_id}/transcribe")
def debug_transcribe_media(mediafile_id: int):
    mediafile = get_mediafile_by_id(mediafile_id)

    if not mediafile:
        return {
            "ok": False,
            "error": "mediafile not found",
            "mediafile_id": mediafile_id
        }

    result = transcribe_mediafile(mediafile)
    return result


@app.post("/whatsapp")

async def whatsapp_webhook(request: Request):

    form = await request.form()

    incoming = (form.get("Body") or "").strip()
    incoming_lower = incoming.lower()
    From = form.get("From") or ""
    num_media = int(form.get("NumMedia") or "0")
    media_content_type_0 = (form.get("MediaContentType0") or "").strip()

    logger.info(
        "INBOUND | from=%s | body=%s | num_media=%s",
        From, incoming, num_media
    )

    if num_media == 0:
        log_message(
            phone=From,
            direction="in",
            body=incoming,
            num_media=num_media,
            media_content_type=media_content_type_0 or None
        )

    user = get_user_state(From)

    # Comandos globales
    if incoming_lower in ["cancelar", "cancelar cita", "salir"]:
        reset_user_state(From)
        reply = (
            "Listo, cancelé el proceso actual.\n"
            "Si quieres empezar de nuevo, escribe: quiero una cita"
        )
        logger.info("STATE RESET | from=%s | reason=cancelar", From)
        log_message(phone=From, direction="out", body=reply)
        return build_twiml_message(reply)

    if incoming_lower in ["reiniciar", "inicio", "menu", "menú", "empezar de nuevo"]:
        reset_user_state(From)
        reply = (
            "Reinicié la conversación.\n"
            "Puedo ayudarte a agendar una cita, consultar horario o ubicación."
        )
        logger.info("STATE RESET | from=%s | reason=reiniciar", From)
        log_message(phone=From, direction="out", body=reply)
        return build_twiml_message(reply)

    if (
        "humano" in incoming_lower
        or "asesor" in incoming_lower
        or "persona" in incoming_lower
        or "recepcionista" in incoming_lower
    ):
        reply = (
            "Claro. Te canalizo con una persona del equipo en cuanto sea posible.\n"
            "Si quieres, también puedo tomar tus datos para la cita."
        )
        logger.info("HUMAN REQUEST | from=%s", From)
        log_message(phone=From, direction="out", body=reply)
        return build_twiml_message(reply)

    # Detección de media / audio

    if num_media > 0:
        logger.info(
            "MEDIA DETECTED | from=%s | num_media=%s",
            From, num_media
        )

        any_audio = False

        message_log_id = log_message(
            phone=From,
            direction="in",
            body=incoming,
            num_media=num_media,
            media_content_type=None,
            media_url=None,
            media_local_path=None
        )

        for i in range(num_media):
            media_url = (form.get(f"MediaUrl{i}") or "").strip()
            media_content_type = (form.get(f"MediaContentType{i}") or "").strip()

            if not media_url and not media_content_type:
                continue

            if is_audio_content(media_content_type):
                any_audio = True

            local_media_path = None
            size_bytes = None
            processing_status = "pending"

            error_message = None

            try:
                downloaded = download_twilio_media(
                    media_url=media_url,
                    phone=From,
                    content_type=media_content_type
                )
                local_media_path = downloaded["filepath"]
                size_bytes = downloaded["size_bytes"]
                processing_status = "downloaded"

                logger.info(
                    "MEDIA DOWNLOADED | from=%s | index=%s | path=%s | size=%s",
                    From, i, downloaded["filepath"], downloaded["size_bytes"]
                )
            except Exception as e:
                processing_status = "failed"
                error_message = str(e)
                logger.exception(
                    "MEDIA DOWNLOAD ERROR | from=%s | index=%s | error=%s",
                    From, i, str(e)
                )


            create_mediafile(
                phone=From,
                messagelog_id=message_log_id,
                media_url=media_url or None,
                media_content_type=media_content_type or None,
                local_path=local_media_path,
                size_bytes=size_bytes,
                processing_status=processing_status,
                error_message=error_message,
                transcript_text=None
            )

        if any_audio:
            reply = (
                "Recibí tu audio correctamente.\n"
                "Aún no lo transcribo automáticamente, pero ya quedó registrado para la siguiente fase del prototipo.\n"
                "Si quieres continuar por texto, escribe: quiero una cita"
            )
        else:
            reply = (
                "Recibí tu archivo correctamente.\n"
                "Por ahora este prototipo todavía no procesa ese tipo de archivo automáticamente.\n"
                "Si quieres, escríbeme por texto: quiero una cita"
            )

        log_message(phone=From, direction="out", body=reply)
        return build_twiml_message(reply)

    # Respuestas globales informativas
    if "horario" in incoming_lower:
        reply = "Nuestro horario es de lunes a sábado de 9 AM a 6 PM."
        log_message(phone=From, direction="out", body=reply)
        return build_twiml_message(reply)

    if (
        "ubicacion" in incoming_lower
        or "ubicación" in incoming_lower
        or "direccion" in incoming_lower
        or "dirección" in incoming_lower
    ):
        reply = "Estamos en Av. Principal 123, Colonia Centro."
        log_message(phone=From, direction="out", body=reply)
        return build_twiml_message(reply)

    # Flujo por estado
    if user["state"] == "inicio":
        if "cita" in incoming_lower or "agendar" in incoming_lower:
            save_user_state(
                phone=From,
                state="esperando_servicio",
                servicio=user["servicio"],
                fecha=user["fecha"],
                hora=user["hora"],
                nombre=user["nombre"]
            )
            reply = (
                "Con gusto. ¿Qué servicio necesitas?\n"
                "Ejemplo: limpieza dental, consulta, corte, barba."
            )
            logger.info("STATE CHANGE | from=%s | state=esperando_servicio", From)
            log_message(phone=From, direction="out", body=reply)
            return build_twiml_message(reply)

        reply = (
            "Hola. Puedo ayudarte a:\n"
            "1) agendar una cita\n"
            "2) consultar horario\n"
            "3) consultar ubicación\n\n"
            "Escribe, por ejemplo: quiero una cita"
        )
        log_message(phone=From, direction="out", body=reply)
        return build_twiml_message(reply)

    elif user["state"] == "esperando_servicio":

        if not looks_like_service(incoming):
            reply = (
                "No alcancé a entender el servicio.\n"
                "Por favor escríbelo de nuevo. Ejemplo: limpieza dental."
            )
            log_message(phone=From, direction="out", body=reply)
            return build_twiml_message(reply)

        save_user_state(
            phone=From,
            state="esperando_fecha",
            servicio=incoming,
            fecha=user["fecha"],
            hora=user["hora"],
            nombre=user["nombre"]
        )
        reply = f"Perfecto, te ayudo con {incoming}. ¿Para qué día quieres la cita?"
        logger.info("STATE CHANGE | from=%s | state=esperando_fecha | servicio=%s", From, incoming)
        log_message(phone=From, direction="out", body=reply)
        return build_twiml_message(reply)

    elif user["state"] == "esperando_fecha":
        if not looks_like_date(incoming):
            reply = (
                "No alcancé a entender la fecha.\n"
                "Escríbeme algo como: mañana, viernes o 15 de mayo."
            )
            log_message(phone=From, direction="out", body=reply)
            return build_twiml_message(reply)

        save_user_state(
            phone=From,
            state="esperando_hora",
            servicio=user["servicio"],
            fecha=incoming,
            hora=user["hora"],
            nombre=user["nombre"]
        )
        reply = f"Entendido. ¿A qué hora quieres tu cita para {user['servicio']}?"
        logger.info("STATE CHANGE | from=%s | state=esperando_hora | fecha=%s", From, incoming)
        log_message(phone=From, direction="out", body=reply)
        return build_twiml_message(reply)

    elif user["state"] == "esperando_hora":
        if not looks_like_time(incoming):
            reply = (
                "No alcancé a entender la hora.\n"
                "Escríbeme algo como: 5 pm, 10:30 am o 4 de la tarde."
            )
            log_message(phone=From, direction="out", body=reply)
            return build_twiml_message(reply)

        save_user_state(
            phone=From,
            state="esperando_nombre",
            servicio=user["servicio"],
            fecha=user["fecha"],
            hora=incoming,
            nombre=user["nombre"]
        )
        reply = "Gracias. ¿Me compartes tu nombre completo?"
        logger.info("STATE CHANGE | from=%s | state=esperando_nombre | hora=%s", From, incoming)
        log_message(phone=From, direction="out", body=reply)
        return build_twiml_message(reply)

    elif user["state"] == "esperando_nombre":

        if not looks_like_name(incoming):
            reply = (
                "Por favor compárteme tu nombre completo para registrar la solicitud.\n"
                "Ejemplo: Juan Pérez"
            )
            log_message(phone=From, direction="out", body=reply)
            return build_twiml_message(reply)

        create_appointment(
            phone=From,
            nombre=incoming,
            servicio=user["servicio"],
            fecha=user["fecha"],
            hora=user["hora"],
            status="solicitada"
        )

        reply = (
            f"Gracias, {incoming}.\n"
            f"Tu solicitud para {user['servicio']} el {user['fecha']} a las {user['hora']} quedó registrada.\n\n"
            "Si deseas hacer otra solicitud, escribe: quiero una cita"
        )

        logger.info(
            "APPOINTMENT CREATED | from=%s | nombre=%s | servicio=%s | fecha=%s | hora=%s",
            From, incoming, user["servicio"], user["fecha"], user["hora"]
        )

        reset_user_state(From)
        log_message(phone=From, direction="out", body=reply)
        return build_twiml_message(reply)

    # Fallback
    reply = (
        "No te entendí del todo.\n"
        "Si quieres agendar, escribe: quiero una cita.\n"
        "También puedes escribir: horario, ubicación, cancelar o reiniciar."
    )
    logger.warning("FALLBACK | from=%s | state=%s | body=%s", From, user["state"], incoming)
    log_message(phone=From, direction="out", body=reply)
    return build_twiml_message(reply)

@app.post("/debug/media/transcribe-pending")
def debug_transcribe_pending_media(limit: int = 20):
    mediafiles = list_pending_mediafiles(limit)
    results = transcribe_pending_mediafiles(mediafiles)

    return {
        "count": len(results),
        "items": results
    }


