# /// script
# dependencies = [
#     "librosa==1.0.0",
#     "marimo",
#     "matplotlib==3.11.1",
#     "numpy==2.5.2",
#     "soundfile==0.14.0",
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
    import librosa
    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    import soundfile as sf

    return base64, io, librosa, mo, np, plt, sf


@app.cell
def audio_helpers(base64, io, np, sf):
    def generate_sample_audio(sound_type: str, duration: float = 3.5, sr: int = 48000) -> np.ndarray:
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        if sound_type == "harmonics":
            freqs = [440, 880, 1760, 3520, 7040, 12000, 16000]
            weights = [0.35, 0.25, 0.18, 0.12, 0.08, 0.05, 0.04]
            y = sum(w * np.sin(2 * np.pi * f * t) for f, w in zip(freqs, weights))
        elif sound_type == "sweep":
            k = (20000 - 200) / duration
            y = 0.4 * np.sin(2 * np.pi * (200 * t + 0.5 * k * t**2))
        elif sound_type == "sibilance":
            vowel = 0.3 * np.sin(2 * np.pi * 220 * t) + 0.2 * np.sin(2 * np.pi * 440 * t) + 0.15 * np.sin(2 * np.pi * 880 * t)
            noise = np.random.normal(0, 0.12, len(t)) * (np.sin(2 * np.pi * 1.5 * t) > 0.25).astype(float) * 0.3
            y = vowel + noise
        else:
            y = 0.5 * np.sin(2 * np.pi * 440 * t)

        fade = int(sr * 0.03)
        fade_curve = 0.5 * (1 - np.cos(np.linspace(0, np.pi, fade)))
        y[:fade] *= fade_curve
        y[-fade:] *= fade_curve[::-1]
        peak = np.max(np.abs(y))
        return (0.95 * y / peak).astype(np.float32) if peak > 0 else y.astype(np.float32)

    def audio_to_wav_data_url(y: np.ndarray, sr: int) -> str:
        buf = io.BytesIO()
        sf.write(buf, y, sr, format='WAV', subtype='PCM_16')
        b64 = base64.b64encode(buf.getvalue()).decode('ascii')
        return f"data:audio/wav;base64,{b64}"

    def get_audio_size_kb(y: np.ndarray, sr: int) -> float:
        return (len(y) * 2 + 44) / 1024.0

    return audio_to_wav_data_url, generate_sample_audio, get_audio_size_kb


