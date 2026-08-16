# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "numpy",
#     "scipy",
#     "anywidget",
#     "traitlets",
# ]
# ///

import marimo

__generated_with = "0.23.16"
app = marimo.App(
    width="medium",
    app_title="Audio Sampling & The Nyquist Principle",
)


@app.cell(hide_code=True)
def imports():
    import base64
    import io
    import anywidget
    import marimo as mo
    import numpy as np
    import scipy.io.wavfile as wav
    import scipy.signal
    import traitlets

    return anywidget, base64, io, mo, np, scipy, traitlets, wav


@app.cell(hide_code=True)
def pure_dsp_engine(base64, io, np, scipy, wav):
    def synth_educational_bell(duration_s: float = 3.0, sr: int = 48000) -> tuple[np.ndarray, int]:
        """Synthesizes a rich harmonic chime with distinct high overtones up to 14 kHz."""
        t = np.linspace(0, duration_s, int(duration_s * sr), endpoint=False)
    
        # Harmonic overtone series
        harmonics = [
            (440.0, 0.40, 1.2),    # A4 fundamental (warmth)
            (880.0, 0.28, 1.8),    # A5 octave
            (1760.0, 0.20, 2.5),   # A6 bell body
            (3520.0, 0.16, 3.2),   # A7 presence
            (7040.0, 0.12, 4.0),   # A8 brilliance / air
            (11000.0, 0.08, 5.0),  # Metallic sparkle overtone
            (14080.0, 0.06, 6.0),  # Ultra-high shimmer
        ]
    
        signal = np.zeros_like(t)
        for freq, amp, decay_rate in harmonics:
            if freq < sr / 2.0:
                env = np.exp(-decay_rate * (t % (duration_s / 2.0)))
                signal += amp * np.sin(2.0 * np.pi * freq * t) * env
            
        # Metallic transient attack
        noise = np.random.uniform(-0.1, 0.1, len(t)) * np.exp(-15.0 * (t % (duration_s / 2.0)))
        signal += noise
    
        # Smooth seamless looping crossfade
        fade_len = int(0.05 * sr)
        if fade_len > 0 and len(signal) > 2 * fade_len:
            fade_in = np.linspace(0, 1, fade_len)
            fade_out = np.linspace(1, 0, fade_len)
            signal[:fade_len] *= fade_in
            signal[-fade_len:] *= fade_out
        
        # Normalize to [-0.95, 0.95]
        max_val = np.max(np.abs(signal))
        if max_val > 0:
            signal = (signal / max_val) * 0.95
        
        return signal.astype(np.float32), sr

    def load_audio_data(raw_bytes: bytes | None, filename: str | None = None) -> tuple[np.ndarray, int, str]:
        """Loads uploaded audio or gracefully falls back to synthesized harmonic bell."""
        if raw_bytes and len(raw_bytes) > 0:
            try:
                sr, data = wav.read(io.BytesIO(raw_bytes))
                if data.ndim > 1:
                    data = data.mean(axis=1)
                if np.issubdtype(data.dtype, np.integer):
                    max_int = np.iinfo(data.dtype).max
                    audio = data.astype(np.float32) / max_int
                else:
                    audio = data.astype(np.float32)
                name = filename if filename else "Uploaded Audio"
                return audio, int(sr), name
            except Exception:
                pass
        audio, sr = synth_educational_bell(3.0, 48000)
        return audio, sr, "Default Harmonic Bell (48 kHz Reference)"

    def resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int) -> tuple[np.ndarray, int]:
        """Band-limited anti-aliased sinc resampling using Fourier method."""
        if orig_sr == target_sr:
            return audio.copy(), orig_sr
        num_target_samples = int(round(len(audio) * float(target_sr) / orig_sr))
        resampled = scipy.signal.resample(audio, num_target_samples)
        # Prevent clipping post sinc-interpolation
        resampled = np.clip(resampled, -1.0, 1.0)
        return resampled.astype(np.float32), target_sr

    def compute_audio_metrics(audio: np.ndarray, sr: int) -> dict:
        """Computes sample count, duration, raw PCM size, and theoretical Nyquist limit."""
        duration_s = float(len(audio)) / float(sr) if sr > 0 else 0.0
        pcm_kb = float(len(audio) * 2) / 1024.0  # 16-bit uncompressed PCM
        nyquist_hz = float(sr) / 2.0
        return {
            "duration_s": duration_s,
            "sample_count": len(audio),
            "sampling_rate": sr,
            "pcm_kb": pcm_kb,
            "nyquist_hz": nyquist_hz,
        }

    def audio_to_base64_wav(audio: np.ndarray, sr: int) -> str:
        """Encodes float32 audio array into standard 16-bit PCM WAV base64 data URI."""
        int16_audio = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
        buffer = io.BytesIO()
        wav.write(buffer, sr, int16_audio)
        b64_str = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:audio/wav;base64,{b64_str}"

    return (
        audio_to_base64_wav,
        compute_audio_metrics,
        load_audio_data,
        resample_audio,
    )


