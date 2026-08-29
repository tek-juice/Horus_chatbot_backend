from models.users import ChatSession, ChatMessage, MessageRole
from config.extensions.database_config import db
from config.model_engine.model_streamer import stream_answer

import logging
import time
import re

from config.speech.speech_service import text_to_speech_stream


logger = logging.getLogger(__name__)

def get_chat_session(session_uuid):

    return ChatSession.query.filter_by(
        chat_id=session_uuid
    ).first()


def should_flush_buffer(buffer):
    """
    Decide when enough text has accumulated
    to send to TTS.
    """

    text = buffer.strip()

    if not text:
        return False

    # Avoid tiny TTS requests
    if len(text) < 40:
        return False

    # Natural sentence endings
    if re.search(r"[.!?]\s*$", text):
        return True

    # New paragraph
    if text.endswith("\n"):
        return True

    # Prevent excessively large buffers
    if len(text) >= 180:
        return True

    return False


def generate_voice_answer(session_uuid, question):

    start_time = time.perf_counter()

    logger.info(
        "[VOICE] Starting streaming voice answer. Session=%s",
        session_uuid
    )

    session = get_chat_session(session_uuid)

    if session is None:

        logger.error(
            "[VOICE] Invalid session: %s",
            session_uuid
        )

        raise Exception("Invalid session")

    try:
        db_start = time.perf_counter()

        user_message = ChatMessage(
            session_id=session.id,
            role=MessageRole.USER,
            message=question
        )

        db.session.add(user_message)
        db.session.commit()

        logger.info(
            "[VOICE] User DB save: %.2fs",
            time.perf_counter() - db_start
        )

        llm_start = time.perf_counter()

        first_token_time = None
        first_audio_time = None

        complete_answer = ""
        text_buffer = ""

        logger.info(
            "[VOICE] Starting LLM stream"
        )

        for token in stream_answer(
            session_uuid,
            question
        ):

            if first_token_time is None:

                first_token_time = (
                    time.perf_counter() - llm_start
                )

                logger.info(
                    "[VOICE] LLM first token: %.2fs",
                    first_token_time
                )


            complete_answer += token

            text_buffer += token

            if should_flush_buffer(text_buffer):

                speech_text = text_buffer.strip()

                text_buffer = ""

                logger.info(
                    "[VOICE] Sending text chunk to TTS. "
                    "Characters=%d",
                    len(speech_text)
                )

                for audio_chunk in text_to_speech_stream(
                    speech_text
                ):

                    if first_audio_time is None:

                        first_audio_time = (
                            time.perf_counter() - start_time
                        )

                        logger.info(
                            "[VOICE] FIRST AUDIO: %.2fs",
                            first_audio_time
                        )

                    yield audio_chunk

        if text_buffer.strip():

            speech_text = text_buffer.strip()

            logger.info(
                "[VOICE] Processing final TTS buffer. "
                "Characters=%d",
                len(speech_text)
            )

            for audio_chunk in text_to_speech_stream(
                speech_text
            ):

                if first_audio_time is None:

                    first_audio_time = (
                        time.perf_counter() - start_time
                    )

                    logger.info(
                        "[VOICE] FIRST AUDIO: %.2fs",
                        first_audio_time
                    )

                yield audio_chunk

        llm_time = time.perf_counter() - llm_start

        logger.info(
            "[VOICE] LLM complete: %.2fs",
            llm_time
        )

        logger.info(
            "[VOICE] Complete answer length: %d characters",
            len(complete_answer)
        )

        if complete_answer.strip():

            db_start = time.perf_counter()

            assistant_message = ChatMessage(
                session_id=session.id,
                role=MessageRole.ASSISTANT,
                message=complete_answer
            )

            db.session.add(assistant_message)
            db.session.commit()

            logger.info(
                "[VOICE] Assistant DB save: %.2fs",
                time.perf_counter() - db_start
            )

        total_time = time.perf_counter() - start_time

        logger.info(
            "[VOICE] Streaming voice answer complete: %.2fs",
            total_time
        )

        if first_audio_time is not None:

            logger.info(
                "[VOICE] Time to first audio: %.2fs",
                first_audio_time
            )

    except GeneratorExit:

        logger.warning(
            "[VOICE] Client disconnected during voice stream"
        )

        raise

    except Exception:

        logger.exception(
            "[VOICE] Error generating streaming voice answer"
        )

        db.session.rollback()

        raise