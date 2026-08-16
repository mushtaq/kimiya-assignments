"""Frontend AnyWidget visualizer for audio sampling and Nyquist limit analysis.

Loads external JavaScript and CSS assets for high-DPI dual-domain rendering:
- Time Domain: Continuous waveform line + discrete stem sample points.
- Frequency Domain: Real-time FFT spectrum with dynamic Nyquist cutoff marker.
"""

from __future__ import annotations

import pathlib
import anywidget
import traitlets

_ASSET_DIR = pathlib.Path(__file__).parent / "assets"


class AudioSamplingPlayer(anywidget.AnyWidget):
    """Interactive WebAudio player and dual-domain oscilloscope/spectrum visualizer."""

    _esm = _ASSET_DIR / "widget.js"
    _css = _ASSET_DIR / "widget.css"

    b64_data = traitlets.Unicode("").tag(sync=True)
    sr = traitlets.Int(48000).tag(sync=True)
    nyquist_hz = traitlets.Float(24000.0).tag(sync=True)
    duration_s = traitlets.Float(3.0).tag(sync=True)
    clip_name = traitlets.Unicode("Harmonic Bell").tag(sync=True)
