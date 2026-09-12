import { useState, useEffect, useRef, useCallback } from 'react';
import { AudioStreamRecorder } from '../utils/audioRecorder';
import { aiApi } from '../services/api';

/**
 * Returns an ordered cascade of BCP 47 locale subtags to try for a given language.
 */
export function getLocaleFallbackChain(lang) {
  if (!lang) return ['en-IN', 'en-US', 'en'];
  const lower = lang.toLowerCase().trim();

  if (lower === 'hi' || lower.startsWith('hi-')) {
    return ['hi-IN', 'hi', 'en-IN', 'en-US'];
  }
  if (lower === 'te' || lower.startsWith('te-')) {
    return ['te-IN', 'te', 'en-IN', 'en-US'];
  }
  if (lower === 'en' || lower.startsWith('en-')) {
    return ['en-IN', 'en-US', 'en-GB', 'en'];
  }
  return [lang, 'en-IN', 'en-US', 'en'];
}

export function mapLanguageToLocale(lang) {
  const chain = getLocaleFallbackChain(lang);
  return chain[0] || 'en-IN';
}

/**
 * Dual-Engine Hybrid Speech Recognition Hook.
 * - Engine 1: Fast Browser Web Speech API (streaming real-time results if available).
 * - Engine 2: Zero-failure Server Audio Bridge (captures voice without dropping, transcribes on stop).
 */
