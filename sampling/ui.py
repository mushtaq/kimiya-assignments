"""Marimo UI components and 2-column responsive dashboard layout.

Provides audio source selection, dynamic sampling rate controls with bandwidth
savings metrics, aligned 2-column educational foundations, and audio-specific insights.
"""

from __future__ import annotations

import marimo as mo


def create_source_dropdown() -> mo.ui.dropdown:
    """Creates a dropdown selector for preset audio clips or custom upload without emojis."""
    options = {
        "Jazz Vibes (Music - Default)": "jazz_vibes",
        "Classical Strings (Orchestra)": "classical_strings",
        "Drums & Bass Beat (Percussion)": "drums_beat",
        "Spoken Speech (Voice)": "speech_voice",
        "Solo Trumpet (Fanfare)": "solo_trumpet",
        "Harmonic Bell (Synthetic)": "bell",
        "Upload Custom Audio...": "upload",
    }
    return mo.ui.dropdown(
        options=options,
        value="Jazz Vibes (Music - Default)",
    )


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
        mo.md("Explore how sound is converted into discrete digital samples and observe the audible and spectral effects of changing the sampling rate."),
    ], gap=0.2)


def create_controls_card(
    source_select: mo.ui.dropdown,
    audio_upload: mo.ui.file,
    rate_select: mo.ui.radio,
) -> mo.Html:
    """Groups audio source dropdown, conditional file upload, and sampling rate radio list."""
    if source_select.value == "upload":
        source_body = mo.vstack([
            source_select,
            audio_upload,
        ], gap=0.3)
    else:
        source_body = source_select

    source_section = mo.vstack([
        mo.md("**Audio Source**"),
        source_body,
    ], gap=0.3)

    rate_section = mo.vstack([
        mo.md("**Sampling Rate ($f_s$) & Bandwidth Savings**"),
        rate_select,
    ], gap=0.3)

    return mo.vstack([
        source_section,
        rate_section,
    ], gap=0.8)


def get_audio_insights(source_key: str, nyquist_hz: float, current_sr: int) -> str:
    """Returns deep observations about the nature of the selected audio and the expected downsampling effect."""
    nyq_khz = nyquist_hz / 1000.0

    if source_key == "jazz_vibes":
        nature = "**Nature of Audio**: Polyphonic acoustic arrangement featuring vibraphone with resonant metallic bar overtones (reaching 14–16 kHz), piano body resonance, and upright acoustic bass."
        if current_sr >= 44100:
            effect = f"**Current Effect ({current_sr:,} Hz / {nyq_khz:.1f} kHz Nyquist)**: Full acoustic air, metallic sparkle, and harmonic decay remain completely intact across the full audible spectrum."
        elif current_sr >= 16000:
            effect = f"**Current Effect ({current_sr:,} Hz / {nyq_khz:.1f} kHz Nyquist)**: High-frequency metallic shimmer above {nyq_khz:.1f} kHz is cut off; the vibraphone sounds slightly warmer with reduced brightness."
        else:
            effect = f"**Current Effect ({current_sr:,} Hz / {nyq_khz:.1f} kHz Nyquist)**: High overtones are completely eliminated, leaving only the fundamental bass and midrange melody in a dark, muffled telephone-grade sound."
        return f"{nature}\n\n{effect}"

    if source_key == "classical_strings":
        nature = "**Nature of Audio**: Orchestral string ensemble (Brahms Hungarian Dance) rich in complex high-frequency bow friction, rosin attack transients, and natural concert hall acoustic reverberation."
        if current_sr >= 44100:
            effect = f"**Current Effect ({current_sr:,} Hz / {nyq_khz:.1f} kHz Nyquist)**: Delicate violin bow scrapings and spacious orchestral hall depth are fully preserved."
        elif current_sr >= 16000:
            effect = f"**Current Effect ({current_sr:,} Hz / {nyq_khz:.1f} kHz Nyquist)**: Upper string sheen above {nyq_khz:.1f} kHz is smoothed away, giving violins a softer, less airy character."
        else:
            effect = f"**Current Effect ({current_sr:,} Hz / {nyq_khz:.1f} kHz Nyquist)**: Rapid bow articulations lose clarity; the orchestra sounds boxy and distant, reminiscent of vintage 78 RPM gramophone recordings."
        return f"{nature}\n\n{effect}"

    if source_key == "drums_beat":
        nature = "**Nature of Audio**: Wide-bandwidth percussive drum groove spanning low sub-bass kick thumps, snappy snare wire sizzle (5–8 kHz), and open hi-hat cymbals extending past 15 kHz."
        if current_sr >= 44100:
            effect = f"**Current Effect ({current_sr:,} Hz / {nyq_khz:.1f} kHz Nyquist)**: Sharp transient attack spikes and crisp cymbal decay are reproduced with maximum punch."
        elif current_sr >= 16000:
            effect = f"**Current Effect ({current_sr:,} Hz / {nyq_khz:.1f} kHz Nyquist)**: High cymbal sizzle is attenuated; snare drum transients lose their upper bite."
        else:
            effect = f"**Current Effect ({current_sr:,} Hz / {nyq_khz:.1f} kHz Nyquist)**: Cymbals are completely silenced (>4 kHz); only the low kick and dull snare body remain, demonstrating extreme loss of transient information."
        return f"{nature}\n\n{effect}"

    if source_key == "speech_voice":
        nature = "**Nature of Audio**: Human speech containing vowel vocal tract formants (300–3,000 Hz) alongside high-frequency unvoiced consonant fricatives ('s', 'sh', 'f', 'th') reaching 5–8 kHz."
        if current_sr >= 16000:
            effect = f"**Current Effect ({current_sr:,} Hz / {nyq_khz:.1f} kHz Nyquist)**: Natural, broadcast-quality voice reproduction with crisp, clear consonant pronunciation."
        elif current_sr >= 8000:
            effect = f"**Current Effect ({current_sr:,} Hz / {nyq_khz:.1f} kHz Nyquist)**: Vowel formants are preserved ensuring 100% speech intelligibility, but fricatives soften—explaining why global telecom networks standardized on 8 kHz to save over 80% bandwidth."
        else:
            effect = f"**Current Effect ({current_sr:,} Hz / {nyq_khz:.1f} kHz Nyquist)**: Heavy bandwidth reduction causes phonetic ambiguity (confusing 's' with 'f'), characteristic of military walkie-talkies."
        return f"{nature}\n\n{effect}"

    if source_key == "solo_trumpet":
        nature = "**Nature of Audio**: Bright brass solo performance characterized by intense harmonic overtones extending beyond 12 kHz and sharp embouchure attack transients."
        if current_sr >= 44100:
            effect = f"**Current Effect ({current_sr:,} Hz / {nyq_khz:.1f} kHz Nyquist)**: Cutting brass brilliance and overtone bite are fully captured."
        elif current_sr >= 16000:
            effect = f"**Current Effect ({current_sr:,} Hz / {nyq_khz:.1f} kHz Nyquist)**: High brass edge is shaved off, making the trumpet sound warmer, closer to a flugelhorn or cornet."
        else:
            effect = f"**Current Effect ({current_sr:,} Hz / {nyq_khz:.1f} kHz Nyquist)**: Upper harmonics are completely absent, converting the vibrant trumpet into a muted, horn-like tone."
        return f"{nature}\n\n{effect}"

    if source_key == "bell":
        nature = "**Nature of Audio**: Synthetic chime generated from 7 pure mathematical sine harmonics (440 Hz, 880 Hz, 1.76 kHz, 3.52 kHz, 7.04 kHz, 11.0 kHz, 14.08 kHz)."
        effect = f"**Current Effect ({current_sr:,} Hz / {nyq_khz:.1f} kHz Nyquist)**: Look at the FFT spectrum below. Every harmonic peak located to the right of the red dashed Nyquist line ({nyq_khz:.1f} kHz) is strictly eliminated from the audio."
        return f"{nature}\n\n{effect}"

    # Default / upload
    nature = "**Nature of Audio**: Custom user-provided audio recording."
    effect = f"**Current Effect ({current_sr:,} Hz / {nyq_khz:.1f} kHz Nyquist)**: Fourier sinc anti-aliasing removes all frequency components above {nyq_khz:.1f} kHz. Observe the discrete stem markers spreading farther apart as the sampling period ($T_s = 1/f_s$) increases."
    return f"{nature}\n\n{effect}"


