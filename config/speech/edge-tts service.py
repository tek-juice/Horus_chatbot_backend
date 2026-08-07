from piper.voice import PiperVoice
import tempfile
import wave


tts_voice = PiperVoice.load(
    "models/piper/en_US-lessac-medium.onnx"
)


def text_to_speech(text):

    output = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".wav"
    )


    with wave.open(output.name, "wb") as wav_file:

        tts_voice.synthesize_wav(
            text,
            wav_file
        )


    return output.name