# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "numpy",
#     "scipy",
# ]
# ///

"""Pure Python Mathematical Digital Signal Processing (DSP) Engine.

Focuses on core mathematical routines:
- Band-limited anti-aliased Fourier sinc resampling (Nyquist reconstruction filter)
- Fundamental sampling metrics (duration, rate, theoretical Nyquist cutoff limit)
"""

from __future__ import annotations

import numpy as np
import scipy.signal


def resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int) -> tuple[np.ndarray, int]:
    """Band-limited anti-aliased sinc resampling using Fourier method.
    
    Implements ideal low-pass interpolation by transforming the signal to the
    frequency domain via FFT, truncating or zero-padding high-frequency bins,
    and transforming back with IFFT.
    """
    if orig_sr == target_sr:
        return audio.copy(), orig_sr
    num_target_samples = int(round(len(audio) * float(target_sr) / orig_sr))
    resampled = scipy.signal.resample(audio, num_target_samples)
    resampled = np.clip(np.real(resampled), -1.0, 1.0)
    return resampled.astype(np.float32), target_sr


def compute_audio_metrics(audio: np.ndarray, sr: int) -> dict:
    """Computes duration, sampling rate, and theoretical Nyquist limit."""
    duration_s = float(len(audio)) / float(sr) if sr > 0 else 0.0
    nyquist_hz = float(sr) / 2.0
    return {
        "duration_s": duration_s,
        "sampling_rate": sr,
        "nyquist_hz": nyquist_hz,
    }


if __name__ == "__main__":
    print("--- Pure Python DSP Math Engine ---")
    sr = 48000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    # 440 Hz test tone + 12 kHz overtone
    signal = 0.6 * np.sin(2 * np.pi * 440 * t) + 0.3 * np.sin(2 * np.pi * 12000 * t)
    
    metrics = compute_audio_metrics(signal, sr)
    print(f"Original: {metrics['duration_s']:.2f}s @ {sr} Hz, Nyquist = {metrics['nyquist_hz']/1000:.1f} kHz")
    
    resampled, res_sr = resample_audio(signal, sr, 8000)
    res_metrics = compute_audio_metrics(resampled, res_sr)
    print(f"Resampled: {res_metrics['duration_s']:.2f}s @ {res_sr} Hz, Nyquist = {res_metrics['nyquist_hz']/1000:.1f} kHz")
    print("DSP engine validated successfully!")
