# /// script
# dependencies = [
#     "librosa",
#     "marimo",
#     "matplotlib",
#     "numpy",
#     "soundfile",
# ]
# requires-python = ">=3.13"
# ///

import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium")


@app.cell
def imports():
    import io
    import librosa
    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    import soundfile as sf

    return io, librosa, mo, np, plt, sf


@app.cell(hide_code=True)
def header(mo):
    mo.md(r"""
    # 🎵 Simple Audio Sampling & Nyquist Explorer

    Explore what happens when audio is sampled at different rates ($f_s$).
    - **Hear** how lower sample rates remove high frequencies (the *telephone effect*).
    - **See** discrete sampling points overlaid onto the original continuous sound wave.
    - **Observe** the direct relationship between sample rate, bandwidth, and file size.
    """)
    return


@app.cell
def controls(mo):
    sr_slider = mo.ui.slider(
        start=4000,
        stop=48000,
        step=4000,
        value=8000,
        label="Target Sampling Rate ($f_s$ in Hz)",
        show_value=True,
    )
    sr_slider
    return (sr_slider,)


@app.cell
def generate_sound(np):
    # Continuous reference audio (48,000 Hz)
    orig_sr = 48000
    duration = 3.0  # seconds
    t = np.linspace(0, duration, int(orig_sr * duration), endpoint=False)

    # 3-second chirp sweeping from 200 Hz to 12,000 Hz
    k = (12000 - 200) / duration
    orig_audio = (0.5 * np.sin(2 * np.pi * (200 * t + 0.5 * k * t**2))).astype(np.float32)
    return orig_audio, orig_sr


@app.cell
def resample_audio(librosa, orig_audio, orig_sr, sr_slider):
    target_sr = sr_slider.value
    new_audio = librosa.resample(orig_audio, orig_sr=orig_sr, target_sr=target_sr)
    return new_audio, target_sr


@app.cell
def audio_players(io, mo, new_audio, orig_audio, orig_sr, sf, target_sr):
    def to_wav_bytes(y, sr):
        buf = io.BytesIO()
        sf.write(buf, y, sr, format="WAV")
        return buf.getvalue()

    orig_kb = (len(orig_audio) * 2) / 1024
    new_kb = (len(new_audio) * 2) / 1024
    reduction = (1 - new_kb / orig_kb) * 100

    mo.vstack([
        mo.md("### 🎧 Audio Comparison"),
        mo.hstack([
            mo.vstack([
                mo.md(f"**Original ({orig_sr:,} Hz)** &bull; `{orig_kb:.1f} KB`"),
                mo.audio(to_wav_bytes(orig_audio, orig_sr)),
            ]),
            mo.vstack([
                mo.md(f"**Resampled ({target_sr:,} Hz)** &bull; `{new_kb:.1f} KB` (**{reduction:.0f}% smaller**)"),
                mo.audio(to_wav_bytes(new_audio, target_sr)),
            ]),
        ], gap=3),
    ])
    return


@app.cell
def plot_waveform(new_audio, np, orig_audio, orig_sr, plt, target_sr):
    # Display an 8 millisecond window to see individual samples
    win_ms = 8.0
    n_orig = int(orig_sr * (win_ms / 1000.0))
    n_res = int(target_sr * (win_ms / 1000.0))

    t_orig_ms = np.linspace(0, win_ms, n_orig, endpoint=False)
    t_res_ms = np.linspace(0, win_ms, n_res, endpoint=False)

    fig, ax = plt.subplots(figsize=(7, 2.8), dpi=120)
    ax.plot(t_orig_ms, orig_audio[:n_orig], color="#94a3b8", label="Continuous Wave (48 kHz)", lw=1.5)
    ax.stem(t_res_ms, new_audio[:n_res], linefmt="#2563eb", markerfmt="C0o", basefmt=" ", label=f"Discrete Samples ({target_sr:,} Hz)")
    ax.set_title(f"Time-Domain Sampling View (Nyquist Limit = {target_sr / 2000:.1f} kHz)", fontsize=10, fontweight="bold")
    ax.set_xlabel("Time (milliseconds)", fontsize=9)
    ax.set_ylabel("Amplitude", fontsize=9)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", fontsize=8)
    plt.tight_layout()
    fig
    return


@app.cell
def takeaway_theory(mo, target_sr):
    nyquist_hz = target_sr / 2
    mo.md(
        rf"""
        ### 💡 Key Takeaway: The Nyquist Theorem
        - **Nyquist Frequency**: $f_{{\text{{Nyquist}}}} = \frac{{f_s}}{{2}} = \mathbf{{{nyquist_hz:,.0f}\text{{ Hz}}}}$
        - Any sound frequency component above **{nyquist_hz:,.0f} Hz** cannot be represented at this sampling rate and is filtered out.
        - Notice how high pitches cut out when you drag the slider below 16,000 Hz or 8,000 Hz!
        """
    )
    return


if __name__ == "__main__":
    app.run()