@app.cell
def intro_markdown(mo):
    source_select = mo.ui.dropdown(
        options={
            "Harmonic Series (Overtones to 16 kHz)": "harmonics",
            "Frequency Sweep (200 Hz → 20 kHz)": "sweep",
            "Speech Sibilance (Vowels + Fricatives)": "sibilance",
            "Upload Custom Audio File": "custom",
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

    file_upload = mo.ui.file(
        filetypes=[".wav", ".mp3", ".ogg", ".flac"],
        label="Choose audio file (.wav, .mp3, .ogg)",
    )

    header_view = mo.vstack([
        mo.md("# Digital Audio Sampling & The Nyquist Theorem"),
        mo.md("<span style='color: #64748b; font-size: 14px;'>Explore how sampling rate dictates frequency reproduction, anti-aliasing cutoff, and digital bandwidth.</span>"),
    ], gap=0.3)
    header_view
    return file_upload, rate_select, source_select


@app.cell
def part1_controls(
    audio_to_wav_data_url,
    file_upload,
    generate_sample_audio,
    get_audio_size_kb,
    io,
    librosa,
    mo,
    np,
    plt,
    rate_select,
    source_select,
):
    _source_key = source_select.value
    if _source_key == "custom" and file_upload.value:
        _bio = io.BytesIO(file_upload.value[0].contents)
        y_native, native_sr = librosa.load(_bio, sr=None, mono=True)
        source_label = file_upload.value[0].name
    else:
        native_sr = 48000
        _mode = _source_key if _source_key != "custom" else "harmonics"
        y_native = generate_sample_audio(_mode, duration=3.5, sr=native_sr)
        source_label = f"Synthetic {_mode.title()}"

    native_duration = len(y_native) / native_sr
    native_wav_url = audio_to_wav_data_url(y_native, native_sr)
    native_kb = get_audio_size_kb(y_native, native_sr)
    native_nyquist = native_sr / 2.0

    active_rate = int(rate_select.value)
    if active_rate == native_sr:
        y_resampled = y_native.copy()
    else:
        y_resampled = librosa.resample(y_native, orig_sr=native_sr, target_sr=active_rate)

    resampled_wav_url = audio_to_wav_data_url(y_resampled, active_rate)
    resampled_kb = get_audio_size_kb(y_resampled, active_rate)
    resampled_nyquist = active_rate / 2.0
    reduction_pct = max(0.0, (1.0 - (resampled_kb / max(native_kb, 0.001))) * 100.0)

    fig_time, ax_time = plt.subplots(figsize=(6.2, 2.9), dpi=120)
    fig_time.patch.set_facecolor('#ffffff')

    _win = 0.008
    _t0 = max(0.2, native_duration * 0.4)
    _t1 = _t0 + _win
    _i0_nat, _i1_nat = int(_t0 * native_sr), int(_t1 * native_sr)
    _i0_res, _i1_res = int(_t0 * active_rate), int(_t1 * active_rate)

    _t_nat = np.linspace(_t0 * 1000, _t1 * 1000, _i1_nat - _i0_nat, endpoint=False)
    _t_res = np.linspace(_t0 * 1000, _t1 * 1000, _i1_res - _i0_res, endpoint=False)

    ax_time.plot(_t_nat, y_native[_i0_nat:_i1_nat], color='#94a3b8', label=f'Continuous Wave', lw=1.5, alpha=0.85)
    ax_time.stem(_t_res, y_resampled[_i0_res:_i1_res], linefmt='#2563eb', markerfmt='.', basefmt=' ', label=f'Discrete Samples ({active_rate/1000:.1f} kHz)')
    ax_time.set_title("Discrete Time Sampling (8ms Window)", fontsize=9.5, fontweight='bold', color='#0f172a', pad=8)
    ax_time.set_xlabel("Time (ms)", fontsize=8.5, color='#64748b')
    ax_time.set_ylabel("Amplitude", fontsize=8.5, color='#64748b')
    ax_time.grid(True, linestyle=':', color='#e2e8f0', alpha=0.8)
    ax_time.spines[['top', 'right']].set_visible(False)
    ax_time.spines[['left', 'bottom']].set_color('#cbd5e1')
    ax_time.tick_params(colors='#64748b', labelsize=8)
    ax_time.legend(loc='upper right', fontsize=8, frameon=False)
    plt.tight_layout()

    fig_freq, ax_freq = plt.subplots(figsize=(6.2, 2.9), dpi=120)
    fig_freq.patch.set_facecolor('#ffffff')

    _n_fft = 4096
    _fft_nat = np.abs(np.fft.rfft(y_native[:min(len(y_native), 65536)], n=_n_fft))
    _freqs_nat = np.fft.rfftfreq(_n_fft, d=1.0 / native_sr) / 1000.0
    _mag_nat = 20 * np.log10(np.maximum(_fft_nat, 1e-6))
    _mag_nat -= np.max(_mag_nat)

    _fft_res = np.abs(np.fft.rfft(y_resampled[:min(len(y_resampled), 65536)], n=_n_fft))
    _freqs_res = np.fft.rfftfreq(_n_fft, d=1.0 / active_rate) / 1000.0
    _mag_res = 20 * np.log10(np.maximum(_fft_res, 1e-6))
    _mag_res -= np.max(_mag_res)

    ax_freq.plot(_freqs_nat, _mag_nat, color='#94a3b8', label='Original Spectrum', lw=1.2, alpha=0.7)
    ax_freq.plot(_freqs_res, _mag_res, color='#2563eb', label='Resampled Spectrum', lw=1.6)

    _nyq_khz = resampled_nyquist / 1000.0
    ax_freq.axvline(_nyq_khz, color='#dc2626', linestyle='--', lw=1.4, label=f'Nyquist Limit ({_nyq_khz:.1f} kHz)')
    ax_freq.axvspan(_nyq_khz, 24.0, color='#fee2e2', alpha=0.45)
    ax_freq.set_xlim(0, 24)
    ax_freq.set_ylim(-55, 3)
    ax_freq.set_title("Frequency Spectrum & Cutoff", fontsize=9.5, fontweight='bold', color='#0f172a', pad=8)
    ax_freq.set_xlabel("Frequency (kHz)", fontsize=8.5, color='#64748b')
    ax_freq.set_ylabel("Magnitude (dB)", fontsize=8.5, color='#64748b')
    ax_freq.grid(True, linestyle=':', color='#e2e8f0', alpha=0.8)
    ax_freq.spines[['top', 'right']].set_visible(False)
    ax_freq.spines[['left', 'bottom']].set_color('#cbd5e1')
    ax_freq.tick_params(colors='#64748b', labelsize=8)
    ax_freq.legend(loc='upper right', fontsize=8, frameon=False)
    plt.tight_layout()

    _row_controls = mo.hstack([
        mo.vstack([source_select], gap=0).style({"flex": "1"}),
        mo.vstack([rate_select], gap=0).style({"flex": "1"}),
    ], gap=2, justify="space-between")

    _card_orig = mo.vstack([
        mo.hstack([
            mo.md("**ORIGINAL SIGNAL**"),
            mo.md(f"<span style='color: #64748b; font-size: 12px; font-variant-numeric: tabular-nums;'>{native_sr:,} Hz &bull; {native_kb:.1f} KB</span>"),
        ], justify="space-between", align="center"),
        mo.audio(src=native_wav_url),
        mo.md(f"<span style='font-size: 12px; color: #64748b;'>Full bandwidth &bull; Nyquist limit: **{native_nyquist/1000:.1f} kHz**</span>"),
    ], gap=0.5).style({
        "background": "#ffffff",
        "border": "1px solid #e2e8f0",
        "border-radius": "8px",
        "padding": "16px 20px",
        "flex": "1",
        "height": "100%",
    })

    _card_res = mo.vstack([
        mo.hstack([
            mo.md(f"**RESAMPLED SIGNAL**"),
            mo.md(f"<span style='color: #2563eb; font-weight: 600; font-size: 12px; font-variant-numeric: tabular-nums;'>{active_rate:,} Hz &bull; {resampled_kb:.1f} KB</span>"),
        ], justify="space-between", align="center"),
        mo.audio(src=resampled_wav_url),
        mo.md(f"<span style='font-size: 12px; color: #2563eb;'>**{reduction_pct:.1f}% data saved** &bull; Nyquist limit: **{_nyq_khz:.1f} kHz**</span>"),
    ], gap=0.5).style({
        "background": "#f8fafc",
        "border": "1px solid #cbd5e1",
        "border-radius": "8px",
        "padding": "16px 20px",
        "flex": "1",
        "height": "100%",
    })

    _row_signals = mo.hstack([_card_orig, _card_res], gap=2, justify="space-between")

    _row_plots = mo.hstack([
        mo.vstack([fig_time], align="center").style({"flex": "1", "width": "100%", "background": "#ffffff", "border": "1px solid #f1f5f9", "border-radius": "8px", "padding": "8px"}),
        mo.vstack([fig_freq], align="center").style({"flex": "1", "width": "100%", "background": "#ffffff", "border": "1px solid #f1f5f9", "border-radius": "8px", "padding": "8px"}),
    ], gap=2, justify="space-between")

    _takeaway_left = mo.vstack([
        mo.md("**Frequency Cutoff ($f_s / 2$)**"),
        mo.md(
            f"Sampling at **{active_rate:,} Hz** establishes a strict upper frequency limit of **{_nyq_khz:.1f} kHz**. "
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

    _takeaway_right = mo.vstack([
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

    _row_takeaways = mo.hstack([_takeaway_left, _takeaway_right], gap=2, justify="space-between")

    workbench_view = mo.vstack([
        _row_controls,
        file_upload if _source_key == "custom" else mo.md(""),
        _row_signals,
        _row_plots,
        _row_takeaways,
    ], gap=1.5)
    workbench_view
    return


@app.cell
def part1_loader(mo):
    _theory_col_left = mo.vstack([
        mo.md("#### 1. The Nyquist-Shannon Theorem"),
        mo.md(
            r"""
            A continuous bandlimited signal can be perfectly reconstructed from discrete samples if and only if the sampling rate $f_s$ exceeds twice the highest frequency component $f_{\text{max}}$:

            $$f_s \ge 2 \cdot f_{\text{max}} \quad \Longleftrightarrow \quad f_{\text{Nyquist}} = \frac{f_s}{2}$$

            The **Nyquist frequency** ($f_s / 2$) is the strict physical upper bound for any frequency that can be captured at that sample rate.
            """
        ),
    ], gap=0.4).style({"flex": "1", "padding": "16px 20px", "background": "#f8fafc", "border": "1px solid #e2e8f0", "border-radius": "8px"})

    _theory_col_right = mo.vstack([
        mo.md("#### 2. Anti-Aliasing & Bitrate Scaling"),
        mo.md(
            r"""
            - **Anti-Aliasing:** Frequencies above $f_{\text{Nyquist}}$ must be filtered prior to sampling; otherwise they fold back into the audible band as discordant aliasing distortion.
            - **Bitrate Scaling:** Linear 16-bit PCM data rate scales in direct 1:1 proportion to sampling frequency:
        
            $$\text{Bitrate} = f_s \times 16\text{ bits/sample} = 2 f_s\text{ bytes/second}$$
            """
        ),
    ], gap=0.4).style({"flex": "1", "padding": "16px 20px", "background": "#f8fafc", "border": "1px solid #e2e8f0", "border-radius": "8px"})

    _theory_2col = mo.hstack([_theory_col_left, _theory_col_right], gap=2, justify="space-between")

    _standards_table_md = mo.md(
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
        "Sampling Theory & Mathematical Principles": _theory_2col,
        "Real-World Audio Standards Reference Table": _standards_table_md,
    })
    reference_view
    return


if __name__ == "__main__":
    app.run()