@app.cell(hide_code=True)
def player_widget_definition(anywidget, traitlets):
    class AudioSamplingPlayer(anywidget.AnyWidget):
        b64_data = traitlets.Unicode("").tag(sync=True)
        sr = traitlets.Int(48000).tag(sync=True)
        nyquist_hz = traitlets.Float(24000.0).tag(sync=True)
        duration_s = traitlets.Float(3.0).tag(sync=True)
        clip_name = traitlets.Unicode("Harmonic Bell").tag(sync=True)

        _esm = """
        export default {
            render({ model, el }) {
                el.innerHTML = `
                <div class="audio-player-card" style="
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #090d16;
                    border: 1px solid #1e293b;
                    border-radius: 12px;
                    padding: 20px;
                    color: #f1f5f9;
                    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
                ">
                    <!-- Control Header -->
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 10px;">
                        <div style="display: flex; align-items: center; gap: 14px;">
                            <button class="play-btn" style="
                                background: #2563eb;
                                color: #ffffff;
                                border: none;
                                border-radius: 8px;
                                padding: 9px 20px;
                                font-size: 13px;
                                font-weight: 600;
                                letter-spacing: 0.02em;
                                cursor: pointer;
                                display: inline-flex;
                                align-items: center;
                                gap: 8px;
                                transition: all 0.15s ease;
                            ">
                                <span class="play-icon" style="font-size: 11px;">&#9654;</span>
                                <span class="play-label">PLAY CONTINUOUS LOOP</span>
                            </button>
                            <div style="display: flex; flex-direction: column;">
                                <span class="time-readout" style="font-family: ui-monospace, SFMono-Regular, monospace; font-size: 12px; color: #94a3b8;">0:00.0 / 0.00s</span>
                                <span class="clip-title" style="font-size: 11px; color: #64748b;">Audio</span>
                            </div>
                        </div>

                        <div style="display: flex; gap: 8px; align-items: center;">
                            <div style="background: #131d2e; border: 1px solid #1e293b; border-radius: 6px; padding: 4px 10px; text-align: right;">
                                <div style="font-size: 9px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">Active Rate</div>
                                <div class="rate-badge" style="font-family: ui-monospace, monospace; font-size: 13px; font-weight: 600; color: #38bdf8;">-- Hz</div>
                            </div>
                            <div style="background: #1e131d; border: 1px solid #3b1d28; border-radius: 6px; padding: 4px 10px; text-align: right;">
                                <div style="font-size: 9px; color: #f43f5e; text-transform: uppercase; letter-spacing: 0.05em;">Nyquist Limit</div>
                                <div class="nyquist-badge" style="font-family: ui-monospace, monospace; font-size: 13px; font-weight: 600; color: #fb7185;">-- kHz</div>
                            </div>
                        </div>
                    </div>

                    <!-- 60fps Real-Time Canvas -->
                    <canvas class="viz-canvas" width="700" height="230" style="
                        width: 100%;
                        height: 230px;
                        background: #040711;
                        border-radius: 8px;
                        border: 1px solid #1e293b;
                        display: block;
                    "></canvas>

                    <div style="display: flex; justify-content: space-between; margin-top: 8px; font-size: 10.5px; color: #64748b; font-family: ui-monospace, monospace; flex-wrap: wrap; gap: 4px;">
                        <span>TOP: TIME-DOMAIN WAVEFORM & DISCRETE SAMPLING STEMS</span>
                        <span>BOTTOM: REAL-TIME FFT SPECTRUM & NYQUIST GATE</span>
                    </div>
                </div>
                `;

                const playBtn = el.querySelector('.play-btn');
                const playIcon = el.querySelector('.play-icon');
                const playLabel = el.querySelector('.play-label');
                const timeReadout = el.querySelector('.time-readout');
                const clipTitle = el.querySelector('.clip-title');
                const rateBadge = el.querySelector('.rate-badge');
                const nyquistBadge = el.querySelector('.nyquist-badge');
                const canvas = el.querySelector('.viz-canvas');
                const ctx = canvas.getContext('2d');

                if (!window.__marimo_audio_engine) {
                    window.__marimo_audio_engine = {
                        audioCtx: null,
                        sourceNode: null,
                        analyser: null,
                        audioBuffer: null,
                        isPlaying: false,
                        startTime: 0,
                        pauseOffset: 0,
                        animId: null,
                        timerId: null,
                    };
                }
                const state = window.__marimo_audio_engine;

                function getAudioContext() {
                    if (!state.audioCtx) {
                        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
                        state.audioCtx = new AudioContextClass();
                        state.analyser = state.audioCtx.createAnalyser();
                        state.analyser.fftSize = 1024;
                        state.analyser.smoothingTimeConstant = 0.8;
                        state.analyser.connect(state.audioCtx.destination);
                    }
                    if (state.audioCtx.state === 'suspended') {
                        state.audioCtx.resume();
                    }
                    return state.audioCtx;
                }

                function b64ToArrayBuffer(b64) {
                    const cleanB64 = b64.replace("data:audio/wav;base64,", "");
                    const binaryString = window.atob(cleanB64);
                    const len = binaryString.length;
                    const bytes = new Uint8Array(len);
                    for (let i = 0; i < len; i++) {
                        bytes[i] = binaryString.charCodeAt(i);
                    }
                    return bytes.buffer;
                }

                function updateBadges() {
                    const sr = model.get('sr') || 48000;
                    const nyq = model.get('nyquist_hz') || 24000;
                    const dur = model.get('duration_s') || 3.0;
                    const title = model.get('clip_name') || 'Harmonic Bell';

                    rateBadge.textContent = sr.toLocaleString() + ' Hz';
                    nyquistBadge.textContent = (nyq / 1000).toFixed(1) + ' kHz';
                    clipTitle.textContent = title;
                    timeReadout.textContent = '0:00.0 / ' + dur.toFixed(2) + 's';
                }

                function updateUiButton() {
                    if (state.isPlaying) {
                        playBtn.style.background = '#e11d48';
                        playIcon.innerHTML = '&#10074;&#10074;';
                        playLabel.textContent = 'STOP PLAYBACK';
                    } else {
                        playBtn.style.background = '#2563eb';
                        playIcon.innerHTML = '&#9654;';
                        playLabel.textContent = 'PLAY CONTINUOUS LOOP';
                    }
                }

                function loadBuffer(callback) {
                    const b64 = model.get('b64_data');
                    if (!b64) return;
                    const actx = getAudioContext();
                    const arrayBuf = b64ToArrayBuffer(b64);
                    actx.decodeAudioData(arrayBuf, (decoded) => {
                        state.audioBuffer = decoded;
                        if (callback) callback();
                    }, (err) => {
                        console.error('Audio decode error:', err);
                    });
                }

                function startPlayback() {
                    const actx = getAudioContext();
                    if (state.sourceNode) {
                        try { state.sourceNode.stop(); } catch(e) {}
                        try { state.sourceNode.disconnect(); } catch(e) {}
                    }
                    if (!state.audioBuffer) return;
                    state.sourceNode = actx.createBufferSource();
                    state.sourceNode.buffer = state.audioBuffer;
                    state.sourceNode.loop = true;
                    state.sourceNode.connect(state.analyser);

                    const dur = state.audioBuffer.duration || 1.0;
                    const offset = state.pauseOffset % dur;
                    state.startTime = actx.currentTime - offset;
                    state.sourceNode.start(0, offset);
                    state.isPlaying = true;

                    updateUiButton();
                    loopVisualizer();
                    if (state.timerId) clearInterval(state.timerId);
                    state.timerId = setInterval(drawFrame, 35);
                }

                function stopPlayback() {
                    if (state.sourceNode) {
                        try { state.sourceNode.stop(); } catch(e) {}
                        try { state.sourceNode.disconnect(); } catch(e) {}
                        state.sourceNode = null;
                    }
                    const dur = model.get('duration_s') || 3.0;
                    if (state.audioCtx) {
                        state.pauseOffset = (state.audioCtx.currentTime - state.startTime) % dur;
                    }
                    state.isPlaying = false;
                    updateUiButton();

                    if (state.animId) cancelAnimationFrame(state.animId);
                    if (state.timerId) clearInterval(state.timerId);
                    drawFrame();
                }

                playBtn.onclick = () => {
                    if (state.isPlaying) {
                        stopPlayback();
                    } else {
                        if (!state.audioBuffer) {
                            loadBuffer(startPlayback);
                        } else {
                            startPlayback();
                        }
                    }
                };

                function onDataChange() {
                    updateBadges();
                    loadBuffer(() => {
                        if (state.isPlaying) {
                            startPlayback();
                        } else {
                            drawFrame();
                        }
                    });
                }

                model.on('change:b64_data', onDataChange);
                model.on('change:sr', onDataChange);
                model.on('change:nyquist_hz', onDataChange);
                model.on('change:duration_s', onDataChange);
                model.on('change:clip_name', onDataChange);

                function loopVisualizer() {
                    if (!state.isPlaying) return;
                    drawFrame();
                    state.animId = requestAnimationFrame(loopVisualizer);
                }

                function drawFrame() {
                    if (!canvas || !ctx) return;
                    const w = canvas.width;
                    const h = canvas.height;
                    const hHalf = Math.floor(h / 2);
                    ctx.clearRect(0, 0, w, h);

                    const activeSampleRate = model.get('sr') || 48000;
                    const nyquistFreq = model.get('nyquist_hz') || 24000.0;
                    const clipDuration = model.get('duration_s') || 3.0;

                    ctx.fillStyle = '#040711';
                    ctx.fillRect(0, 0, w, h);

                    ctx.strokeStyle = '#1e293b';
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.moveTo(0, hHalf);
                    ctx.lineTo(w, hHalf);
                    ctx.stroke();

                    if (state.isPlaying && state.audioCtx) {
                        const elapsed = (state.audioCtx.currentTime - state.startTime) % clipDuration;
                        const min = Math.floor(elapsed / 60);
                        const sec = (elapsed % 60).toFixed(1).padStart(4, '0');
                        timeReadout.textContent = min + ':' + sec + ' / ' + clipDuration.toFixed(2) + 's';
                    }

                    // 1. TIME DOMAIN
                    const midY = hHalf / 2;
                    ctx.strokeStyle = '#0f172a';
                    ctx.beginPath();
                    ctx.moveTo(0, midY);
                    ctx.lineTo(w, midY);
                    ctx.stroke();

                    const timeData = new Uint8Array(state.analyser ? state.analyser.fftSize : 1024);
                    if (state.analyser && state.isPlaying) {
                        state.analyser.getByteTimeDomainData(timeData);
                    } else if (state.audioBuffer) {
                        const channelData = state.audioBuffer.getChannelData(0);
                        const step = Math.floor(channelData.length / timeData.length);
                        for (let i = 0; i < timeData.length; i++) {
                            const sample = channelData[i * step] || 0;
                            timeData[i] = Math.round((sample + 1.0) * 127.5);
                        }
                    } else {
                        for (let i = 0; i < timeData.length; i++) {
                            timeData[i] = 128 + Math.round(35 * Math.sin(i * 0.06) + 15 * Math.sin(i * 0.18));
                        }
                    }

                    ctx.strokeStyle = '#64748b';
                    ctx.lineWidth = 1.6;
                    ctx.beginPath();
                    const sliceWidth = w / timeData.length;
                    let x = 0;
                    for (let i = 0; i < timeData.length; i++) {
                        const v = timeData[i] / 128.0;
                        const y = (v - 1.0) * (midY * 0.85) + midY;
                        if (i === 0) ctx.moveTo(x, y);
                        else ctx.lineTo(x, y);
                        x += sliceWidth;
                    }
                    ctx.stroke();

                    const stemInterval = Math.max(1, Math.round(48000 / activeSampleRate) * 3);
                    ctx.fillStyle = '#38bdf8';
                    ctx.strokeStyle = 'rgba(56, 189, 248, 0.45)';
                    ctx.lineWidth = 1.2;

                    for (let i = 0; i < timeData.length; i += stemInterval) {
                        const px = i * sliceWidth;
                        const v = timeData[i] / 128.0;
                        const py = (v - 1.0) * (midY * 0.85) + midY;

                        ctx.beginPath();
                        ctx.moveTo(px, midY);
                        ctx.lineTo(px, py);
                        ctx.stroke();

                        ctx.beginPath();
                        ctx.arc(px, py, 2.5, 0, Math.PI * 2);
                        ctx.fill();
                    }

                    ctx.font = '10px ui-monospace, monospace';
                    ctx.fillStyle = '#94a3b8';
                    ctx.fillText('TIME SAMPLING: ' + activeSampleRate.toLocaleString() + ' SAMPLES/SEC', 12, 16);

                    // 2. FREQUENCY DOMAIN
                    const specY = hHalf;
                    const specH = hHalf;
                    const freqData = new Uint8Array(state.analyser ? state.analyser.frequencyBinCount : 512);
                    if (state.analyser && state.isPlaying) {
                        state.analyser.getByteFrequencyData(freqData);
                    }

                    const nyqFrac = Math.min(1.0, nyquistFreq / 24000.0);
                    const nyqX = Math.round(nyqFrac * w);

                    ctx.fillStyle = 'rgba(244, 63, 94, 0.08)';
                    ctx.fillRect(nyqX, specY, w - nyqX, specH);

                    const numBars = 110;
                    const barW = (w / numBars) - 1;
                    for (let i = 0; i < numBars; i++) {
                        const bin = Math.floor(i * (freqData.length / numBars));
                        const val = freqData[bin] || (state.isPlaying ? 0 : Math.max(0, Math.round(150 * Math.exp(-i * 0.04))));
                        const bH = (val / 255.0) * (specH - 26);
                        const bx = i * (barW + 1);
                        const by = h - bH - 3;

                        ctx.fillStyle = (bx < nyqX) ? '#2563eb' : '#f43f5e';
                        ctx.fillRect(bx, by, barW, bH);
                    }

                    ctx.strokeStyle = '#f43f5e';
                    ctx.setLineDash([4, 4]);
                    ctx.lineWidth = 1.6;
                    ctx.beginPath();
                    ctx.moveTo(nyqX, specY);
                    ctx.lineTo(nyqX, h);
                    ctx.stroke();
                    ctx.setLineDash([]);

                    ctx.fillStyle = '#f43f5e';
                    ctx.font = '10px ui-monospace, monospace';
                    const tagX = Math.max(12, Math.min(w - 180, nyqX + 8));
                    ctx.fillText('NYQUIST CEILING: ' + (nyquistFreq / 1000.0).toFixed(1) + ' kHz', tagX, specY + 18);

                    ctx.fillStyle = '#64748b';
                    ctx.fillText('0 Hz', 12, h - 6);
                    ctx.fillText('12 kHz', Math.floor(w / 2) - 18, h - 6);
                    ctx.fillText('24 kHz', w - 50, h - 6);
                }

                onDataChange();
                updateUiButton();
                setTimeout(drawFrame, 50);

                return () => {
                    if (state.animId) cancelAnimationFrame(state.animId);
                    if (state.timerId) clearInterval(state.timerId);
                };
            }
        };
        """

    return (AudioSamplingPlayer,)


