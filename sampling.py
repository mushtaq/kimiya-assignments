# /// script
# dependencies = [
#     "marimo",
#     "matplotlib==3.11.1",
#     "numpy==2.5.2",
#     "scipy==1.17.0",
# ]
# requires-python = ">=3.13"
# ///

import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium")


@app.cell
def imports():
    import base64
    import io
    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    import scipy.io.wavfile as wav
    import scipy.signal as sig

    return base64, io, mo, np, plt, sig, wav


@app.cell
def audio_helpers(base64, io, np, sig, wav):
    def to_wav_url(y: np.ndarray, sr: int) -> str:
        buf = io.BytesIO()
        y_int16 = (np.clip(y, -1.0, 1.0) * 32767).astype(np.int16)
        wav.write(buf, sr, y_int16)
        return f"data:audio/wav;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"

    def synth_audio(sound_type: str, duration: float = 3.5, sr: int = 48000) -> np.ndarray:
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        if sound_type == "harmonics":
            freqs = [440, 880, 1760, 3520, 7040, 12000, 16000]
            weights = [0.35, 0.25, 0.18, 0.12, 0.08, 0.05, 0.04]
            y = sum(w * np.sin(2 * np.pi * f * t) for f, w in zip(freqs, weights))
        elif sound_type == "sweep":
            y = 0.4 * sig.chirp(t, f0=200, t1=duration, f1=20000, method="linear")
        elif sound_type == "sibilance":
            vowel = 0.3 * np.sin(2 * np.pi * 220 * t) + 0.2 * np.sin(2 * np.pi * 440 * t) + 0.15 * np.sin(2 * np.pi * 880 * t)
            noise = np.random.normal(0, 0.12, len(t)) * (np.sin(2 * np.pi * 1.5 * t) > 0.25) * 0.3
            y = vowel + noise
        else:
            y = 0.5 * np.sin(2 * np.pi * 440 * t)

        fade = int(sr * 0.03)
        if fade > 0:
            window = 0.5 * (1 - np.cos(np.linspace(0, np.pi, fade)))
            y[:fade] *= window
            y[-fade:] *= window[::-1]
        peak = np.max(np.abs(y))
        return (0.95 * y / peak).astype(np.float32) if peak > 0 else y.astype(np.float32)

    return synth_audio, to_wav_url


@app.cell
def intro_and_controls(mo):
    source_select = mo.ui.dropdown(
        options={
            "Harmonic Series (Overtones to 16 kHz)": "harmonics",
            "Frequency Sweep (200 Hz → 20 kHz)": "sweep",
            "Speech Sibilance (Vowels + Fricatives)": "sibilance",
        },
        value="Harmonic Series (Overtones to 16 kHz)",
        label="Signal Source",
    )

    rate_select = mo.ui.dropdown(
        options={
            "4,000 Hz (Walkie-Talkie)": 4000,
            "8,000 Hz (Telephone / Landline)": 8000,
            "16,000 Hz (VoIP / Zoom)": 16000,
            "22,050 Hz (FM Radio)": 22050,
            "32,000 Hz (Digital Broadcast)": 32000,
            "44,100 Hz (CD Standard)": 44100,
            "48,000 Hz (Studio Master)": 48000,
        },
        value="8,000 Hz (Telephone / Landline)",
        label="Target Rate",
    )

    header = mo.vstack([
        mo.md("# Digital Audio Sampling & The Nyquist Theorem"),
        mo.md("<span style='color: #64748b; font-size: 14px;'>Explore how sampling rate dictates frequency reproduction, anti-aliasing cutoff, and digital bandwidth.</span>"),
    ], gap=0.3)

    controls = mo.hstack([
        mo.vstack([source_select], gap=0).style({"flex": "1"}),
        mo.vstack([rate_select], gap=0).style({"flex": "1"}),
    ], gap=2, justify="space-between")

    return controls, header, rate_select, source_select


