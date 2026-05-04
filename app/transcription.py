from app.storage import (
    update_mediafile_processing,
    MEDIA_STATUS_TRANSCRIBING,
    MEDIA_STATUS_TRANSCRIBED,
    MEDIA_STATUS_TRANSCRIPTION_FAILED,
)


def transcribe_mediafile(mediafile: dict):
    mediafile_id = mediafile["id"]
    local_path = mediafile.get("local_path")
    media_type = mediafile.get("media_content_type") or ""

    update_mediafile_processing(
        mediafile_id=mediafile_id,
        processing_status=MEDIA_STATUS_TRANSCRIBING,
        transcript_text=None,
        error_message=None
    )

    if not local_path:
        update_mediafile_processing(
            mediafile_id=mediafile_id,
            processing_status=MEDIA_STATUS_TRANSCRIPTION_FAILED,
            transcript_text=None,
            error_message="No local_path available for transcription"
        )
        return {
            "ok": False,
            "mediafile_id": mediafile_id,
            "error": "No local_path available for transcription"
        }

    if not media_type.startswith("audio/"):
        update_mediafile_processing(
            mediafile_id=mediafile_id,
            processing_status=MEDIA_STATUS_TRANSCRIPTION_FAILED,
            transcript_text=None,
            error_message="Media is not audio"
        )
        return {
            "ok": False,
            "mediafile_id": mediafile_id,
            "error": "Media is not audio"
        }

    transcript_text = "[stub] transcripción pendiente de motor real"

    update_mediafile_processing(
        mediafile_id=mediafile_id,
        processing_status=MEDIA_STATUS_TRANSCRIBED,
        transcript_text=transcript_text,
        error_message=None
    )

    return {
        "ok": True,
        "mediafile_id": mediafile_id,
        "transcript_text": transcript_text
    }

def transcribe_pending_mediafiles(mediafiles: list):
    results = []

    for mediafile in mediafiles:
        result = transcribe_mediafile(mediafile)
        results.append(result)

    return results


