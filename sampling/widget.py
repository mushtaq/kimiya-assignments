# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "anywidget",
#     "traitlets",
# ]
# ///

"""Frontend AnyWidget visualizer for audio sampling and Nyquist limit analysis.

Renders an interactive WebAudio player with a high-DPI responsive dual-domain canvas:
- Time Domain: Continuous waveform line + discrete stem sample points with responsive spacing.
- Frequency Domain: Real-time FFT spectrum with dynamic Nyquist cutoff marker and attenuation zone.
"""

from __future__ import annotations

import anywidget
import traitlets


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
            <div class="audio-player" style="
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 14px 16px;
                color: #0f172a;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
            ">
                <!-- Transport & Info Toolbar -->
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 10px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <button class="play-btn" style="
                            background: #0f172a;
                            color: #ffffff;
                            border: none;
                            border-radius: 5px;
                            padding: 6px 14px;
                            font-size: 12.5px;
                            font-weight: 500;
                            cursor: pointer;
                            display: inline-flex;
                            align-items: center;
                            gap: 6px;
                            transition: background 0.15s ease;
                        ">
                            <svg class="play-icon" viewBox="0 0 24 24" width="12" height="12" fill="currentColor">
                                <polygon points="6 4 20 12 6 20 6 4"></polygon>
                            </svg>
                            <span class="play-label">Play</span>
                        </button>
                        <span class="time-readout" style="font-family: ui-monospace, SFMono-Regular, monospace; font-size: 12px; color: #64748b; font-weight: 500;">0:00.0 / 0.00s</span>
                    </div>

                    <div style="display: flex; align-items: center; gap: 8px; font-size: 12px; color: #475569; background: #f8fafc; padding: 4px 10px; border-radius: 5px; border: 1px solid #e2e8f0;">
                        <span class="clip-title" style="color: #334155; font-weight: 500; max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">Audio</span>
                        <span style="color: #cbd5e1;">|</span>
                        <span style="font-family: ui-monospace, monospace; color: #0f172a;"><strong class="rate-val">--</strong> Hz</span>
                        <span style="color: #cbd5e1;">|</span>
                        <span style="font-family: ui-monospace, monospace; color: #dc2626;">Nyquist: <strong class="nyquist-val">--</strong> kHz</span>
                    </div>
                </div>

                <!-- High-DPI Dual Domain Visualizer Canvas -->
                <div style="position: relative; width: 100%; height: 250px; background: #f8fafc; border-radius: 6px; border: 1px solid #e2e8f0; overflow: hidden;">
                    <canvas class="viz-canvas" style="width: 100%; height: 100%; display: block;"></canvas>
                </div>

                <div style="display: flex; justify-content: space-between; margin-top: 6px; font-size: 10.5px; color: #64748b; font-family: ui-monospace, monospace; padding: 0 2px;">
                    <span>Top: Waveform & Discrete Stems</span>
                    <span>Bottom: FFT Spectrum & Nyquist Cutoff</span>
                </div>
            </div>
            `;

            const playBtn = el.querySelector('.play-btn');
            const playIcon = el.querySelector('.play-icon');
            const playLabel = el.querySelector('.play-label');
            const timeReadout = el.querySelector('.time-readout');
            const clipTitle = el.querySelector('.clip-title');
            const rateVal = el.querySelector('.rate-val');
            const nyquistVal = el.querySelector('.nyquist-val');
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

            function resizeCanvasToDisplaySize() {
                const dpr = window.devicePixelRatio || 1;
                const rect = canvas.getBoundingClientRect();
                const displayW = Math.round(rect.width);
                const displayH = Math.round(rect.height);

                if (displayW > 0 && displayH > 0) {
                    const requiredW = Math.round(displayW * dpr);
                    const requiredH = Math.round(displayH * dpr);
                    if (canvas.width !== requiredW || canvas.height !== requiredH) {
                        canvas.width = requiredW;
                        canvas.height = requiredH;
                    }
                }
            }

            const resizeObserver = new ResizeObserver(() => {
                resizeCanvasToDisplaySize();
                drawFrame();
            });
            resizeObserver.observe(canvas);

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

            function updateLabels() {
                const sr = model.get('sr') || 48000;
                const nyq = model.get('nyquist_hz') || 24000;
                const dur = model.get('duration_s') || 3.0;
                const title = model.get('clip_name') || 'Harmonic Bell';

                rateVal.textContent = sr.toLocaleString();
                nyquistVal.textContent = (nyq / 1000).toFixed(1);
                clipTitle.textContent = title;
                timeReadout.textContent = '0:00.0 / ' + dur.toFixed(2) + 's';
            }

            function updatePlayButtonUi() {
                if (state.isPlaying) {
                    playBtn.style.background = '#dc2626';
                    playIcon.innerHTML = '<rect x="5" y="4" width="4" height="16"></rect><rect x="15" y="4" width="4" height="16"></rect>';
                    playLabel.textContent = 'Stop';
                } else {
                    playBtn.style.background = '#0f172a';
                    playIcon.innerHTML = '<polygon points="6 4 20 12 6 20 6 4"></polygon>';
                    playLabel.textContent = 'Play';
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

                updatePlayButtonUi();
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
                updatePlayButtonUi();

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
                updateLabels();
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
                resizeCanvasToDisplaySize();

                const dpr = window.devicePixelRatio || 1;
                const w = canvas.width / dpr;
                const h = canvas.height / dpr;
                if (w <= 0 || h <= 0) return;

                ctx.save();
                ctx.scale(dpr, dpr);
                ctx.clearRect(0, 0, w, h);

                const activeSampleRate = model.get('sr') || 48000;
                const nyquistFreq = model.get('nyquist_hz') || 24000.0;
                const clipDuration = model.get('duration_s') || 3.0;

                const paneH = Math.floor(h / 2);

                // Background
                ctx.fillStyle = '#f8fafc';
                ctx.fillRect(0, 0, w, h);

                // Divider line between panes
                ctx.strokeStyle = '#e2e8f0';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(0, paneH);
                ctx.lineTo(w, paneH);
                ctx.stroke();

                // Progress readout
                if (state.isPlaying && state.audioCtx) {
                    const elapsed = (state.audioCtx.currentTime - state.startTime) % clipDuration;
                    const min = Math.floor(elapsed / 60);
                    const sec = (elapsed % 60).toFixed(1).padStart(4, '0');
                    timeReadout.textContent = min + ':' + sec + ' / ' + clipDuration.toFixed(2) + 's';
                }

                // ==========================================
                // 1. TOP PANE: TIME DOMAIN (Wave & Stems)
                // ==========================================
                const midY = paneH / 2;

                // Centerline
                ctx.strokeStyle = '#edf2f7';
                ctx.lineWidth = 1;
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
                        timeData[i] = 128 + Math.round(30 * Math.sin(i * 0.06) + 12 * Math.sin(i * 0.18));
                    }
                }

                // Continuous reconstructed waveform
                ctx.strokeStyle = '#94a3b8';
                ctx.lineWidth = 1.6;
                ctx.beginPath();
                const sliceWidth = w / timeData.length;
                let x = 0;
                for (let i = 0; i < timeData.length; i++) {
                    const v = timeData[i] / 128.0;
                    const y = (v - 1.0) * (midY * 0.80) + midY;
                    if (i === 0) ctx.moveTo(x, y);
                    else ctx.lineTo(x, y);
                    x += sliceWidth;
                }
                ctx.stroke();

                // Discrete sample stems & dots
                const stemInterval = Math.max(2, Math.round((48000 / activeSampleRate) * 3));
                ctx.fillStyle = '#2563eb';
                ctx.strokeStyle = 'rgba(37, 99, 235, 0.45)';
                ctx.lineWidth = 1.4;

                for (let i = 0; i < timeData.length; i += stemInterval) {
                    const px = i * sliceWidth;
                    const v = timeData[i] / 128.0;
                    const py = (v - 1.0) * (midY * 0.80) + midY;

                    ctx.beginPath();
                    ctx.moveTo(px, midY);
                    ctx.lineTo(px, py);
                    ctx.stroke();

                    ctx.beginPath();
                    ctx.arc(px, py, 2.4, 0, Math.PI * 2);
                    ctx.fill();
                }

                // Top Pane Badge
                ctx.fillStyle = '#64748b';
                ctx.font = '10.5px ui-monospace, SFMono-Regular, monospace';
                ctx.fillText('Oscilloscope (Sample Stems)', 10, 16);

                // ==========================================
                // 2. BOTTOM PANE: FREQUENCY DOMAIN (FFT & Nyquist)
                // ==========================================
                const specY = paneH;
                const specH = paneH;
                const freqData = new Uint8Array(state.analyser ? state.analyser.frequencyBinCount : 512);
                if (state.analyser && state.isPlaying) {
                    state.analyser.getByteFrequencyData(freqData);
                }

                const nyqFrac = Math.min(1.0, nyquistFreq / 24000.0);
                const nyqX = Math.round(nyqFrac * w);

                // Shaded attenuation cutoff zone
                ctx.fillStyle = 'rgba(225, 29, 72, 0.06)';
                ctx.fillRect(nyqX, specY, w - nyqX, specH);

                // Frequency bars
                const numBars = Math.min(140, Math.floor(w / 4));
                const barW = Math.max(2, (w / numBars) - 1.2);
                for (let i = 0; i < numBars; i++) {
                    const bin = Math.floor(i * (freqData.length / numBars));
                    const val = freqData[bin] || (state.isPlaying ? 0 : Math.max(0, Math.round(150 * Math.exp(-i * 0.035))));
                    const bH = (val / 255.0) * (specH - 26);
                    const bx = i * (barW + 1.2);
                    const by = h - bH - 4;

                    ctx.fillStyle = (bx < nyqX) ? '#3b82f6' : '#cbd5e1';
                    ctx.fillRect(bx, by, barW, bH);
                }

                // Dashed Nyquist limit line
                ctx.strokeStyle = '#dc2626';
                ctx.setLineDash([4, 3]);
                ctx.lineWidth = 1.6;
                ctx.beginPath();
                ctx.moveTo(nyqX, specY);
                ctx.lineTo(nyqX, h);
                ctx.stroke();
                ctx.setLineDash([]);

                // Nyquist tag
                ctx.fillStyle = '#dc2626';
                ctx.font = 'bold 10.5px ui-monospace, SFMono-Regular, monospace';
                const tagX = Math.max(8, Math.min(w - 150, nyqX + 8));
                ctx.fillText('Nyquist: ' + (nyquistFreq / 1000.0).toFixed(1) + ' kHz', tagX, specY + 18);

                // Spectrum labels
                ctx.fillStyle = '#94a3b8';
                ctx.font = '10px ui-monospace, SFMono-Regular, monospace';
                ctx.fillText('0 Hz', 10, h - 6);
                ctx.fillText('12 kHz', Math.floor(w / 2) - 16, h - 6);
                ctx.fillText('24 kHz', w - 46, h - 6);

                ctx.restore();
            }

            onDataChange();
            updatePlayButtonUi();
            setTimeout(() => {
                resizeCanvasToDisplaySize();
                drawFrame();
            }, 60);

            return () => {
                resizeObserver.disconnect();
                if (state.animId) cancelAnimationFrame(state.animId);
                if (state.timerId) clearInterval(state.timerId);
            };
        }
    };
    """
