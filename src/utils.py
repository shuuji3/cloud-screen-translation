import html
import io
import os
import platform
import re
import subprocess

import wx.adv
import yaml
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

    # Filter small characters
    def _calc_height(word):
        """Calculate the height of the word boundary box."""
        ys = list(map(lambda v: v.y, word.bounding_box.vertices))
        return max(ys) - min(ys)

    texts = []
    max_height = 0
    for page in res.full_text_annotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                max_height = max(max_height, max(map(_calc_height, paragraph.words)))
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    if _calc_height(word) > max_height * 0.60:
                        texts.append(''.join([symbol.text for symbol in word.symbols]))
            texts.append('\n')

    return re.sub('\n+', '　', ' '.join(texts)).strip()


def translate(text: str, target_language: str = 'en', source_language: str = 'ja') -> str:
    """Translate text from PIL.Image data using Google Cloud Translate."""
    translation = translate_client.translate(
        replace_words(text),
        target_language=target_language,
        source_language=source_language,
    )
    translated_text = html.unescape(translation['translatedText']).strip()
    return translated_text


def replace_words(text: str) -> str:
    """Replace words in text by using the replace table."""

    with open('replace_table.yaml') as f:
        replace_table = yaml.load(f)

    for item in replace_table:
        text = re.sub(item['pattern'], item['replace'], text)

    return text


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
