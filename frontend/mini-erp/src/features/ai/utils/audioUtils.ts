/** Convert browser-recorded audio (e.g. webm) to 16 kHz mono WAV for FPT Whisper STT. */

const TARGET_SAMPLE_RATE = 16_000

function writeString(view: DataView, offset: number, str: string) {
  for (let i = 0; i < str.length; i++) {
    view.setUint8(offset + i, str.charCodeAt(i))
  }
}

function audioBufferToWav(buffer: AudioBuffer): ArrayBuffer {
  const numChannels = 1
  const sampleRate = buffer.sampleRate
  const format = 1
  const bitDepth = 16

  const samples = buffer.length
  const blockAlign = (numChannels * bitDepth) / 8
  const byteRate = sampleRate * blockAlign
  const dataSize = samples * blockAlign
  const bufferLength = 44 + dataSize
  const arrayBuffer = new ArrayBuffer(bufferLength)
  const view = new DataView(arrayBuffer)

  writeString(view, 0, "RIFF")
  view.setUint32(4, 36 + dataSize, true)
  writeString(view, 8, "WAVE")
  writeString(view, 12, "fmt ")
  view.setUint32(16, 16, true)
  view.setUint16(20, format, true)
  view.setUint16(22, numChannels, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, byteRate, true)
  view.setUint16(32, blockAlign, true)
  view.setUint16(34, bitDepth, true)
  writeString(view, 36, "data")
  view.setUint32(40, dataSize, true)

  const channel = buffer.getChannelData(0)
  let offset = 44
  for (let i = 0; i < samples; i++) {
    const sample = Math.max(-1, Math.min(1, channel[i]))
    view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true)
    offset += 2
  }
  return arrayBuffer
}

/** Resample to mono 16 kHz (FPT Cloud STT recommendation). */
async function resampleToMono16k(decoded: AudioBuffer): Promise<AudioBuffer> {
  const length = Math.max(1, Math.ceil(decoded.duration * TARGET_SAMPLE_RATE))
  const offline = new OfflineAudioContext(1, length, TARGET_SAMPLE_RATE)
  const mono = offline.createBuffer(1, decoded.length, decoded.sampleRate)
  const out = mono.getChannelData(0)
  out.fill(0)
  for (let ch = 0; ch < decoded.numberOfChannels; ch++) {
    const data = decoded.getChannelData(ch)
    for (let i = 0; i < decoded.length; i++) {
      out[i] += data[i] / decoded.numberOfChannels
    }
  }
  const source = offline.createBufferSource()
  source.buffer = mono
  source.connect(offline.destination)
  source.start(0)
  return offline.startRendering()
}

/** Peak amplitude 0..1 — detect silence before upload. */
export function peakAmplitude(buffer: AudioBuffer): number {
  let peak = 0
  for (let ch = 0; ch < buffer.numberOfChannels; ch++) {
    const data = buffer.getChannelData(ch)
    for (let i = 0; i < data.length; i++) {
      const v = Math.abs(data[i])
      if (v > peak) peak = v
    }
  }
  return peak
}

export async function convertToWav(blob: Blob): Promise<{ wav: Blob; durationSec: number; peak: number }> {
  const audioContext = new AudioContext()
  try {
    const arrayBuffer = await blob.arrayBuffer()
    const decoded = await audioContext.decodeAudioData(arrayBuffer.slice(0))
    const resampled = await resampleToMono16k(decoded)
    const peak = peakAmplitude(resampled)
    const wavBuffer = audioBufferToWav(resampled)
    return {
      wav: new Blob([wavBuffer], { type: "audio/wav" }),
      durationSec: resampled.duration,
      peak,
    }
  } finally {
    await audioContext.close()
  }
}

export const MAX_RECORDING_MS = 60_000
export const MIN_RECORDING_SEC = 0.8
export const MIN_PEAK_AMPLITUDE = 0.008
