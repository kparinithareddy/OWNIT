import io
import wave
import logging
from typing import Optional, Tuple
import speech_recognition as sr

logger = logging.getLogger(__name__)

class SpeechService:
    """
    Robust Speech-to-Text service utilizing python-speechrecognition.
    Handles WAV audio buffers with language localization (English, Hindi, Telugu).
    """

    def map_language_to_locale(self, lang: Optional[str]) -> str:
        if not lang:
            return "en-IN"
        lower = lang.lower().strip()
        if lower in ["hi", "hi-in"] or lower.startswith("hi"):
            return "hi-IN"
        if lower in ["te", "te-in"] or lower.startswith("te"):
            return "te-IN"
        if lower in ["en", "en-in", "en-us"] or lower.startswith("en"):
            return "en-IN"
        return lang

    def transcribe_wav_bytes(
        self,
        audio_bytes: bytes,
        language: Optional[str] = "en-IN"
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Transcribes WAV audio bytes into text.
        Returns (success, transcript, error_message).
        """
        if not audio_bytes or len(audio_bytes) < 200:
            return False, "", "Audio recording was too short. Please hold or click the mic and speak."

        target_locale = self.map_language_to_locale(language)
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 150
        recognizer.dynamic_energy_threshold = True

        try:
            audio_io = io.BytesIO(audio_bytes)
            with sr.AudioFile(audio_io) as source:
                audio_data = recognizer.record(source)

            if not audio_data or len(audio_data.frame_data) == 0:
                return False, "", "No audible sound detected. Please check your microphone volume."

            # Primary attempt in user's selected language
            try:
                transcript = recognizer.recognize_google(audio_data, language=target_locale)
                if transcript and transcript.strip():
                    return True, transcript.strip(), None
            except sr.UnknownValueError:
                # If user spoke English while in Hindi/Telugu mode, try English fallback
                if target_locale != "en-IN":
                    try:
                        transcript = recognizer.recognize_google(audio_data, language="en-IN")
                        if transcript and transcript.strip():
                            return True, transcript.strip(), None
                    except Exception:
                        pass
                logger.info(f"Speech recognition: could not understand audio in {target_locale}")
                return False, "", "Could not detect clear speech. Please speak clearly into your microphone."

            return False, "", "No speech detected."

        except sr.RequestError as e:
            logger.warning(f"Speech recognition service request error: {e}")
            # Fallback to English if regional recognition failed
            if target_locale != "en-IN":
                try:
                    audio_io = io.BytesIO(audio_bytes)
                    with sr.AudioFile(audio_io) as source:
                        audio_data = recognizer.record(source)
                    transcript = recognizer.recognize_google(audio_data, language="en-IN")
                    if transcript and transcript.strip():
                        return True, transcript.strip(), None
                except Exception:
                    pass
            return False, "", f"Speech recognition service connection error: {str(e)}"
        except Exception as e:
            logger.error(f"Speech transcription unexpected error: {e}", exc_info=True)
            return False, "", f"Transcription error: {str(e)}"

speech_service = SpeechService()
