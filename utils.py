import html
import io
import os
import platform
import subprocess

import wx.adv
from PIL.Image import Image
from google.cloud import texttospeech
from google.cloud.translate import Client as TranslateClient
from google.cloud.vision import ImageAnnotatorClient
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file('service_account_creds.json')
translate_client = TranslateClient(credentials=credentials)
vision_client = ImageAnnotatorClient(credentials=credentials)
text_to_speech_client = texttospeech.TextToSpeechClient(credentials=credentials)


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


def speech(text: str, langage_code: str = 'ja-JP') -> None:
    """Speak the text by Google Cloud Text-to-Speech voice synthesis."""

    # Create synthesis voice data
    temp_file = 'tmp.mp3'
    synthesis_input = texttospeech.types.SynthesisInput(text=text)
    voice = texttospeech.types.VoiceSelectionParams(
        language_code=langage_code,
        ssml_gender=texttospeech.enums.SsmlVoiceGender.FEMALE,
    )
    audio_config = texttospeech.types.AudioConfig(audio_encoding=texttospeech.enums.AudioEncoding.MP3)
    response = text_to_speech_client.synthesize_speech(synthesis_input, voice, audio_config)
    with open(temp_file, 'wb') as f:
        f.write(response.audio_content)

    # Play sound
    system = platform.system()
    if system == 'Windows':
        cmd = 'cmdmp3 {}'.format(temp_file)
        subprocess.call(cmd)
    else:
        wx.adv.Sound.PlaySound(temp_file, flags=wx.adv.SOUND_SYNC)

    # Windows has a problem in making temp files
    # ref: https://github.com/bravoserver/bravo/issues/111
    try:
        os.unlink(temp_file)
    except FileNotFoundError:
        pass