@app.cell
def process_audio(np, rate_select, sig, source_select, synth_audio):
    native_sr = 48000
    y_native = synth_audio(source_select.value, duration=3.5, sr=native_sr)
    active_rate = int(rate_select.value)

    if active_rate == native_sr:
        y_resampled = y_native.copy()
    else:
        num_samples = int(len(y_native) * active_rate / native_sr)
        y_resampled = sig.resample(y_native, num_samples).astype(np.float32)

    native_kb = (len(y_native) * 2 + 44) / 1024.0
    resampled_kb = (len(y_resampled) * 2 + 44) / 1024.0
    reduction_pct = max(0.0, (1.0 - (resampled_kb / max(native_kb, 0.001))) * 100.0)

    return active_rate, native_kb, native_sr, reduction_pct, resampled_kb, y_native, y_resampled


@app.cell
def audio_cards(
    active_rate,
    mo,
    native_kb,
    native_sr,
    reduction_pct,
    resampled_kb,
    to_wav_url,
    y_native,
    y_resampled,
):
    nyq_khz = (active_rate / 2.0) / 1000.0

    card_orig = mo.vstack([
        mo.hstack([
            mo.md("**ORIGINAL SIGNAL**"),
            mo.md(f"<span style='color: #64748b; font-size: 12px; font-variant-numeric: tabular-nums;'>{native_sr:,} Hz &bull; {native_kb:.1f} KB</span>"),
        ], justify="space-between", align="center"),
        mo.audio(src=to_wav_url(y_native, native_sr)),
        mo.md(f"<span style='font-size: 12px; color: #64748b;'>Full bandwidth &bull; Nyquist limit: **{native_sr/2000:.1f} kHz**</span>"),
    ], gap=0.5).style({
        "background": "#ffffff",
        "border": "1px solid #e2e8f0",
        "border-radius": "8px",
        "padding": "16px 20px",
        "flex": "1",
        "height": "100%",
    })

    card_res = mo.vstack([
        mo.hstack([
            mo.md("**RESAMPLED SIGNAL**"),
            mo.md(f"<span style='color: #2563eb; font-weight: 600; font-size: 12px; font-variant-numeric: tabular-nums;'>{active_rate:,} Hz &bull; {resampled_kb:.1f} KB</span>"),
        ], justify="space-between", align="center"),
        mo.audio(src=to_wav_url(y_resampled, active_rate)),
        mo.md(f"<span style='font-size: 12px; color: #2563eb;'>**{reduction_pct:.1f}% data saved** &bull; Nyquist limit: **{nyq_khz:.1f} kHz**</span>"),
    ], gap=0.5).style({
        "background": "#f8fafc",
        "border": "1px solid #cbd5e1",
        "border-radius": "8px",
        "padding": "16px 20px",
        "flex": "1",
        "height": "100%",
    })

    signals_view = mo.hstack([card_orig, card_res], gap=2, justify="space-between")
    return card_orig, card_res, nyq_khz, signals_view


