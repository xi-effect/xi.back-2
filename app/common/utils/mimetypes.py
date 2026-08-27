import mimetypes

from app.common.filetype_ext import SUPPORTED_AUDIO_FORMATS

SUPPORTED_AUDIO_MIME_TYPES: dict[str, str] = {
    # taken from https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Containers
    "audio/aac": ".aac",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/mp4": ".m4a",
    "audio/ogg": ".ogg",
    "audio/flac": ".flac",
    "audio/x-flac": ".flac",
    "audio/wave": ".wav",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/x-pn-wav": ".wav",
}


def add_missing_mime_to_mimetypes() -> None:
    for audio_format in SUPPORTED_AUDIO_FORMATS:
        if mimetypes.guess_extension(audio_format.mime) is None:
            mimetypes.add_type(audio_format.mime, f".{audio_format.extension}")

    for mime, extension in SUPPORTED_AUDIO_MIME_TYPES.items():
        if mimetypes.guess_extension(mime) is None:
            mimetypes.add_type(mime, extension)
