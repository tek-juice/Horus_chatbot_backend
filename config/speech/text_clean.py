import re


def clean_text_for_speech(text):
    """
    Remove Markdown formatting and other characters
    that should not be spoken by the TTS engine.
    """

    # Remove bold: **text** -> text
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)

    # Remove italic: *text* -> text
    text = re.sub(r"\*(.*?)\*", r"\1", text)

    # Remove inline code: `text` -> text
    text = re.sub(r"`(.*?)`", r"\1", text)

    # Remove Markdown headings: ### Heading -> Heading
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

    # Remove Markdown bullet points
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)

    # Remove numbered list formatting: 1. Something -> Something
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)

    # Remove Markdown links but keep the visible text
    # [Horus](https://example.com) -> Horus
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Remove remaining Markdown emphasis characters
    text = text.replace("**", "")
    text = text.replace("__", "")

    # Clean excessive whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()