export default function useSpeechRecognition({
  language = 'en',
  continuous = false,
  interimResults = true,
  onResult,
  onError,
  onEnd
} = {}) {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [error, setError] = useState(null);
  const [errorCode, setErrorCode] = useState(null);

  const recognitionRef = useRef(null);
  const audioRecorderRef = useRef(null);
  const autoStopTimeoutRef = useRef(null);
  const manualStopRef = useRef(false);
  const recognizedAnyTextRef = useRef(false);
  const activeLanguageRef = useRef(language);

  const onResultRef = useRef(onResult);
  const onErrorRef = useRef(onError);
  const onEndRef = useRef(onEnd);

  useEffect(() => {
    onResultRef.current = onResult;
  }, [onResult]);

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  useEffect(() => {
    onEndRef.current = onEnd;
  }, [onEnd]);

  useEffect(() => {
    activeLanguageRef.current = language;
  }, [language]);

  const isSupported = typeof window !== 'undefined' && Boolean(
    window.SpeechRecognition ||
    window.webkitSpeechRecognition ||
    (navigator.mediaDevices && navigator.mediaDevices.getUserMedia)
  );

  useEffect(() => {
    return () => {
      if (autoStopTimeoutRef.current) {
        clearTimeout(autoStopTimeoutRef.current);
      }
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {}
        recognitionRef.current = null;
      }
      if (audioRecorderRef.current) {
        audioRecorderRef.current.cancel();
        audioRecorderRef.current = null;
      }
    };
  }, []);

  const getFriendlyErrorMessage = (code, lang = activeLanguageRef.current) => {
    const isHi = lang === 'hi' || lang?.startsWith('hi-');
    const isTe = lang === 'te' || lang?.startsWith('te-');

    switch (code) {
      case 'not-allowed':
      case 'permission-denied':
        if (isHi) return 'माइक्रोफ़ोन अनुमति अस्वीकृत। कृपया ब्राउज़र में माइक्रोफ़ोन की अनुमति दें।';
        if (isTe) return 'మైక్రోఫోన్ అనుమతి నిరాకరించబడింది. దయచేసి బ్రౌజర్‌లో మైక్రోఫోన్ అనుమతించండి.';
        return 'Microphone access denied. Please allow microphone permissions in your browser.';
      case 'no-speech':
        if (isHi) return 'कोई आवाज़ नहीं सुनी गई। कृपया पुनः बोलें।';
        if (isTe) return 'శబ్దం వినబడలేదు. దయచేసి మళ్లీ మాట్లాడండి.';
        return 'No speech detected. Please speak clearly into your microphone.';
      case 'audio-capture':
        if (isHi) return 'कोई माइक्रोफ़ोन नहीं मिला या ऑडियो कैप्चर विफल रहा।';
        if (isTe) return 'మైక్రోఫోన్ కనుగొనబడలేదు లేదా ఆడియో క్యాప్చర్ విఫలమైంది.';
        return 'No microphone found or audio capture failed.';
      case 'offline':
        if (isHi) return 'आप ऑफ़लाइन हैं। वाक् पहचान के लिए इंटरनेट कनेक्शन आवश्यक है।';
        if (isTe) return 'మీరు ఆఫ్‌లైన్‌లో ఉన్నారు. స్పీచ్ రికగ్నిషన్ కోసం ఇంటర్నెట్ అవసరం.';
        return 'You are offline. Voice recognition requires an active internet connection.';
      default:
        return isHi ? `वाक् पहचान त्रुटि: ${code}` : isTe ? `స్పీచ్ రికగ్నిషన్ లోపం: ${code}` : `Speech recognition error: ${code}`;
    }
  };

  /**
   * Process and transcribe the recorded audio buffer via backend speech service.
   */
  const processRecordedAudio = useCallback(async (targetLang) => {
    if (!audioRecorderRef.current) {
      setIsListening(false);
      setIsProcessing(false);
      return;
    }

    try {
      setIsProcessing(true);
      const recorder = audioRecorderRef.current;
      audioRecorderRef.current = null;
      const wavBlob = await recorder.stop();

      if (!wavBlob || wavBlob.size < 600) {
        setIsListening(false);
        setIsProcessing(false);
        return;
      }

      const localeTag = mapLanguageToLocale(targetLang);
      const res = await aiApi.transcribeSpeech(wavBlob, localeTag);

      if (res && res.success && res.transcript) {
        const text = res.transcript.trim();
        setTranscript((prev) => (prev ? `${prev} ${text}` : text));
        recognizedAnyTextRef.current = true;
        setError(null);
        setErrorCode(null);

        if (onResultRef.current) {
          onResultRef.current({
            finalTranscript: text,
            interimTranscript: '',
            isFinal: true
          });
        }
      } else if (res && res.error && !recognizedAnyTextRef.current) {
        const fallbackMsg = res.error;
        setError(fallbackMsg);
        if (onErrorRef.current) onErrorRef.current(fallbackMsg, 'server_transcribe_error');
      }
    } catch (err) {
      console.warn('[Speech] Server audio fallback notice:', err);
      if (!recognizedAnyTextRef.current) {
        const friendlyMsg = getFriendlyErrorMessage('network', targetLang);
        setError(friendlyMsg);
        if (onErrorRef.current) onErrorRef.current(friendlyMsg, 'network');
      }
    } finally {
      setIsListening(false);
      setIsProcessing(false);
      setInterimTranscript('');
      if (onEndRef.current) onEndRef.current();
    }
  }, []);

  const stopListening = useCallback(async () => {
    manualStopRef.current = true;
    if (autoStopTimeoutRef.current) {
      clearTimeout(autoStopTimeoutRef.current);
      autoStopTimeoutRef.current = null;
    }

    // Stop native recognition
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {}
    }

    // Transcribe recorded audio buffer if native speech hasn't already provided final transcript
    if (audioRecorderRef.current) {
      if (!recognizedAnyTextRef.current) {
        await processRecordedAudio(activeLanguageRef.current);
      } else {
        audioRecorderRef.current.cancel();
        audioRecorderRef.current = null;
        setIsListening(false);
        setIsProcessing(false);
        setInterimTranscript('');
      }
    } else {
      setIsListening(false);
      setIsProcessing(false);
      setInterimTranscript('');
    }
  }, [processRecordedAudio]);

  const startListening = useCallback(async (overrideLang) => {
    const targetLang = overrideLang || activeLanguageRef.current || 'en';
    activeLanguageRef.current = targetLang;
    manualStopRef.current = false;
    recognizedAnyTextRef.current = false;

    setError(null);
    setErrorCode(null);
    setInterimTranscript('');

    if (autoStopTimeoutRef.current) {
      clearTimeout(autoStopTimeoutRef.current);
      autoStopTimeoutRef.current = null;
    }

    // Check offline status
    if (typeof navigator !== 'undefined' && navigator.onLine === false) {
      const offlineMsg = getFriendlyErrorMessage('offline', targetLang);
      setError(offlineMsg);
      setErrorCode('offline');
      if (onErrorRef.current) onErrorRef.current(offlineMsg, 'offline');
      return;
    }

    // Clean up any existing instances
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch {}
      recognitionRef.current = null;
    }
    if (audioRecorderRef.current) {
      audioRecorderRef.current.cancel();
      audioRecorderRef.current = null;
    }

    // 1. Start High-Fidelity Audio Stream Recorder FIRST
    try {
      const recorder = new AudioStreamRecorder();
      await recorder.start();
      audioRecorderRef.current = recorder;
    } catch (recorderErr) {
      console.warn('[Speech] Audio recorder initialization:', recorderErr);
      if (recorderErr.name === 'NotAllowedError' || recorderErr.name === 'PermissionDeniedError') {
        const permMsg = getFriendlyErrorMessage('not-allowed', targetLang);
        setError(permMsg);
        setErrorCode('not-allowed');
        if (onErrorRef.current) onErrorRef.current(permMsg, 'not-allowed');
        return;
      }
    }

    setIsListening(true);

    // 2. Set comfortable 12-second max recording auto-stop timeout
    autoStopTimeoutRef.current = setTimeout(() => {
      if (!manualStopRef.current && audioRecorderRef.current) {
        stopListening();
      }
    }, 12000);

    // 3. Concurrently start Browser-Native Web Speech API for fast streaming
    const SpeechRecognitionClass = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognitionClass) {
      try {
        const recognition = new SpeechRecognitionClass();
        const activeLocale = mapLanguageToLocale(targetLang);

        recognition.lang = activeLocale;
        recognition.continuous = continuous;
        recognition.interimResults = interimResults;
        recognition.maxAlternatives = 1;

        recognition.onresult = (event) => {
          let finalStr = '';
          let interimStr = '';

          for (let i = event.resultIndex; i < event.results.length; ++i) {
            const res = event.results[i];
            const transcriptPiece = res[0]?.transcript || '';
            if (res.isFinal) {
              finalStr += transcriptPiece;
            } else {
              interimStr += transcriptPiece;
            }
          }

          if (finalStr) {
            recognizedAnyTextRef.current = true;
            setTranscript((prev) => (prev ? `${prev} ${finalStr.trim()}` : finalStr.trim()));
          }
          setInterimTranscript(interimStr);

          if (onResultRef.current) {
            onResultRef.current({
              finalTranscript: finalStr.trim(),
              interimTranscript: interimStr,
              isFinal: Boolean(finalStr && !interimStr)
            });
          }
        };

        recognition.onerror = (event) => {
          const code = event.error;
          // Log native speech status without interrupting active audio recording
          console.info(`[SpeechRecognition] Native status: ${code} (Audio recorder is actively capturing speech)`);
        };

        recognition.onend = () => {
          // If native recognition ends but audio is still recording, keep listening until user stops
          if (!isProcessing && !audioRecorderRef.current) {
            setIsListening(false);
            setInterimTranscript('');
          }
        };

        recognitionRef.current = recognition;
        recognition.start();
      } catch (err) {
        console.info('[Speech] Native recognition start notice:', err);
      }
    }
  }, [continuous, interimResults, stopListening]);

  const resetTranscript = useCallback(() => {
    manualStopRef.current = true;
    if (autoStopTimeoutRef.current) {
      clearTimeout(autoStopTimeoutRef.current);
      autoStopTimeoutRef.current = null;
    }
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch {}
      recognitionRef.current = null;
    }
    if (audioRecorderRef.current) {
      audioRecorderRef.current.cancel();
      audioRecorderRef.current = null;
    }
    setTranscript('');
    setInterimTranscript('');
    setError(null);
    setErrorCode(null);
    setIsListening(false);
    setIsProcessing(false);
  }, []);

  return {
    isSupported,
    isListening,
    isProcessing,
    transcript,
    interimTranscript,
    error,
    errorCode,
    startListening,
    stopListening,
    resetTranscript
  };
}
