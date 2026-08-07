from faster_whisper import WhisperModel
from gtts import gTTS
import tempfile


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


def text_to_speech(text):

    output = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".mp3"
    )

    output.close()

    tts = gTTS(
        text=text,
        lang="en",
        tld="co.uk",
        slow=False
    )

    tts.save(output.name)

    return output.name