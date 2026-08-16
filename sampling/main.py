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
    import marimo as mo
    import dsp
    import ui
    from widget import AudioSamplingPlayer

    return AudioSamplingPlayer, dsp, mo, ui


@app.cell(hide_code=True)
def controls(ui):
    audio_upload, rate_select = ui.create_controls()
    return audio_upload, rate_select


@app.cell(hide_code=True)
def process_audio(audio_upload, dsp, rate_select):
    raw_content = audio_upload.contents() if audio_upload.value else None
    uploaded_name = audio_upload.name() if audio_upload.value else None
    source_audio, source_sr, source_name = dsp.load_audio_data(raw_content, uploaded_name)

    target_sr = rate_select.value if rate_select.value else source_sr
    resampled_audio, actual_sr = dsp.resample_audio(source_audio, source_sr, target_sr)

    meta_orig = dsp.compute_audio_metrics(source_audio, source_sr)
    meta_res = dsp.compute_audio_metrics(resampled_audio, actual_sr)
    wav_b64 = dsp.audio_to_base64_wav(resampled_audio, actual_sr)
    return meta_orig, meta_res, source_name, wav_b64


@app.cell(hide_code=True)
def app_view(
    AudioSamplingPlayer,
    audio_upload,
    meta_orig,
    meta_res,
    mo,
    rate_select,
    source_name,
    ui,
    wav_b64,
):
    player_widget = AudioSamplingPlayer(
        b64_data=wav_b64,
        sr=meta_res["sampling_rate"],
        nyquist_hz=meta_res["nyquist_hz"],
        duration_s=meta_res["duration_s"],
        clip_name=source_name,
    )

    header = ui.create_header()
    controls_card = ui.create_controls_card(audio_upload, rate_select)
    metrics_card = ui.create_metrics_card(meta_orig, meta_res)
    takeaway_box = ui.create_takeaway(meta_res["nyquist_hz"])

    left_column = mo.vstack([
        header,
        controls_card,
        metrics_card,
    ], gap=1.0)

    right_column = mo.vstack([
        player_widget,
        takeaway_box,
    ], gap=1.0)

    dashboard = ui.create_dashboard_layout(left_column, right_column)
    dashboard
    return


if __name__ == "__main__":
    app.run()
