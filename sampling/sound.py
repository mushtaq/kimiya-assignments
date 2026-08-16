# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "numpy",
#     "scipy",
# ]
# ///

"""Sound I/O, preset management, serialization, and synthetic audio generation.

Handles decoding audio files (.wav in pure Python for 100% WASM/Pyodide compatibility,
with optional soundfile fallback for .mp3/.ogg/.flac), loading bundled presets (with
remote GitHub raw fallback for WASM / marimo.app environments where binary assets are
not cloned into Pyodide virtual FS), base64 WAV data URI encoding, and fallback synthesis.
"""

from __future__ import annotations

import base64
import io
import pathlib
import urllib.request
import numpy as np
import scipy.io.wavfile as wav

try:
    import soundfile as sf
except Exception:
    sf = None

_PRESET_DIR = pathlib.Path(__file__).parent / "assets" / "presets"
_GITHUB_RAW_BASE = "https://raw.githubusercontent.com/mushtaq/kimiya-assignments/main/sampling/assets/presets"

PRESETS: dict[str, dict[str, str]] = {
    "jazz_vibes": {
        "name": "Jazz Vibes (Kevin MacLeod)",
        "file": "jazz_vibes.wav",
    },
    "classical_strings": {
        "name": "Classical Strings (Brahms)",
        "file": "classical_strings.wav",
    },
    "drums_beat": {
        "name": "Drums & Bass Beat (Admiral Bob)",
        "file": "drums_beat.wav",
    },
    "speech_voice": {
        "name": "Spoken Speech (LibriSpeech)",
        "file": "speech_voice.wav",
    },
    "solo_trumpet": {
        "name": "Solo Trumpet (Mihai Sorohan)",
        "file": "solo_trumpet.wav",
    },
}

_PRESET_CACHE: dict[str, tuple[np.ndarray, int, str]] = {}


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


def decode_audio_bytes(raw_bytes: bytes, max_duration_s: float = 8.0) -> tuple[np.ndarray, int]:
    """Decodes raw audio bytes into a normalized float32 mono array (WAV or soundfile)."""
    data = None
    sr = None

    # 1. Pure Python scipy.io.wavfile decoder (100% WASM/Pyodide safe)
    try:
        sr, data = wav.read(io.BytesIO(raw_bytes))
    except Exception:
        pass

    # 2. Soundfile fallback if available (for MP3/OGG/FLAC in native Python)
    if data is None and sf is not None:
        try:
            data, sr = sf.read(io.BytesIO(raw_bytes))
        except Exception:
            pass

    if data is None or sr is None:
        raise ValueError("Could not decode audio data format")

    if data.ndim > 1:
        data = data.mean(axis=1)

    if np.issubdtype(data.dtype, np.integer):
        max_int = np.iinfo(data.dtype).max
        audio = data.astype(np.float32) / float(max_int)
    else:
        audio = data.astype(np.float32)

    # Trim to max_duration_s
    max_samples = int(max_duration_s * sr)
    if len(audio) > max_samples:
        audio = audio[:max_samples]

    # Smooth crossfade
    fade_len = int(0.04 * sr)
    if fade_len > 0 and len(audio) > 2 * fade_len:
        audio[:fade_len] *= np.linspace(0, 1, fade_len)
        audio[-fade_len:] *= np.linspace(1, 0, fade_len)

    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = (audio / max_val) * 0.95

    return audio.astype(np.float32), int(sr)


def load_preset_audio(preset_key: str) -> tuple[np.ndarray, int, str]:
    """Loads a preset audio file (from local disk or GitHub Raw in WASM) with in-memory caching."""
    if preset_key in _PRESET_CACHE:
        return _PRESET_CACHE[preset_key]

    if preset_key in PRESETS:
        preset_info = PRESETS[preset_key]
        raw_bytes = None

        # 1. Try reading from local / virtual file system first (if non-empty)
        local_path = _PRESET_DIR / preset_info["file"]
        if local_path.exists():
            try:
                content = local_path.read_bytes()
                if len(content) > 100:
                    raw_bytes = content
            except Exception:
                pass

        # 2. Fallback for WASM / marimo.app (where binary assets are 0-byte stubs or missing)
        if raw_bytes is None:
            try:
                url = f"{_GITHUB_RAW_BASE}/{preset_info['file']}"
                req = urllib.request.Request(url, headers={"User-Agent": "marimo-sampling"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = resp.read()
                    if len(data) > 100:
                        raw_bytes = data
            except Exception:
                pass

        if raw_bytes is not None:
            try:
                audio, sr = decode_audio_bytes(raw_bytes)
                result = (audio, sr, preset_info["name"])
                _PRESET_CACHE[preset_key] = result
                return result
            except Exception:
                pass

    if preset_key == "bell":
        audio, sr = synth_educational_bell()
        result = (audio, sr, "Harmonic Bell (Synthetic)")
        _PRESET_CACHE["bell"] = result
        return result

    # Fallback to synthetic bell
    audio, sr = synth_educational_bell()
    return audio, sr, "Harmonic Bell (Synthetic)"


def load_audio_data(
    raw_bytes: bytes | None,
    filename: str | None = None,
    max_duration_s: float = 8.0,
) -> tuple[np.ndarray, int, str]:
    """Loads uploaded audio (.wav, .mp3, .ogg, .flac) or falls back to default preset."""
    if raw_bytes:
        try:
            audio, sr = decode_audio_bytes(raw_bytes, max_duration_s)
            name = filename if filename else "Uploaded Audio"
            return audio, sr, name
        except Exception:
            pass
    return load_preset_audio("jazz_vibes")


def load_preset_or_upload(
    source_key: str,
    raw_bytes: bytes | None = None,
    filename: str | None = None,
    max_duration_s: float = 8.0,
) -> tuple[np.ndarray, int, str]:
    """Routes audio loading based on selected source (preset, upload, or synthetic bell)."""
    if source_key == "upload":
        if raw_bytes:
            return load_audio_data(raw_bytes, filename, max_duration_s)
        return load_preset_audio("jazz_vibes")
    return load_preset_audio(source_key)


def audio_to_base64_wav(audio: np.ndarray, sr: int) -> str:
    """Encodes float32 audio array into standard 16-bit PCM WAV base64 data URI."""
    int16_audio = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    buffer = io.BytesIO()
    wav.write(buffer, sr, int16_audio)
    b64_str = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:audio/wav;base64,{b64_str}"


if __name__ == "__main__":
    print("--- Sound I/O & Presets Test (WASM Safe) ---")
    for key in PRESETS:
        audio, sr, name = load_preset_audio(key)
        print(f"Loaded {key:18}: {name:30} | {len(audio):,} samples @ {sr} Hz")
    b64 = audio_to_base64_wav(audio, sr)
    print(f"Base64 WAV size: {len(b64):,} chars")
    print("Sound module validated successfully!")
