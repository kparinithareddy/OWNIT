import pytest
import io
import wave
import struct
import math
from app.services.speech_service import speech_service

def create_synthetic_wav():
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        frames = bytearray()
        for i in range(16000):
            val = int(500 * math.sin(2 * math.pi * 440 * (i / 16000)))
            frames.extend(struct.pack('<h', val))
        wav_file.writeframes(frames)
    buf.seek(0)
    return buf.read()

def test_speech_service_language_mapping():
    assert speech_service.map_language_to_locale("en") == "en-IN"
    assert speech_service.map_language_to_locale("hi") == "hi-IN"
    assert speech_service.map_language_to_locale("te") == "te-IN"
    assert speech_service.map_language_to_locale("te-IN") == "te-IN"
    assert speech_service.map_language_to_locale(None) == "en-IN"

def test_speech_service_empty_audio():
    success, transcript, err = speech_service.transcribe_wav_bytes(b"", "en-IN")
    assert success is False
    assert err is not None
    assert len(err) > 0

def test_speech_service_synthetic_wav():
    wav_bytes = create_synthetic_wav()
    success, transcript, err = speech_service.transcribe_wav_bytes(wav_bytes, "en-IN")
    assert isinstance(success, bool)
    assert isinstance(transcript, str)
