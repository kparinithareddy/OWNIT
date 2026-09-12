/**
 * Lightweight in-browser Mono WAV Audio Recorder.
 * Records high-fidelity PCM audio and encodes to standard WAV.
 */

function writeString(view, offset, string) {
  for (let i = 0; i < string.length; i++) {
    view.setUint8(offset + i, string.charCodeAt(i));
  }
}

function encodeWAV(samples, sampleRate) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  /* RIFF identifier */
  writeString(view, 0, 'RIFF');
  /* file length */
  view.setUint32(4, 36 + samples.length * 2, true);
  /* RIFF type */
  writeString(view, 8, 'WAVE');
  /* format chunk identifier */
  writeString(view, 12, 'fmt ');
  /* format chunk length */
  view.setUint32(16, 16, true);
  /* sample format (1 = PCM) */
  view.setUint16(20, 1, true);
  /* channel count (1 = mono) */
  view.setUint16(22, 1, true);
  /* sample rate */
  view.setUint32(24, sampleRate, true);
  /* byte rate (sample rate * block align) */
  view.setUint32(28, sampleRate * 2, true);
  /* block align (channel count * bytes per sample) */
  view.setUint16(32, 2, true);
  /* bits per sample */
  view.setUint16(34, 16, true);
  /* data chunk identifier */
  writeString(view, 36, 'data');
  /* data chunk length */
  view.setUint32(40, samples.length * 2, true);

  // Write PCM 16-bit samples with gentle gain normalization
  let offset = 44;
  for (let i = 0; i < samples.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }

  return new Blob([view], { type: 'audio/wav' });
}

export class AudioStreamRecorder {
  constructor() {
    this.audioContext = null;
    this.mediaStream = null;
    this.processor = null;
    this.source = null;
    this.audioBuffers = [];
    this.isRecording = false;
    this.startTime = null;
  }

  async start() {
    if (this.isRecording) return;
    this.audioBuffers = [];
    this.startTime = Date.now();

    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) {
      throw new Error('AudioContext not supported in this browser.');
    }

    this.audioContext = new AudioContextClass();
    if (this.audioContext.state === 'suspended') {
      await this.audioContext.resume();
    }

    this.mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    });

    this.source = this.audioContext.createMediaStreamSource(this.mediaStream);
    // 4096 sample buffer size for smooth streaming
    this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);

    this.processor.onaudioprocess = (e) => {
      if (!this.isRecording) return;
      const inputData = e.inputBuffer.getChannelData(0);
      this.audioBuffers.push(new Float32Array(inputData));
    };

    this.source.connect(this.processor);
    this.processor.connect(this.audioContext.destination);
    this.isRecording = true;
  }

  getRecordingDurationMs() {
    if (!this.startTime) return 0;
    return Date.now() - this.startTime;
  }

  async stop() {
    this.isRecording = false;

    if (this.processor) {
      try {
        this.processor.disconnect();
      } catch {}
      this.processor = null;
    }

    if (this.source) {
      try {
        this.source.disconnect();
      } catch {}
      this.source = null;
    }

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((t) => t.stop());
      this.mediaStream = null;
    }

    const sampleRate = this.audioContext?.sampleRate || 44100;
    if (this.audioContext && this.audioContext.state !== 'closed') {
      try {
        await this.audioContext.close();
      } catch {}
      this.audioContext = null;
    }

    // Merge audio chunks
    let totalLength = 0;
    for (const chunk of this.audioBuffers) {
      totalLength += chunk.length;
    }

    if (totalLength === 0) {
      return null;
    }

    const merged = new Float32Array(totalLength);
    let offset = 0;
    for (const chunk of this.audioBuffers) {
      merged.set(chunk, offset);
      offset += chunk.length;
    }

    return encodeWAV(merged, sampleRate);
  }

  cancel() {
    this.isRecording = false;
    this.audioBuffers = [];
    if (this.processor) {
      try {
        this.processor.disconnect();
      } catch {}
      this.processor = null;
    }
    if (this.source) {
      try {
        this.source.disconnect();
      } catch {}
      this.source = null;
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((t) => t.stop());
      this.mediaStream = null;
    }
    if (this.audioContext && this.audioContext.state !== 'closed') {
      try {
        this.audioContext.close();
      } catch {}
      this.audioContext = null;
    }
  }
}
