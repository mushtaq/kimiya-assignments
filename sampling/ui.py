# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
# ]
# ///

"""Marimo UI components and 2-column responsive dashboard layout.

Provides audio upload, a dynamic sampling rate radio ladder with inline
bandwidth savings percentages and source rate tagging, and theoretical callouts.
"""

from __future__ import annotations

import marimo as mo


def create_audio_upload() -> mo.ui.file:
    """Creates audio upload button for custom sound files."""
    return mo.ui.file(
        filetypes=[".wav", ".mp3", ".ogg", ".flac"],
        label="Upload audio file",
    )


def create_sampling_rate_options(source_sr: int) -> dict[str, int]:
    """Generates rate radio options dynamically with inline bandwidth savings and source indicator."""
    tier_names = {
        48000: "Studio HD",
        44100: "CD Audio",
        24000: "FM Quality",
        16000: "Voice Radio",
        8000: "Telephone",
        4000: "Walkie-Talkie",
    }

    rates = [48000, 44100, 24000, 16000, 8000, 4000]
    if source_sr not in rates:
        rates.append(source_sr)

    # Filter only rates <= source_sr and sort descending
    rates = sorted([r for r in rates if r <= source_sr], reverse=True)

    options: dict[str, int] = {}
    for r in rates:
        nyq_khz = r / 2000.0
        name = tier_names.get(r, "Custom Rate")
        if r == source_sr:
            label = f"{r:,} Hz • {name} • {nyq_khz:.2g} kHz Nyquist (Source • 0% savings)"
        else:
            savings = (1.0 - (r / source_sr)) * 100.0
            label = f"{r:,} Hz • {name} • {nyq_khz:.2g} kHz Nyquist ({savings:.1f}% savings)"
        options[label] = r

    return options


def create_rate_radio(source_sr: int) -> mo.ui.radio:
    """Creates a vertical radio selection list with inline bandwidth savings."""
    options = create_sampling_rate_options(source_sr)
    first_label = next(iter(options.keys()))
    return mo.ui.radio(
        options=options,
        value=first_label,
    )


def create_header() -> mo.Html:
    """Renders clean title and description header."""
    return mo.vstack([
        mo.md("### **Audio Sampling**"),
        mo.md("Explore how sound is turned into digital snapshots (samples) and hear how changing the sample rate affects audio quality."),
    ], gap=0.2)


def create_controls_card(audio_upload: mo.ui.file, rate_select: mo.ui.radio) -> mo.Html:
    """Groups audio source selector and sampling rate radio list with inline savings."""
    source_section = mo.vstack([
        mo.md("**Audio Source**"),
        audio_upload,
    ], gap=0.3)

    rate_section = mo.vstack([
        mo.md("**Sampling Rate ($f_s$) & Bandwidth Savings**"),
        rate_select,
    ], gap=0.3)

    return mo.vstack([
        source_section,
        rate_section,
    ], gap=0.8)


def create_takeaway(nyquist_hz: float) -> mo.Html:
    """Generates a simple educational callout explaining the Nyquist rule for students."""
    nyq_khz = nyquist_hz / 1000.0
    return mo.callout(
        mo.md(
            f"""
            **The Nyquist Rule**  
            To capture a sound wave cleanly, you need at least **2 sample points** for every wave cycle. That means the highest sound pitch you can record is always **half your sample rate**:
            
            $$f_{{\\text{{max}}}} = \\frac{{f_s}}{{2}} = \\mathbf{{{nyq_khz:.1f}\\text{{ kHz}}}}$$

            When you lower the sample rate, any sounds above the red dashed line get cut off, making the audio sound muffled. Notice how the sample dots on the waveform spread farther apart!
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
