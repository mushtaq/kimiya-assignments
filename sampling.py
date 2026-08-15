# /// script
# dependencies = [
#     "marimo",
#     "matplotlib==3.11.1",
#     "numpy==2.5.2",
#     "scipy==1.17.0",
# ]
# requires-python = ">=3.13"
# ///

"""Digital Audio Sampling & The Nyquist Theorem.

A pedagogical Marimo notebook demonstrating digital signal sampling,
anti-aliasing filters, frequency cutoffs, and bandwidth scaling.

Structured into 3 distinct pedagogical layers:
- Layer 1: Core Mathematical DSP Engine (Pure Python / NumPy / SciPy)
- Layer 2: Scientific Visualization Engine (Pure Matplotlib / NumPy)
- Layer 3: Interactive Reactive Layer (Marimo UI & Reactive DAG)
"""

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
    def synth_signal(signal_type: str, duration: float = 3.5, sr: int = 48000) -> np.ndarray:
        """Synthesize bandlimited continuous reference audio signal (48 kHz reference)."""
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        if signal_type == "harmonics":
            freqs = [440, 880, 1760, 3520, 7040, 12000, 16000]
            weights = [0.35, 0.25, 0.18, 0.12, 0.08, 0.05, 0.04]
            y = sum(w * np.sin(2 * np.pi * f * t) for f, w in zip(freqs, weights))
        elif signal_type == "sweep":
            y = 0.4 * sig.chirp(t, f0=200, t1=duration, f1=20000, method="linear")
        elif signal_type == "sibilance":
            vowel = 0.3 * np.sin(2 * np.pi * 220 * t) + 0.2 * np.sin(2 * np.pi * 440 * t) + 0.15 * np.sin(2 * np.pi * 880 * t)
            noise = np.random.normal(0, 0.12, len(t)) * (np.sin(2 * np.pi * 1.5 * t) > 0.25) * 0.3
            y = vowel + noise
        else:
            y = 0.5 * np.sin(2 * np.pi * 440 * t)

        fade_len = int(sr * 0.03)
        if fade_len > 0:
            window = 0.5 * (1.0 - np.cos(np.linspace(0, np.pi, fade_len)))
            y[:fade_len] *= window
            y[-fade_len:] *= window[::-1]

        peak = np.max(np.abs(y))
        return (0.95 * y / peak).astype(np.float32) if peak > 0 else y.astype(np.float32)


    def resample_signal(y: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Resample discrete signal with bandlimited Fourier anti-aliasing filter."""
        if target_sr == orig_sr:
            return y.copy()
        num_samples = int(len(y) * target_sr / orig_sr)
        return sig.resample(y, num_samples).astype(np.float32)


    def compute_spectrum(y: np.ndarray, sr: int, n_fft: int = 4096) -> tuple[np.ndarray, np.ndarray]:
        """Compute real Fast Fourier Transform (rFFT) magnitude spectrum in decibels."""
        samples = y[:min(len(y), 65536)]
        fft = np.abs(np.fft.rfft(samples, n=n_fft))
        freqs_khz = np.fft.rfftfreq(n_fft, d=1.0 / sr) / 1000.0
        mag_db = 20.0 * np.log10(np.maximum(fft, 1e-6))
        mag_db -= np.max(mag_db)
        return freqs_khz, mag_db


    def compute_bandwidth_metrics(num_orig_samples: int, num_res_samples: int) -> dict[str, float]:
        """Calculate uncompressed 16-bit linear PCM payload sizes and bandwidth reduction."""
        orig_kb = (num_orig_samples * 2 + 44) / 1024.0
        res_kb = (num_res_samples * 2 + 44) / 1024.0
        savings_pct = max(0.0, (1.0 - (res_kb / max(orig_kb, 0.001))) * 100.0)
        return {"orig_kb": orig_kb, "res_kb": res_kb, "savings_pct": savings_pct}


    def encode_wav_base64(y: np.ndarray, sr: int) -> str:
        """Encode float32 audio array into standard 16-bit PCM WAV data URL."""
        buf = io.BytesIO()
        y_int16 = (np.clip(y, -1.0, 1.0) * 32767).astype(np.int16)
        wav.write(buf, sr, y_int16)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:audio/wav;base64,{b64}"


    return (
        compute_bandwidth_metrics,
        compute_spectrum,
        encode_wav_base64,
        resample_signal,
        synth_signal,
    )


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
        mo.md("<span style='color: #64748b; font-size: 14px;'>Interactive exploration of sampling rates, anti-aliasing filters, frequency reproduction, and bandwidth scaling.</span>"),
    ], gap=0.3)

    controls_row = mo.hstack([
        mo.vstack([source_select], gap=0).style({"flex": "1"}),
        mo.vstack([rate_select], gap=0).style({"flex": "1"}),
    ], gap=2, justify="space-between")

    return controls_row, header, rate_select, source_select


@app.cell
def process_audio(
    compute_bandwidth_metrics,
    compute_spectrum,
    rate_select,
    resample_signal,
    source_select,
    synth_signal,
):
    native_sr = 48000
    active_rate = int(rate_select.value)

    # 1. Synthesize reference continuous signal (48 kHz)
    y_native = synth_signal(source_select.value, duration=3.5, sr=native_sr)

    # 2. Apply anti-aliased resampling to target rate
    y_resampled = resample_signal(y_native, orig_sr=native_sr, target_sr=active_rate)

    # 3. Compute spectral and bandwidth metrics
    f_orig, m_orig = compute_spectrum(y_native, native_sr)
    f_res, m_res = compute_spectrum(y_resampled, active_rate)
    metrics = compute_bandwidth_metrics(len(y_native), len(y_resampled))
    nyquist_khz = (active_rate / 2.0) / 1000.0

    return (
        active_rate,
        f_orig,
        f_res,
        m_orig,
        m_res,
        metrics,
        native_sr,
        nyquist_khz,
        y_native,
        y_resampled,
    )


@app.cell
def audio_cards(
    active_rate,
    encode_wav_base64,
    metrics,
    mo,
    native_sr,
    nyquist_khz,
    y_native,
    y_resampled,
):
    orig_card = mo.vstack([
        mo.hstack([
            mo.md("**ORIGINAL SIGNAL**"),
            mo.md(f"<span style='color: #64748b; font-size: 12px; font-variant-numeric: tabular-nums;'>{native_sr:,} Hz &bull; {metrics['orig_kb']:.1f} KB</span>"),
        ], justify="space-between", align="center"),
        mo.audio(src=encode_wav_base64(y_native, native_sr)),
        mo.md(f"<span style='font-size: 12px; color: #64748b;'>Full bandwidth &bull; Nyquist limit: **{native_sr/2000:.1f} kHz**</span>"),
    ], gap=0.5).style({
        "background": "#ffffff",
        "border": "1px solid #e2e8f0",
        "border-radius": "8px",
        "padding": "16px 20px",
        "flex": "1",
        "height": "100%",
    })

    res_card = mo.vstack([
        mo.hstack([
            mo.md("**RESAMPLED SIGNAL**"),
            mo.md(f"<span style='color: #2563eb; font-weight: 600; font-size: 12px; font-variant-numeric: tabular-nums;'>{active_rate:,} Hz &bull; {metrics['res_kb']:.1f} KB</span>"),
        ], justify="space-between", align="center"),
        mo.audio(src=encode_wav_base64(y_resampled, active_rate)),
        mo.md(f"<span style='font-size: 12px; color: #2563eb;'>**{metrics['savings_pct']:.1f}% data saved** &bull; Nyquist limit: **{nyquist_khz:.1f} kHz**</span>"),
    ], gap=0.5).style({
        "background": "#f8fafc",
        "border": "1px solid #cbd5e1",
        "border-radius": "8px",
        "padding": "16px 20px",
        "flex": "1",
        "height": "100%",
    })

    signals_row = mo.hstack([orig_card, res_card], gap=2, justify="space-between")

    return (signals_row,)


@app.cell
def visualizations(
    active_rate,
    f_orig,
    f_res,
    m_orig,
    m_res,
    mo,
    native_sr,
    np,
    plt,
    y_native,
    y_resampled,
):
    def style_axes(ax, title: str, xlabel: str, ylabel: str) -> None:
        """Apply clean minimalist scientific styling to a Matplotlib axes."""
        ax.set_title(title, fontsize=9.5, fontweight="bold", color="#0f172a", pad=8)
        ax.set_xlabel(xlabel, fontsize=8.5, color="#64748b")
        ax.set_ylabel(ylabel, fontsize=8.5, color="#64748b")
        ax.grid(True, linestyle=":", color="#e2e8f0", alpha=0.8)
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color("#cbd5e1")
        ax.tick_params(colors="#64748b", labelsize=8)
        ax.legend(loc="upper right", fontsize=8, frameon=False)


    def plot_time_domain_sampling(y_orig: np.ndarray, y_res: np.ndarray, orig_sr: int, target_sr: int, window_ms: float = 8.0) -> plt.Figure:
        """Plot discrete sampling points overlaid onto continuous reference waveform."""
        fig, ax = plt.subplots(figsize=(6.2, 2.9), dpi=120)
        fig.patch.set_facecolor("#ffffff")
        t0 = 0.5
        win_s = window_ms / 1000.0
        i0_nat, i1_nat = int(t0 * orig_sr), int((t0 + win_s) * orig_sr)
        i0_res, i1_res = int(t0 * target_sr), int((t0 + win_s) * target_sr)

        t_nat = np.linspace(t0 * 1000, (t0 + win_s) * 1000, i1_nat - i0_nat, endpoint=False)
        t_res = np.linspace(t0 * 1000, (t0 + win_s) * 1000, i1_res - i0_res, endpoint=False)

        ax.plot(t_nat, y_orig[i0_nat:i1_nat], color="#94a3b8", label="Continuous Wave", lw=1.5, alpha=0.85)
        ax.stem(t_res, y_res[i0_res:i1_res], linefmt="#2563eb", markerfmt=".", basefmt=" ", label=f"Discrete Samples ({target_sr/1000:.1f} kHz)")
        style_axes(ax, f"Discrete Time Sampling ({window_ms:.0f}ms Window)", "Time (ms)", "Amplitude")
        plt.tight_layout()
        return fig


    def plot_frequency_spectrum(f_orig: np.ndarray, m_orig: np.ndarray, f_res: np.ndarray, m_res: np.ndarray, target_sr: int) -> plt.Figure:
        """Plot frequency spectrum comparison with Nyquist limit and anti-aliasing cutoff."""
        fig, ax = plt.subplots(figsize=(6.2, 2.9), dpi=120)
        fig.patch.set_facecolor("#ffffff")
        nyq_khz = (target_sr / 2.0) / 1000.0

        ax.plot(f_orig, m_orig, color="#94a3b8", label="Original Spectrum", lw=1.2, alpha=0.7)
        ax.plot(f_res, m_res, color="#2563eb", label="Resampled Spectrum", lw=1.6)
        ax.axvline(nyq_khz, color="#dc2626", linestyle="--", lw=1.4, label=f"Nyquist Limit ({nyq_khz:.1f} kHz)")
        ax.axvspan(nyq_khz, 24.0, color="#fee2e2", alpha=0.45)
        ax.set_xlim(0, 24)
        ax.set_ylim(-55, 3)
        style_axes(ax, "Frequency Spectrum & Cutoff", "Frequency (kHz)", "Magnitude (dB)")
        plt.tight_layout()
        return fig

    fig_time = plot_time_domain_sampling(y_native, y_resampled, native_sr, active_rate)
    fig_freq = plot_frequency_spectrum(f_orig, m_orig, f_res, m_res, active_rate)

    card_style = {
        "flex": "1",
        "width": "100%",
        "background": "#ffffff",
        "border": "1px solid #f1f5f9",
        "border-radius": "8px",
        "padding": "8px",
    }

    plots_row = mo.hstack([
        mo.vstack([fig_time], align="center").style(card_style),
        mo.vstack([fig_freq], align="center").style(card_style),
    ], gap=2, justify="space-between")

    return (plots_row,)


@app.cell
def takeaways_and_theory(active_rate, metrics, mo, nyquist_khz):
    takeaway_cutoff = mo.vstack([
        mo.md("**Frequency Cutoff ($f_s / 2$)**"),
        mo.md(
            f"Sampling at **{active_rate:,} Hz** establishes a strict upper frequency limit of **{nyquist_khz:.1f} kHz**. "
            f"Frequencies above this boundary are filtered by the anti-aliasing stage to prevent in-band distortion."
        ),
    ], gap=0.2).style({
        "background": "#f8fafc",
        "border": "1px solid #e2e8f0",
        "border-left": "3px solid #64748b",
        "border-radius": "6px",
        "padding": "12px 16px",
        "flex": "1",
    })

    takeaway_bandwidth = mo.vstack([
        mo.md("**Bandwidth & Storage Impact**"),
        mo.md(
            f"Uncompressed 16-bit PCM payload is reduced by **{metrics['savings_pct']:.1f}%** "
            f"(from **{metrics['orig_kb']:.1f} KB** down to **{metrics['res_kb']:.1f} KB**)."
        ),
    ], gap=0.2).style({
        "background": "#f8fafc",
        "border": "1px solid #e2e8f0",
        "border-left": "3px solid #2563eb",
        "border-radius": "6px",
        "padding": "12px 16px",
        "flex": "1",
    })

    takeaways_row = mo.hstack([takeaway_cutoff, takeaway_bandwidth], gap=2, justify="space-between")

    architecture_guide = mo.md(
        r"""
        This notebook is structured into three clean, decoupled software layers:

        ---

        #### <span style="background:#f0fdf4; color:#166534; border:1px solid #bbf7d0; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; padding:3px 8px; border-radius:4px;">Layer 1 &bull; Core DSP Engine</span> &nbsp; *(Pure Python / NumPy / SciPy)*
        * **Pure mathematical logic** — zero UI, zero Matplotlib, zero Marimo.
        * **Functions**: `synth_signal()`, `resample_signal()`, `compute_spectrum()`, `compute_bandwidth_metrics()`.
        * **Student Exercise**: These functions are standalone and can be copied or imported directly into standard `.py` scripts and unit tests:
          ```python
          from sampling import synth_signal, resample_signal, compute_spectrum
          ```

        ---

        #### <span style="background:#f0f9ff; color:#075985; border:1px solid #bae6fd; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; padding:3px 8px; border-radius:4px;">Layer 2 &bull; Scientific Visualization</span> &nbsp; *(Pure Matplotlib / NumPy)*
        * **Publication-quality plotting functions** returning raw `plt.Figure` objects.
        * **Functions**: `plot_time_domain_sampling()`, `plot_frequency_spectrum()`.
        * **Student Exercise**: Call these functions with any NumPy audio array to generate standalone figures for lab reports.

        ---

        #### <span style="background:#faf5ff; color:#6b21a8; border:1px solid #e9d5ff; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; padding:3px 8px; border-radius:4px;">Layer 3 &bull; Interactive Reactive Workbench</span> &nbsp; *(Marimo UI)*
        * **Reactive DAG wiring** — connects `mo.ui.dropdown` inputs to the DSP and plotting engines.
        * Assembles responsive audio player cards, metrics callouts, and layout containers.
        """
    )

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
            * **Anti-Aliasing Filter:** Frequencies above $f_{\text{Nyquist}}$ must be filtered prior to sampling; otherwise they fold back into the audible band as discordant aliasing distortion.
            * **Bitrate Scaling:** Linear 16-bit PCM data rate scales in direct 1:1 proportion to sampling frequency:
    
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
        "Code Architecture & Pedagogical Layering Guide": architecture_guide,
        "Sampling Theory & Mathematical Principles": mo.hstack([theory_left, theory_right], gap=2, justify="space-between"),
        "Real-World Audio Standards Reference Table": standards_table,
    })

    return reference_view, takeaways_row


@app.cell
def main_layout(
    controls_row,
    header,
    mo,
    plots_row,
    reference_view,
    signals_row,
    takeaways_row,
):
    workbench = mo.vstack([
        header,
        controls_row,
        signals_row,
        plots_row,
        takeaways_row,
        reference_view,
    ], gap=1.5)
    workbench

    return


if __name__ == "__main__":
    app.run()
