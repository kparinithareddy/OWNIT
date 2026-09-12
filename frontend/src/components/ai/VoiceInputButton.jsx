import React, { useState, useEffect } from 'react';
import { Mic, AlertCircle, RefreshCw } from 'lucide-react';
import { useLanguage } from '../../i18n/LanguageContext';
import useSpeechRecognition, { mapLanguageToLocale } from '../../hooks/useSpeechRecognition';
import './VoiceInputButton.css';

/**
 * VoiceInputButton component for speech-to-text input in chat interfaces.
 * Features dual-engine hybrid speech recognition with automatic fallback.
 * 
 * @param {Object} props
 * @param {Function} props.onSpeechRecognized - Callback invoked with final recognized text string
 * @param {Function} [props.onInterimChange] - Optional callback for live interim text
 * @param {boolean} [props.disabled=false] - Whether the button is disabled
 * @param {string} [props.size='md'] - 'sm' | 'md' | 'lg'
 * @param {string} [props.className=''] - Additional CSS classes
 */
export default function VoiceInputButton({
  onSpeechRecognized,
  onInterimChange,
  disabled = false,
  size = 'md',
  className = ''
}) {
  const { language, t } = useLanguage();
  const [feedbackMessage, setFeedbackMessage] = useState(null);

  const {
    isSupported,
    isListening,
    isProcessing,
    interimTranscript,
    error,
    startListening,
    stopListening
  } = useSpeechRecognition({
    language,
    continuous: false,
    interimResults: true,
    onResult: ({ finalTranscript, interimTranscript }) => {
      if (onInterimChange) {
        onInterimChange(interimTranscript);
      }
      if (finalTranscript && onSpeechRecognized) {
        onSpeechRecognized(finalTranscript);
      }
    },
    onError: (err) => {
      if (err) {
        setFeedbackMessage(err);
      }
    },
    onEnd: () => {
      if (onInterimChange) {
        onInterimChange('');
      }
    }
  });

  // Auto-clear feedback error message after 6 seconds
  useEffect(() => {
    if (feedbackMessage) {
      const timer = setTimeout(() => {
        setFeedbackMessage(null);
      }, 6000);
      return () => clearTimeout(timer);
    }
  }, [feedbackMessage]);

  const handleToggleListening = (e) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }

    if (disabled || isProcessing) return;

    if (!isSupported) {
      setFeedbackMessage(t('ai.voiceUnsupported', {}, 'Voice input is not supported in this browser. Please use Chrome, Edge, or Safari.'));
      return;
    }

    if (isListening) {
      stopListening();
    } else {
      setFeedbackMessage(null);
      startListening(language);
    }
  };

  const handleRetryClick = (e) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    setFeedbackMessage(null);
    startListening(language);
  };

  const getLanguageLabel = () => {
    if (language === 'hi') return 'हिंदी (hi-IN)';
    if (language === 'te') return 'తెలుగు (te-IN)';
    return 'English (en-IN)';
  };

  const buttonTitle = !isSupported
    ? t('ai.voiceUnsupported', {}, 'Speech recognition not supported in this browser')
    : isProcessing
    ? t('ai.voiceProcessing', {}, 'Transcribing audio...')
    : isListening
    ? `${t('ai.stopListening', {}, 'Click to finish speaking')} · ${getLanguageLabel()}`
    : `${t('ai.startListening', {}, 'Click to speak')} · ${getLanguageLabel()}`;

  return (
    <div className={`voice-input-container ${className}`}>
      <button
        type="button"
        className={`voice-input-btn voice-btn-${size} ${isListening ? 'listening' : ''} ${isProcessing ? 'processing' : ''} ${!isSupported ? 'unsupported' : ''}`}
        onClick={handleToggleListening}
        disabled={disabled || !isSupported || isProcessing}
        title={buttonTitle}
        aria-label={buttonTitle}
        aria-pressed={isListening}
      >
        {isListening ? (
          <>
            <span className="voice-pulse-ring" />
            <Mic className="voice-icon listening-icon" size={size === 'sm' ? 14 : size === 'lg' ? 20 : 16} />
          </>
        ) : isProcessing ? (
          <RefreshCw className="voice-icon processing-icon spinning" size={size === 'sm' ? 14 : size === 'lg' ? 20 : 16} />
        ) : (
          <Mic className="voice-icon" size={size === 'sm' ? 14 : size === 'lg' ? 20 : 16} />
        )}
      </button>

      {/* Live Listening Status Popover */}
      {isListening && !isProcessing && (
        <div className="voice-listening-popover" role="status" aria-live="polite">
          <span className="voice-wave-dot dot1" />
          <span className="voice-wave-dot dot2" />
          <span className="voice-wave-dot dot3" />
          <span className="voice-popover-text">
            {t('ai.listening', {}, 'Listening...')} ({getLanguageLabel()})
          </span>
          {interimTranscript && (
            <span className="voice-interim-preview">"{interimTranscript}"</span>
          )}
        </div>
      )}

      {/* Processing Server Transcription Popover */}
      {isProcessing && (
        <div className="voice-processing-popover" role="status" aria-live="polite">
          <RefreshCw size={13} className="spinning processing-spinner" />
          <span>{t('ai.voiceProcessing', {}, 'Transcribing audio...')}</span>
        </div>
      )}

      {/* Temporary Error Feedback Tooltip with Retry Action */}
      {feedbackMessage && !isListening && !isProcessing && (
        <div className="voice-error-popover" role="alert">
          <div className="voice-error-content">
            <AlertCircle size={14} className="voice-error-icon" />
            <span>{feedbackMessage}</span>
          </div>
          <div className="voice-error-actions">
            <button
              type="button"
              className="voice-retry-btn"
              onClick={handleRetryClick}
            >
              {t('ai.voiceRetry', {}, 'Retry')}
            </button>
            <button
              type="button"
              className="voice-dismiss-btn"
              onClick={() => setFeedbackMessage(null)}
              title="Dismiss"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
