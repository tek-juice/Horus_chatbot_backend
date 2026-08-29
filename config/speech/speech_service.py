from faster_whisper import WhisperModel
from kokoro import KPipeline
import time
import logging
import numpy as np

from config.speech.text_clean import clean_text_for_speech


logger = logging.getLogger(__name__)

logger.info("[VOICE] Loading Faster-Whisper model...")

whisper_model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8"
)

logger.info(
    "[VOICE] Faster-Whisper loaded successfully."
)


def speech_to_text(audio_path):

    start_time = time.perf_counter()

    logger.info("[VOICE] Starting speech-to-text")

    segments, info = whisper_model.transcribe(
        audio_path,
        beam_size=1
    )

    text = ""

    for segment in segments:
        text += segment.text

    elapsed = time.perf_counter() - start_time

    logger.info(
        "[VOICE] STT time: %.2fs",
        elapsed
    )

    logger.info(
        "[VOICE] Transcription: %s",
        text.strip()
    )

    return text.strip()

KOKORO_VOICE = "af_heart"

logger.info("[VOICE] Loading Kokoro model...")

kokoro_start = time.perf_counter()

kokoro_pipeline = KPipeline(
    lang_code="a",
    repo_id="hexgrad/Kokoro-82M"
)

logger.info(
    "[VOICE] Kokoro pipeline loaded. "
    "Warming voice=%s",
    KOKORO_VOICE
)


try:
    voice_start = time.perf_counter()
    kokoro_pipeline.load_voice(
        KOKORO_VOICE
    )

    voice_elapsed = time.perf_counter() - voice_start

    logger.info(
        "[VOICE] Kokoro voice warmed successfully. "
        "Voice=%s Time=%.2fs",
        KOKORO_VOICE,
        voice_elapsed
    )

except Exception:

    logger.exception(
        "[VOICE] Failed to warm Kokoro voice=%s",
        KOKORO_VOICE
    )

    raise


kokoro_elapsed = time.perf_counter() - kokoro_start

logger.info(
    "[VOICE] Kokoro ready. Total startup time=%.2fs",
    kokoro_elapsed
)


def text_to_speech_stream(text):
    """
    Convert a text chunk into PCM16 audio chunks.

    Yields raw PCM audio bytes as Kokoro generates them.
    """

    start_time = time.perf_counter()

    logger.info(
        "[VOICE] Starting streaming TTS. Characters=%d",
        len(text)
    )

    text = clean_text_for_speech(text)

    if not text.strip():

        logger.warning(
            "[VOICE] TTS received empty text after cleaning."
        )

        return

    logger.info(
        "[VOICE] Streaming TTS text after cleaning. Characters=%d",
        len(text)
    )

    generator = kokoro_pipeline(
        text,
        voice=KOKORO_VOICE
    )

    chunk_count = 0

    for _, _, audio in generator:

        chunk_count += 1

        # Kokoro returns a NumPy floating-point
        # audio array in the range [-1, 1].
        audio = np.asarray(audio)

        audio = np.clip(
            audio,
            -1.0,
            1.0
        )

        # Convert float32 audio → signed 16-bit PCM.
        pcm16 = (
            audio * 32767
        ).astype(
            np.int16
        )

        audio_bytes = pcm16.tobytes()

        if audio_bytes:

            logger.debug(
                "[VOICE] TTS audio chunk=%d bytes=%d",
                chunk_count,
                len(audio_bytes)
            )

            yield audio_bytes

    elapsed = time.perf_counter() - start_time

    logger.info(
        "[VOICE] Streaming TTS complete. "
        "Chunks=%d Time=%.2fs",
        chunk_count,
        elapsed
    )