@app.cell
def visualizations(active_rate, mo, native_sr, np, nyq_khz, plt, y_native, y_resampled):
    def style_axis(ax, title, xlabel, ylabel):
        ax.set_title(title, fontsize=9.5, fontweight='bold', color='#0f172a', pad=8)
        ax.set_xlabel(xlabel, fontsize=8.5, color='#64748b')
        ax.set_ylabel(ylabel, fontsize=8.5, color='#64748b')
        ax.grid(True, linestyle=':', color='#e2e8f0', alpha=0.8)
        ax.spines[['top', 'right']].set_visible(False)
        ax.spines[['left', 'bottom']].set_color('#cbd5e1')
        ax.tick_params(colors='#64748b', labelsize=8)
        ax.legend(loc='upper right', fontsize=8, frameon=False)

    # 1. Time-Domain Sampling Plot (8ms window)
    fig_time, ax_time = plt.subplots(figsize=(6.2, 2.9), dpi=120)
    fig_time.patch.set_facecolor('#ffffff')
    t0, win = 0.5, 0.008
    i0_nat, i1_nat = int(t0 * native_sr), int((t0 + win) * native_sr)
    i0_res, i1_res = int(t0 * active_rate), int((t0 + win) * active_rate)

    t_nat = np.linspace(t0 * 1000, (t0 + win) * 1000, i1_nat - i0_nat, endpoint=False)
    t_res = np.linspace(t0 * 1000, (t0 + win) * 1000, i1_res - i0_res, endpoint=False)

    ax_time.plot(t_nat, y_native[i0_nat:i1_nat], color='#94a3b8', label='Continuous Wave', lw=1.5, alpha=0.85)
    ax_time.stem(t_res, y_resampled[i0_res:i1_res], linefmt='#2563eb', markerfmt='.', basefmt=' ', label=f'Discrete Samples ({active_rate/1000:.1f} kHz)')
    style_axis(ax_time, "Discrete Time Sampling (8ms Window)", "Time (ms)", "Amplitude")
    plt.tight_layout()

    # 2. Frequency-Domain Spectrum Plot
    fig_freq, ax_freq = plt.subplots(figsize=(6.2, 2.9), dpi=120)
    fig_freq.patch.set_facecolor('#ffffff')
    n_fft = 4096

    def get_spectrum(y, sr):
        fft = np.abs(np.fft.rfft(y[:min(len(y), 65536)], n=n_fft))
        freqs = np.fft.rfftfreq(n_fft, d=1.0 / sr) / 1000.0
        mag = 20 * np.log10(np.maximum(fft, 1e-6))
        return freqs, mag - np.max(mag)

    f_nat, m_nat = get_spectrum(y_native, native_sr)
    f_res, m_res = get_spectrum(y_resampled, active_rate)

    ax_freq.plot(f_nat, m_nat, color='#94a3b8', label='Original Spectrum', lw=1.2, alpha=0.7)
    ax_freq.plot(f_res, m_res, color='#2563eb', label='Resampled Spectrum', lw=1.6)
    ax_freq.axvline(nyq_khz, color='#dc2626', linestyle='--', lw=1.4, label=f'Nyquist Limit ({nyq_khz:.1f} kHz)')
    ax_freq.axvspan(nyq_khz, 24.0, color='#fee2e2', alpha=0.45)
    ax_freq.set_xlim(0, 24)
    ax_freq.set_ylim(-55, 3)
    style_axis(ax_freq, "Frequency Spectrum & Cutoff", "Frequency (kHz)", "Magnitude (dB)")
    plt.tight_layout()

    card_style = {"flex": "1", "width": "100%", "background": "#ffffff", "border": "1px solid #f1f5f9", "border-radius": "8px", "padding": "8px"}
    plots_view = mo.hstack([
        mo.vstack([fig_time], align="center").style(card_style),
        mo.vstack([fig_freq], align="center").style(card_style),
    ], gap=2, justify="space-between")

    return plots_view


