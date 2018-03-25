import html
import io
import tempfile

import wx.adv
from PIL.Image import Image
from google.cloud.translate import Client as TranslateClient
from google.cloud.vision import ImageAnnotatorClient
from google.oauth2 import service_account
from gtts import gTTS

credentials = service_account.Credentials.from_service_account_file('service_account_creds.json')
translate_client = TranslateClient(credentials=credentials)
vision_client = ImageAnnotatorClient(credentials=credentials)


def text_detection(image: Image) -> str:
    """Detect text from PIL.Image data using Google Cloud Translate."""
    # Create bytestream of the given image
    bytes_io = io.BytesIO()
    image.save(bytes_io, 'png')
    bytes_io.seek(0)
    content = bytes_io.read()
    bytes_io.close()

    res = vision_client.text_detection({
        'content': content,
    })
    return res.full_text_annotation.text


def translate(text: str, target_language: str = 'en', source_language: str = 'ja') -> str:
    """Translate text from PIL.Image data using Google Cloud Translate."""
    translation = translate_client.translate(text, target_language=target_language, source_language=source_language)
    return html.unescape(translation['translatedText'])


def speak(text: str, lang: str = 'ja') -> None:
    """Speek the text by Google text-to-speech voice synthesis."""

    with tempfile.NamedTemporaryFile() as f:
        # Create synthesis voice data
        voice = gTTS(text=text, lang=lang)
        voice.save(f.name)

        # Play sound
        wx.adv.Sound.PlaySound(f.name, flags=wx.adv.SOUND_SYNC)
