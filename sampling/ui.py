# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
# ]
# ///

"""Marimo UI components and professional 2-column dashboard layout.

Provides modular control widgets, a 2x2 metrics grid, theoretical callouts,
and multi-column responsive dashboard composition with professional aesthetics.
"""

from __future__ import annotations

import marimo as mo


def create_controls() -> tuple[mo.ui.file, mo.ui.dropdown]:
    """Creates audio upload button and sampling rate selection dropdown with full-width layout."""
    audio_upload = mo.ui.file(
        filetypes=[".wav", ".mp3", ".ogg", ".flac"],
        label="Upload audio file",
    )

    sampling_rates = {
        "4,000 Hz (Walkie-Talkie • 2 kHz Nyquist)": 4000,
        "8,000 Hz (Telephone • 4 kHz Nyquist)": 8000,
        "16,000 Hz (Voice Radio • 8 kHz Nyquist)": 16000,
        "24,000 Hz (FM Quality • 12 kHz Nyquist)": 24000,
        "44,100 Hz (CD Audio • 22.05 kHz Nyquist)": 44100,
        "48,000 Hz (Studio HD • 24 kHz Nyquist)": 48000,
    }

    rate_select = mo.ui.dropdown(
        options=sampling_rates,
        value="48,000 Hz (Studio HD • 24 kHz Nyquist)",
        full_width=True,
    )
    return audio_upload, rate_select


def create_header() -> mo.Html:
    """Renders a clean, professional header."""
    return mo.vstack([
        mo.md("### Audio Sampling & The Nyquist Principle"),
        mo.md("Interactive exploration of digital signal discretization, bandlimited reconstruction, and spectral bandwidth."),
    ], gap=0.2)


def create_controls_card(audio_upload: mo.ui.file, rate_select: mo.ui.dropdown) -> mo.Html:
    """Groups audio input and sampling rate dropdown into a structured, well-aligned card."""
    source_section = mo.vstack([
        mo.md("**Audio Source**"),
        audio_upload,
    ], gap=0.3)

    rate_section = mo.vstack([
        mo.md("**Target Sampling Rate ($f_s$)**"),
        rate_select,
    ], gap=0.3)

    return mo.vstack([
        source_section,
        rate_section,
    ], gap=0.8)


def create_metrics_card(meta_orig: dict, meta_res: dict) -> mo.Html:
    """Renders a 2x2 grid comparing source and resampled audio metrics."""
    orig_pcm = meta_orig.get("pcm_kb", 0.0)
    res_pcm = meta_res.get("pcm_kb", 0.0)
    size_saving = (1.0 - (res_pcm / orig_pcm)) * 100.0 if orig_pcm > 0 else 0.0

    row1 = mo.hstack([
        mo.stat(
            label="Source Rate",
            value=f"{meta_orig['sampling_rate']:,} Hz",
            caption=f"{meta_orig['duration_s']:.2f}s • {meta_orig['sample_count']:,} samples",
            bordered=True,
        ),
        mo.stat(
            label="Resampled Rate",
            value=f"{meta_res['sampling_rate']:,} Hz",
            caption=f"{meta_res['sample_count']:,} total samples",
            bordered=True,
        ),
    ], widths="equal", gap=0.6)

    row2 = mo.hstack([
        mo.stat(
            label="Nyquist Cutoff",
            value=f"{meta_res['nyquist_hz']/1000.0:.1f} kHz",
            caption="Theoretical limit (fs / 2)",
            bordered=True,
        ),
        mo.stat(
            label="Bandwidth Savings",
            value=f"{size_saving:.1f}%" if size_saving > 0 else "0.0%",
            caption=f"{res_pcm:.1f} KB (orig {orig_pcm:.1f} KB)",
            bordered=True,
        ),
    ], widths="equal", gap=0.6)

    return mo.vstack([
        mo.md("**Signal & Transmission Metrics**"),
        row1,
        row2,
    ], gap=0.5)


def create_takeaway(nyquist_hz: float) -> mo.Html:
    """Generates a concise educational callout explaining the Nyquist principle."""
    nyq_khz = nyquist_hz / 1000.0
    return mo.callout(
        mo.md(
            f"""
            **Nyquist-Shannon Sampling Theorem**  
            To unambiguously reconstruct a continuous signal of bandwidth $B$, the sampling frequency must satisfy $f_s \\ge 2B$. The theoretical upper frequency limit is the **Nyquist Frequency**:
            
            $$f_{{\\text{{max}}}} = \\frac{{f_s}}{{2}} = \\mathbf{{{nyq_khz:.1f}\\text{{ kHz}}}}$$

            When lowering $f_s$, content above the red dashed Nyquist threshold cannot be represented and is eliminated via a band-limited anti-aliasing sinc filter. In the oscilloscope above, notice how the discrete sample points space further apart as sample density decreases.
            """
        ),
        kind="neutral",
    )


def create_dashboard_layout(
    left_column: mo.Html,
    right_column: mo.Html,
) -> mo.Html:
    """Arranges the dashboard into a balanced 2-column split."""
    return mo.hstack(
        [left_column, right_column],
        widths=[4, 6],
        gap=1.5,
        align="start",
    )