@app.cell
def takeaways_and_theory(
    active_rate,
    mo,
    native_kb,
    nyq_khz,
    reduction_pct,
    resampled_kb,
):
    takeaway_left = mo.vstack([
        mo.md("**Frequency Cutoff ($f_s / 2$)**"),
        mo.md(
            f"Sampling at **{active_rate:,} Hz** establishes a strict upper frequency limit of **{nyq_khz:.1f} kHz**. "
            f"Frequencies above this boundary are filtered to prevent aliasing distortion."
        ),
    ], gap=0.2).style({
        "background": "#f8fafc",
        "border": "1px solid #e2e8f0",
        "border-left": "3px solid #64748b",
        "border-radius": "6px",
        "padding": "12px 16px",
        "flex": "1",
    })

    takeaway_right = mo.vstack([
        mo.md("**Bandwidth & Storage Impact**"),
        mo.md(
            f"Uncompressed 16-bit PCM payload is reduced by **{reduction_pct:.1f}%** "
            f"(from **{native_kb:.1f} KB** down to **{resampled_kb:.1f} KB**)."
        ),
    ], gap=0.2).style({
        "background": "#f8fafc",
        "border": "1px solid #e2e8f0",
        "border-left": "3px solid #2563eb",
        "border-radius": "6px",
        "padding": "12px 16px",
        "flex": "1",
    })

    theory_left = mo.vstack([
        mo.md("#### 1. The Nyquist-Shannon Theorem"),
        mo.md(
            r"""
            A continuous bandlimited signal can be perfectly reconstructed from discrete samples if and only if the sampling rate $f_s$ exceeds twice the highest frequency component $f_{\text{max}}$:

            $$f_s \ge 2 \cdot f_{\text{max}} \quad \Longleftrightarrow \quad f_{\text{Nyquist}} = \frac{f_s}{2}$$

            The **Nyquist frequency** ($f_s / 2$) is the strict physical upper bound for any frequency that can be captured at that sample rate.
            """
        ),
    ], gap=0.4).style({"flex": "1", "padding": "16px 20px", "background": "#f8fafc", "border": "1px solid #e2e8f0", "border-radius": "8px"})

    theory_right = mo.vstack([
        mo.md("#### 2. Anti-Aliasing & Bitrate Scaling"),
        mo.md(
            r"""
            - **Anti-Aliasing:** Frequencies above $f_{\text{Nyquist}}$ must be filtered prior to sampling; otherwise they fold back into the audible band as discordant aliasing distortion.
            - **Bitrate Scaling:** Linear 16-bit PCM data rate scales in direct 1:1 proportion to sampling frequency:
        
            $$\text{Bitrate} = f_s \times 16\text{ bits/sample} = 2 f_s\text{ bytes/second}$$
            """
        ),
    ], gap=0.4).style({"flex": "1", "padding": "16px 20px", "background": "#f8fafc", "border": "1px solid #e2e8f0", "border-radius": "8px"})

    standards_table = mo.md(
        r"""
        | Standard Profile | Sample Rate ($f_s$) | Nyquist Cutoff ($f_N$) | Bandwidth Savings | Acoustic Characteristics |
        | :--- | :---: | :---: | :---: | :--- |
        | **Walkie-Talkie** | 4,000 Hz | 2,000 Hz | 91.7% | Intelligible vowels; severe high-frequency loss |
        | **Telephone / Landline** | 8,000 Hz | 4,000 Hz | 83.3% | Standard voice band; sibilance and treble removed |
        | **VoIP / Zoom Audio** | 16,000 Hz | 8,000 Hz | 66.7% | Wideband speech; clear fricatives and consonants |
        | **FM Broadcast** | 22,050 Hz | 11,025 Hz | 54.1% | Good broadcast quality; rolls off upper treble |
        | **Digital Broadcast** | 32,000 Hz | 16,000 Hz | 33.3% | Near full fidelity; covers 95% of musical spectrum |
        | **CD Audio** | 44,100 Hz | 22,050 Hz | 8.1% | Covers full human hearing range (20 Hz – 20 kHz) |
        | **Studio Master** | 48,000 Hz | 24,000 Hz | 0.0% | Professional recording & production reference |
        """
    )

    reference_view = mo.accordion({
        "Sampling Theory & Mathematical Principles": mo.hstack([theory_left, theory_right], gap=2, justify="space-between"),
        "Real-World Audio Standards Reference Table": standards_table,
    })

    takeaways_view = mo.hstack([takeaway_left, takeaway_right], gap=2, justify="space-between")
    return reference_view, takeaways_view


@app.cell
def main_layout(
    controls,
    header,
    mo,
    plots_view,
    reference_view,
    signals_view,
    takeaways_view,
):
    workbench = mo.vstack([
        header,
        controls,
        signals_view,
        plots_view,
        takeaways_view,
        reference_view,
    ], gap=1.5)
    workbench
    return (workbench,)


if __name__ == "__main__":
    app.run()
