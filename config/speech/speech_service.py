from faster_whisper import WhisperModel
from kokoro import KPipeline
import tempfile
import soundfile as sf
from config.speech.text_clean import clean_text_for_speech  

whisper_model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8"
)


def speech_to_text(audio_path):

    segments, info = whisper_model.transcribe(
        audio_path,
        beam_size=5
    )

    text = ""

    for segment in segments:
        text += segment.text

    return text.strip()


kokoro_pipeline = KPipeline(
    lang_code="a"
)

KOKORO_VOICE = "af_heart"


def text_to_speech(text):

    text = clean_text_for_speech(text)

    output = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".wav"
    )

    output.close()

    generator = kokoro_pipeline(
        text,
        voice=KOKORO_VOICE
    )

    with sf.SoundFile(
        output.name,
        mode="w",
        samplerate=24000,
        channels=1,
        subtype="PCM_16"
    ) as wav_file:

        for _, _, audio in generator:
            wav_file.write(audio)

    return output.name