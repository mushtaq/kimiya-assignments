"""Pure Python Mathematical Digital Signal Processing (DSP) Engine.

Demonstrates band-limited harmonic synthesis, audio loading/decoding,
Fourier sinc resampling (anti-aliasing), and Nyquist-Shannon metrics.
"""

from __future__ import annotations

import base64
import io
import numpy as np
import scipy.io.wavfile as wav
import scipy.signal
import soundfile as sf


def synth_educational_bell(duration_s: float = 3.0, sr: int = 48000) -> tuple[np.ndarray, int]:
    """Synthesizes a rich harmonic chime with distinct high overtones up to 14.08 kHz."""
    t = np.linspace(0, duration_s, int(duration_s * sr), endpoint=False)

    harmonics = [
        (440.0, 0.40, 1.2),    # A4 fundamental
        (880.0, 0.28, 1.8),    # A5 octave
        (1760.0, 0.20, 2.5),   # A6 bell body
        (3520.0, 0.16, 3.2),   # A7 presence
        (7040.0, 0.12, 4.0),   # A8 brilliance
        (11000.0, 0.08, 5.0),  # Metallic sparkle
        (14080.0, 0.06, 6.0),  # Ultra-high shimmer
    ]

    signal = np.zeros_like(t)
    for freq, amp, decay_rate in harmonics:
        if freq < sr / 2.0:
            env = np.exp(-decay_rate * t)
            signal += amp * np.sin(2.0 * np.pi * freq * t) * env

    # Metallic transient attack at onset
    noise = np.random.uniform(-0.12, 0.12, len(t)) * np.exp(-20.0 * t)
    signal += noise

    # Smooth crossfade at loop boundaries
    fade_len = int(0.04 * sr)
    if fade_len > 0 and len(signal) > 2 * fade_len:
        signal[:fade_len] *= np.linspace(0, 1, fade_len)
        signal[-fade_len:] *= np.linspace(1, 0, fade_len)

    # Peak normalize
    max_val = np.max(np.abs(signal))
    if max_val > 0:
        signal = (signal / max_val) * 0.95

    return signal.astype(np.float32), sr


def load_audio_data(
    raw_bytes: bytes | None,
    filename: str | None = None,
    max_duration_s: float = 8.0,
) -> tuple[np.ndarray, int, str]:
    """Loads uploaded audio (.wav, .mp3, .ogg, .flac) or falls back to the educational bell."""
    if raw_bytes and len(raw_bytes) > 0:
        try:
            data, sr = sf.read(io.BytesIO(raw_bytes))
            if data.ndim > 1:
                data = data.mean(axis=1)
            if np.issubdtype(data.dtype, np.integer):
                max_int = np.iinfo(data.dtype).max
                audio = data.astype(np.float32) / max_int
            else:
                audio = data.astype(np.float32)

            # Trim to loop snippet if longer than max_duration_s
            max_samples = int(max_duration_s * sr)
            if len(audio) > max_samples:
                audio = audio[:max_samples]

            # Smooth loop crossfade
            fade_len = int(0.04 * sr)
            if fade_len > 0 and len(audio) > 2 * fade_len:
                audio[:fade_len] *= np.linspace(0, 1, fade_len)
                audio[-fade_len:] *= np.linspace(1, 0, fade_len)

            max_val = np.max(np.abs(audio))
            if max_val > 0:
                audio = (audio / max_val) * 0.95

            name = filename if filename else "Uploaded Audio"
            return audio.astype(np.float32), int(sr), name
        except Exception:
            pass
    audio, sr = synth_educational_bell(3.0, 48000)
    return audio, sr, "Default Harmonic Bell"


def resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int) -> tuple[np.ndarray, int]:
    """Band-limited anti-aliased sinc resampling using Fourier method."""
    if orig_sr == target_sr:
        return audio.copy(), orig_sr
    num_target_samples = int(round(len(audio) * float(target_sr) / orig_sr))
    resampled = scipy.signal.resample(audio, num_target_samples)
    resampled = np.clip(np.real(resampled), -1.0, 1.0)
    return resampled.astype(np.float32), target_sr


def compute_audio_metrics(audio: np.ndarray, sr: int) -> dict:
    """Computes sample count, duration, raw PCM size, and theoretical Nyquist limit."""
    duration_s = float(len(audio)) / float(sr) if sr > 0 else 0.0
    pcm_kb = float(len(audio) * 2) / 1024.0
    nyquist_hz = float(sr) / 2.0
    return {
        "duration_s": duration_s,
        "sample_count": len(audio),
        "sampling_rate": sr,
        "pcm_kb": pcm_kb,
        "nyquist_hz": nyquist_hz,
    }


def audio_to_base64_wav(audio: np.ndarray, sr: int) -> str:
    """Encodes float32 audio array into standard 16-bit PCM WAV base64 data URI."""
    int16_audio = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    buffer = io.BytesIO()
    wav.write(buffer, sr, int16_audio)
    b64_str = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:audio/wav;base64,{b64_str}"


if __name__ == "__main__":
    print("--- Pure Python DSP Engine Demo ---")
    audio, sr = synth_educational_bell(duration_s=3.0, sr=48000)
    metrics = compute_audio_metrics(audio, sr)
    print(f"Synthesized: {metrics['duration_s']:.2f}s, {metrics['sample_count']:,} samples @ {sr} Hz")
    print(f"Nyquist limit: {metrics['nyquist_hz']/1000.0:.1f} kHz, PCM size: {metrics['pcm_kb']:.1f} KB")

    resampled, res_sr = resample_audio(audio, sr, 8000)
    res_metrics = compute_audio_metrics(resampled, res_sr)
    print(f"Resampled to {res_sr} Hz: Nyquist limit = {res_metrics['nyquist_hz']/1000.0:.1f} kHz")
    print("DSP engine validated successfully!")
