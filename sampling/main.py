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

"""Digital Audio Sampling.

Composed Marimo application that orchestrates:
- Pure Python DSP math (`dsp.py`)
- Audio I/O, preset management, and WAV serialization (`sound.py`)
- WebAudio / Canvas AnyWidget visualizer (`widget.py`)
- Reusable UI cards and layouts (`ui.py`)
"""

import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="Audio Sampling")


@app.cell(hide_code=True)
def imports():
    import marimo as mo
    import dsp
    import sound
    import ui
    from widget import AudioSamplingPlayer

    return AudioSamplingPlayer, dsp, mo, sound, ui


@app.cell(hide_code=True)
def source_control(ui):
    source_select = ui.create_source_dropdown()
    audio_upload = ui.create_audio_upload()
    return audio_upload, source_select


@app.cell(hide_code=True)
def load_source_audio(audio_upload, sound, source_select):
    raw_content = audio_upload.contents() if audio_upload.value else None
    uploaded_name = audio_upload.name() if audio_upload.value else None
    source_audio, source_sr, source_name = sound.load_preset_or_upload(
        source_select.value,
        raw_content,
        uploaded_name,
    )
    return source_audio, source_name, source_sr


@app.cell(hide_code=True)
def rate_control(source_sr, ui):
    rate_select = ui.create_rate_radio(source_sr)
    return (rate_select,)


@app.cell(hide_code=True)
def player_init(AudioSamplingPlayer, mo):
    player_widget = mo.ui.anywidget(AudioSamplingPlayer())
    return (player_widget,)


@app.cell(hide_code=True)
def process_audio(
    dsp,
    player_widget,
    rate_select,
    sound,
    source_audio,
    source_name,
    source_sr,
):
    target_sr = rate_select.value if rate_select.value else source_sr
    resampled_audio, actual_sr = dsp.resample_audio(source_audio, source_sr, target_sr)

    meta_res = dsp.compute_audio_metrics(resampled_audio, actual_sr)
    wav_b64 = sound.audio_to_base64_wav(resampled_audio, actual_sr)

    # Directly synchronize AnyWidget traitlets without remounting DOM
    player_widget.widget.b64_data = wav_b64
    player_widget.widget.sr = meta_res["sampling_rate"]
    player_widget.widget.nyquist_hz = meta_res["nyquist_hz"]
    player_widget.widget.duration_s = meta_res["duration_s"]
    player_widget.widget.clip_name = source_name
    return (meta_res,)


@app.cell(hide_code=True)
def app_view(
    audio_upload,
    meta_res,
    mo,
    player_widget,
    rate_select,
    source_select,
    ui,
):
    header = ui.create_header()
    controls_card = ui.create_controls_card(source_select, audio_upload, rate_select)
    takeaway_box = ui.create_takeaway(meta_res["nyquist_hz"])

    left_column = mo.vstack([
        header,
        controls_card,
    ], gap=1.0)

    right_column = player_widget

    dashboard = ui.create_dashboard_layout(left_column, right_column, takeaway_box)
    dashboard
    return


if __name__ == "__main__":
    app.run()
