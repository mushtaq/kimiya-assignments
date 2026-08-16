# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "anywidget",
#     "marimo",
#     "numpy",
#     "scipy",
#     "soundfile",
#     "traitlets",
# ]
# ///

"""Digital Audio Sampling & The Nyquist Principle.

Composed Marimo application that orchestrates:
- Pure Python DSP math (`dsp.py`)
- WebAudio / Canvas AnyWidget visualizer (`widget.py`)
- Reusable UI cards and layouts (`ui.py`)
"""

import marimo

__generated_with = "0.23.16"
app = marimo.App(
    width="medium",
    app_title="Audio Sampling & The Nyquist Principle",
)


@app.cell(hide_code=True)
def imports():
    return


@app.cell(hide_code=True)
def controls():
    return


@app.cell(hide_code=True)
def player_init():
    return


@app.cell(hide_code=True)
def process_audio():
    return


@app.cell(hide_code=True)
def app_view():
    return


if __name__ == "__main__":
    app.run()
