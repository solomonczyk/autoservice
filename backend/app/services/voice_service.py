import os
import logging
import speech_recognition as sr
from pydub import AudioSegment
from io import BytesIO
from aiogram.types import Voice
from aiogram import Bot

logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    async def transcribe_voice(self, bot: Bot, voice: Voice) -> str:
        """
        Downloads voice message, converts to WAV, and transcribes to text.
        """
        try:
            # 1. Download file
            file = await bot.get_file(voice.file_id)
            file_path = file.file_path
            
            # Download into memory
            voice_file = await bot.download_file(file_path)
            
            # 2. Convert OGG to WAV (SpeechRecognition needs WAV)
            # pydub requires ffmpeg/avconv to be installed on the system
            ogg_audio = AudioSegment.from_ogg(voice_file)
            wav_io = BytesIO()
            ogg_audio.export(wav_io, format="wav")
            wav_io.seek(0)

            # 3. Transcribe
            with sr.AudioFile(wav_io) as source:
                # listen for the data (load audio to memory)
                audio_data = self.recognizer.record(source)
                # recognize (using Google Speech Recognition)
                # language='ru-RU' for Russian
                text = self.recognizer.recognize_google(audio_data, language="ru-RU")
                
                return text

        except sr.UnknownValueError:
            logger.warning("Speech Recognition could not understand audio")
            return ""
        except sr.RequestError as e:
            logger.error(f"Could not request results from Speech Recognition service; {e}")
            return ""
        except Exception as e:
            logger.error(f"Error processing voice message: {e}")
            return ""

voice_service = VoiceService()