def create_takeaway(
    source_key: str | float = "jazz_vibes",
    nyquist_hz: float = 22050.0,
    current_sr: int = 44100,
) -> mo.Html:
    """Generates a balanced 2-column educational callout explaining the Nyquist rule and audio-specific insights."""
    if isinstance(source_key, (int, float)):
        nyquist_hz = float(source_key)
        source_key = "jazz_vibes"

    nyq_khz = nyquist_hz / 1000.0
    insights = get_audio_insights(str(source_key), nyquist_hz, current_sr)

    observations_col = mo.vstack([
        mo.md("**Auditory & Visual Observations**"),
        mo.md(insights),
    ], gap=0.2)

    math_col = mo.vstack([
        mo.md("**Mathematical Foundation**"),
        mo.md(
            f"""
            To capture a sound wave cleanly without distortion (aliasing), you need at least **2 sample points** per wave cycle. The highest pitch recorded is always **half the sampling rate**:

            $$f_{{\\text{{max}}}} = \\frac{{f_s}}{{2}} = \\mathbf{{{nyq_khz:.1f}\\text{{ kHz}}}}$$

            Lowering $f_s$ spreads the discrete sample dots ($T_s = 1/f_s$) farther apart in time on the waveform.
            """
        ),
    ], gap=0.2)

    # Use widths=[4, 6] to align with the top 2-column section:
    # Left (40%): Audio Source observations
    # Right (60%): Mathematical foundation & Nyquist cutoff
    columns = mo.hstack(
        [observations_col, math_col],
        widths=[4, 6],
        gap=1.5,
        align="start",
    )

    return mo.callout(
        columns,
        kind="neutral",
    )


def create_dashboard_layout(
    left_column: mo.Html,
    right_column: mo.Html,
    takeaway_box: mo.Html,
) -> mo.Html:
    """Arranges the dashboard into a 2-column top section with a matching 2-column bottom section."""
    top_row = mo.hstack(
        [left_column, right_column],
        widths=[4, 6],
        gap=1.5,
        align="start",
    )
    return mo.vstack(
        [top_row, takeaway_box],
        gap=1.2,
    )