@app.cell(hide_code=True)
def ui_controls(mo):
    audio_upload = mo.ui.file(
        filetypes=[".wav", ".mp3", ".ogg", ".flac"],
        label="Audio File (Leave empty for default clip)",
    )

    sampling_rates = {
        "4,000 Hz (Walkie-Talkie • Nyquist: 2.0 kHz)": 4000,
        "8,000 Hz (Telephone • Nyquist: 4.0 kHz)": 8000,
        "16,000 Hz (Voice Radio • Nyquist: 8.0 kHz)": 16000,
        "24,000 Hz (FM Quality • Nyquist: 12.0 kHz)": 24000,
        "44,100 Hz (Standard CD • Nyquist: 22.05 kHz)": 44100,
        "48,000 Hz (Studio HD • Nyquist: 24.0 kHz)": 48000,
    }

    rate_select = mo.ui.dropdown(
        options=sampling_rates,
        value="48,000 Hz (Studio HD • Nyquist: 24.0 kHz)",
        label="Target Sampling Rate (fs)",
    )
    return audio_upload, rate_select


@app.cell(hide_code=True)
def process_audio(
    audio_to_base64_wav,
    audio_upload,
    compute_audio_metrics,
    load_audio_data,
    rate_select,
    resample_audio,
):
    # 1. Load source audio or default harmonic chime
    raw_content = audio_upload.contents() if audio_upload.value else None
    uploaded_name = audio_upload.name() if audio_upload.value else None
    source_audio, source_sr, source_name = load_audio_data(raw_content, uploaded_name)

    # 2. Resample to selected target rate
    target_sr = rate_select.value if rate_select.value else source_sr
    resampled_audio, actual_sr = resample_audio(source_audio, source_sr, target_sr)

    # 3. Compute metrics & Base64 WAV data URI
    meta_orig = compute_audio_metrics(source_audio, source_sr)
    meta_res = compute_audio_metrics(resampled_audio, actual_sr)
    wav_b64 = audio_to_base64_wav(resampled_audio, actual_sr)
    return meta_orig, meta_res, source_name, wav_b64


@app.cell(hide_code=True)
def web_audio_player(AudioSamplingPlayer, meta_res, source_name, wav_b64):
    player_widget = AudioSamplingPlayer(
        b64_data=wav_b64,
        sr=meta_res["sampling_rate"],
        nyquist_hz=meta_res["nyquist_hz"],
        duration_s=meta_res["duration_s"],
        clip_name=source_name,
    )
    return (player_widget,)


@app.cell(hide_code=True)
def summary_and_takeaway(meta_orig, meta_res, mo):
    size_saving = (1.0 - (meta_res["pcm_kb"] / meta_orig["pcm_kb"])) * 100.0 if meta_orig["pcm_kb"] > 0 else 0.0

    metrics_card = mo.hstack([
        mo.stat(
            label="Original Audio",
            value=f"{meta_orig['sampling_rate']:,} Hz",
            caption=f"{meta_orig['duration_s']:.2f}s • {meta_orig['sample_count']:,} samples • {meta_orig['pcm_kb']:.1f} KB",
            bordered=True,
        ),
        mo.stat(
            label="Active Sample Rate",
            value=f"{meta_res['sampling_rate']:,} Hz",
            caption=f"{size_saving:.1f}% file size savings ({meta_res['pcm_kb']:.1f} KB)" if size_saving > 0 else "Full reference fidelity",
            bordered=True,
        ),
        mo.stat(
            label="Nyquist Limit (Fs / 2)",
            value=f"{meta_res['nyquist_hz']/1000.0:.1f} kHz",
            caption="Strict upper frequency threshold",
            bordered=True,
        ),
    ], widths="equal", gap=1.5)

    takeaway_box = mo.callout(
        mo.md(
            f"""
            ### 💡 The Core Intuition: Why Sample Rate Dictates Pitch & Clarity

            1. **The Nyquist Barrier ($f_\\text{{max}} = \\frac{{f_s}}{{2}} = \\mathbf{{{meta_res['nyquist_hz']/1000.0:.1f}\\text{{ kHz}}}}$):** To capture and reproduce a sound frequency $f$, digital recording requires at least **2 discrete samples per cycle** (one for the crest, one for the trough). Any frequency component above this ceiling cannot be captured and is eliminated by the anti-aliasing filter.
            2. **Acoustic & Visual Proof:** When you switch to **8,000 Hz** (Telephone) or **4,000 Hz** (Walkie-Talkie), notice how the metallic chime's airy brilliance and high sparkle disappear from the audio, while the discrete dots in the time-domain waveform visibly spread apart and the red Nyquist barrier in the spectrum drops to truncate the high frequencies!
            """
        ),
        kind="info",
    )
    return metrics_card, takeaway_box


@app.cell(hide_code=True)
def app_layout(
    audio_upload,
    metrics_card,
    mo,
    player_widget,
    rate_select,
    takeaway_box,
):
    header = mo.vstack([
        mo.md("# Digital Audio Sampling & The Nyquist Principle"),
        mo.md("Listen, visualize, and understand how digital sampling rates define frequency bandwidth and sound fidelity."),
    ], gap=0.5)

    controls_panel = mo.hstack(
        [audio_upload, rate_select],
        justify="space-between",
        align="center",
        gap=2.0,
    )

    notebook_view = mo.vstack([
        header,
        controls_panel,
        player_widget,
        metrics_card,
        takeaway_box,
    ], gap=1.5)

    notebook_view
    return


if __name__ == "__main__":
    app.run()
