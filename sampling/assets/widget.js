/**
 * AudioSamplingPlayer AnyWidget ES Module.
 * Visualizes audio discretization (waveform + stems) and Nyquist cutoff (FFT spectrum) in WebAudio.
 * Maintains continuous, seamless playback across sampling rate changes and file uploads.
 */

if (!window.__marimo_audio_session) {
  window.__marimo_audio_session = {
    audioCtx: null,
    analyser: null,
    sourceNode: null,
    isPlaying: false,
    startTime: 0,
    pauseOffset: 0,
    currentClipName: "",
    audioBuffer: null,
    activeWidgetId: 0,
  };
}

const session = window.__marimo_audio_session;

function getAudioContext() {
  if (!session.audioCtx) {
    const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
    session.audioCtx = new AudioCtxClass();
    session.analyser = session.audioCtx.createAnalyser();
    session.analyser.fftSize = 1024;
    session.analyser.smoothingTimeConstant = 0.8;
    session.analyser.connect(session.audioCtx.destination);
  }
  if (session.audioCtx.state === "suspended") {
    session.audioCtx.resume();
  }
  return session.audioCtx;
}

function b64ToArrayBuffer(b64) {
  const cleanB64 = b64.replace(/^data:audio\/[a-z]+;base64,/, "");
  const binaryString = window.atob(cleanB64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
}

function render({ model, el }) {
  const widgetId = ++session.activeWidgetId;
  let animId = null;

  el.innerHTML = `
    <div class="audio-player-card">
      <div class="ap-toolbar">
        <div class="ap-transport-group">
          <button class="ap-play-btn" type="button">
            <svg class="ap-play-icon" viewBox="0 0 24 24" width="12" height="12" fill="currentColor">
              <polygon points="6 4 20 12 6 20 6 4"></polygon>
            </svg>
            <span class="ap-play-label">Play</span>
          </button>
          <span class="ap-time-readout">0:00.0 / 0.00s</span>
        </div>

        <div class="ap-meta-pill">
          <span class="ap-clip-title">Audio</span>
          <span class="ap-divider-bar">|</span>
          <span><strong class="ap-rate-val">--</strong> Hz</span>
          <span class="ap-divider-bar">|</span>
          <span class="ap-nyquist-badge">Nyquist: <strong class="ap-nyquist-val">--</strong> kHz</span>
        </div>
      </div>

      <div class="ap-canvas-container">
        <canvas class="ap-viz-canvas"></canvas>
      </div>

      <div class="ap-footer-legend">
        <span>Top: Reconstructed Waveform & Discrete Stems</span>
        <span>Bottom: FFT Spectrum & Nyquist Attenuation</span>
      </div>
    </div>
  `;

  const card = el.querySelector(".audio-player-card");
  const playBtn = el.querySelector(".ap-play-btn");
  const playIcon = el.querySelector(".ap-play-icon");
  const playLabel = el.querySelector(".ap-play-label");
  const timeReadout = el.querySelector(".ap-time-readout");
  const clipTitle = el.querySelector(".ap-clip-title");
  const rateVal = el.querySelector(".ap-rate-val");
  const nyquistVal = el.querySelector(".ap-nyquist-val");
  const canvas = el.querySelector(".ap-viz-canvas");
  const ctx = canvas.getContext("2d");

  function getThemeColors() {
    const style = getComputedStyle(card);
    return {
      bg: style.getPropertyValue("--ap-canvas-bg").trim() || "#f8fafc",
      divider: style.getPropertyValue("--ap-canvas-divider").trim() || "#e2e8f0",
      waveform: style.getPropertyValue("--ap-waveform").trim() || "#94a3b8",
      stem: style.getPropertyValue("--ap-stem").trim() || "#2563eb",
      stemAlpha: style.getPropertyValue("--ap-stem-alpha").trim() || "rgba(37, 99, 235, 0.45)",
      fftActive: style.getPropertyValue("--ap-fft-active").trim() || "#3b82f6",
      fftCut: style.getPropertyValue("--ap-fft-cut").trim() || "#cbd5e1",
      nyquist: style.getPropertyValue("--ap-nyquist").trim() || "#dc2626",
      nyquistZone: style.getPropertyValue("--ap-nyquist-zone").trim() || "rgba(225, 29, 72, 0.06)",
      textMuted: style.getPropertyValue("--ap-text-muted").trim() || "#64748b",
    };
  }

  function resizeCanvasToDisplaySize() {
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const displayW = Math.round(rect.width);
    const displayH = Math.round(rect.height);

    if (displayW > 0 && displayH > 0) {
      const targetW = Math.round(displayW * dpr);
      const targetH = Math.round(displayH * dpr);
      if (canvas.width !== targetW || canvas.height !== targetH) {
        canvas.width = targetW;
        canvas.height = targetH;
      }
    }
  }

  const resizeObserver = new ResizeObserver(() => {
    resizeCanvasToDisplaySize();
    drawFrame();
  });
  resizeObserver.observe(canvas);

  function updateLabels() {
    const sr = model.get("sr") || 48000;
    const nyq = model.get("nyquist_hz") || 24000;
    const dur = model.get("duration_s") || 3.0;
    const title = model.get("clip_name") || "Harmonic Bell";

    rateVal.textContent = sr.toLocaleString();
    nyquistVal.textContent = (nyq / 1000).toFixed(1);
    clipTitle.textContent = title;
    timeReadout.textContent = `0:00.0 / ${dur.toFixed(2)}s`;
  }

  function updatePlayButtonUi() {
    if (session.isPlaying) {
      playBtn.classList.add("is-playing");
      playIcon.innerHTML = `<rect x="5" y="4" width="4" height="16"></rect><rect x="15" y="4" width="4" height="16"></rect>`;
      playLabel.textContent = "Stop";
    } else {
      playBtn.classList.remove("is-playing");
      playIcon.innerHTML = `<polygon points="6 4 20 12 6 20 6 4"></polygon>`;
      playLabel.textContent = "Play";
    }
  }

  function loadBuffer(callback) {
    const b64 = model.get("b64_data");
    if (!b64) return;
    const actx = getAudioContext();
    const arrayBuf = b64ToArrayBuffer(b64);
    actx.decodeAudioData(
      arrayBuf,
      (decoded) => {
        session.audioBuffer = decoded;
        if (callback) callback();
      },
      (err) => {
        console.error("Audio decode error:", err);
      }
    );
  }

  function startPlayback(preserveOffset = true) {
    const actx = getAudioContext();
    if (session.sourceNode) {
      try { session.sourceNode.stop(); } catch (_) {}
      try { session.sourceNode.disconnect(); } catch (_) {}
      session.sourceNode = null;
    }
    if (!session.audioBuffer) return;

    session.sourceNode = actx.createBufferSource();
    session.sourceNode.buffer = session.audioBuffer;
    session.sourceNode.loop = true;
    session.sourceNode.connect(session.analyser);

    const dur = session.audioBuffer.duration || 1.0;
    let offset = 0;
    if (preserveOffset) {
      const elapsed = session.isPlaying
        ? ((actx.currentTime - session.startTime) % dur)
        : (session.pauseOffset % dur);
      offset = elapsed >= 0 && elapsed < dur ? elapsed : 0;
    }

    session.startTime = actx.currentTime - offset;
    session.sourceNode.start(0, offset);
    session.isPlaying = true;
    session.currentClipName = model.get("clip_name") || "";

    updatePlayButtonUi();
    if (animId) cancelAnimationFrame(animId);
    loopVisualizer();
  }

  function stopPlayback() {
    if (session.sourceNode) {
      try { session.sourceNode.stop(); } catch (_) {}
      try { session.sourceNode.disconnect(); } catch (_) {}
      session.sourceNode = null;
    }
    const dur = model.get("duration_s") || 3.0;
    if (session.audioCtx) {
      session.pauseOffset = (session.audioCtx.currentTime - session.startTime) % dur;
    }
    session.isPlaying = false;
    updatePlayButtonUi();

    if (animId) {
      cancelAnimationFrame(animId);
      animId = null;
    }
    drawFrame();
  }

  playBtn.onclick = () => {
    if (session.isPlaying) {
      stopPlayback();
    } else {
      if (!session.audioBuffer) {
        loadBuffer(() => startPlayback(false));
      } else {
        startPlayback(true);
      }
    }
  };

  function onDataChange() {
    updateLabels();
    const clipName = model.get("clip_name") || "";
    const isNewClip = session.currentClipName && session.currentClipName !== clipName;

    loadBuffer(() => {
      if (session.isPlaying) {
        // Continue playback seamlessly across sampling rate changes or new clips
        startPlayback(!isNewClip);
      } else {
        drawFrame();
      }
    });
  }

  model.on("change:b64_data", onDataChange);
  model.on("change:sr", onDataChange);
  model.on("change:nyquist_hz", onDataChange);
  model.on("change:duration_s", onDataChange);
  model.on("change:clip_name", onDataChange);

  function loopVisualizer() {
    if (!session.isPlaying) return;
    drawFrame();
    animId = requestAnimationFrame(loopVisualizer);
  }

  function drawFrame() {
    if (!canvas || !ctx) return;
    resizeCanvasToDisplaySize();

    const dpr = window.devicePixelRatio || 1;
    const w = canvas.width / dpr;
    const h = canvas.height / dpr;
    if (w <= 0 || h <= 0) return;

    const colors = getThemeColors();
    const activeSampleRate = model.get("sr") || 48000;
    const nyquistFreq = model.get("nyquist_hz") || 24000.0;
    const clipDuration = model.get("duration_s") || 3.0;

    ctx.save();
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, h);

    // Canvas Background
    ctx.fillStyle = colors.bg;
    ctx.fillRect(0, 0, w, h);

    const paneH = Math.floor(h / 2);

    // Divider Line between Panes
    ctx.strokeStyle = colors.divider;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, paneH);
    ctx.lineTo(w, paneH);
    ctx.stroke();

    // Progress Readout during playback
    if (session.isPlaying && session.audioCtx) {
      const elapsed = (session.audioCtx.currentTime - session.startTime) % clipDuration;
      const min = Math.floor(elapsed / 60);
      const sec = (elapsed % 60).toFixed(1).padStart(4, "0");
      timeReadout.textContent = `${min}:${sec} / ${clipDuration.toFixed(2)}s`;
    }

    // ============================================================
    // 1. TOP PANE: TIME DOMAIN (Continuous Waveform & Sample Stems)
    // ============================================================
    const midY = paneH / 2;

    // Center Baseline
    ctx.strokeStyle = colors.divider;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, midY);
    ctx.lineTo(w, midY);
    ctx.stroke();

    const timeData = new Uint8Array(session.analyser ? session.analyser.fftSize : 1024);
    if (session.analyser && session.isPlaying) {
      session.analyser.getByteTimeDomainData(timeData);
    } else if (session.audioBuffer) {
      // Clean ~25ms initial oscilloscope window
      const channelData = session.audioBuffer.getChannelData(0);
      const windowSamples = Math.min(channelData.length, Math.floor(session.audioBuffer.sampleRate * 0.025));
      const step = windowSamples / timeData.length;
      for (let i = 0; i < timeData.length; i++) {
        const sample = channelData[Math.floor(i * step)] || 0;
        timeData[i] = Math.round((sample + 1.0) * 127.5);
      }
    } else {
      for (let i = 0; i < timeData.length; i++) {
        timeData[i] = 128 + Math.round(35 * Math.sin(i * 0.06) + 15 * Math.sin(i * 0.18));
      }
    }

    // Continuous reconstructed waveform
    ctx.strokeStyle = colors.waveform;
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    const sliceWidth = w / timeData.length;
    let x = 0;
    for (let i = 0; i < timeData.length; i++) {
      const v = timeData[i] / 128.0;
      const y = (v - 1.0) * (midY * 0.82) + midY;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
      x += sliceWidth;
    }
    ctx.stroke();

    // Discrete sample stems & stem points (stem density reflects sampling rate)
    const stemInterval = Math.max(2, Math.round((48000 / activeSampleRate) * 3));
    ctx.fillStyle = colors.stem;
    ctx.strokeStyle = colors.stemAlpha;
    ctx.lineWidth = 1.4;

    for (let i = 0; i < timeData.length; i += stemInterval) {
      const px = i * sliceWidth;
      const v = timeData[i] / 128.0;
      const py = (v - 1.0) * (midY * 0.82) + midY;

      // Stem line from centerline
      ctx.beginPath();
      ctx.moveTo(px, midY);
      ctx.lineTo(px, py);
      ctx.stroke();

      // Stem dot marker
      ctx.beginPath();
      ctx.arc(px, py, 2.5, 0, Math.PI * 2);
      ctx.fill();
    }

    // Top Pane Label
    ctx.fillStyle = colors.textMuted;
    ctx.font = "10.5px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace";
    ctx.fillText("Oscilloscope (Discretized Stems)", 10, 16);

    // ============================================================
    // 2. BOTTOM PANE: FREQUENCY DOMAIN (FFT & Nyquist Attenuation)
    // ============================================================
    const specY = paneH;
    const specH = paneH;
    const freqData = new Uint8Array(session.analyser ? session.analyser.frequencyBinCount : 512);
    if (session.analyser && session.isPlaying) {
      session.analyser.getByteFrequencyData(freqData);
    }

    const maxBandwidth = session.audioCtx ? (session.audioCtx.sampleRate / 2.0) : 24000.0;
    const nyqFrac = Math.min(1.0, Math.max(0.0, nyquistFreq / maxBandwidth));
    const nyqX = Math.round(nyqFrac * w);

    // Shaded attenuation zone for frequencies exceeding Nyquist
    ctx.fillStyle = colors.nyquistZone;
    ctx.fillRect(nyqX, specY, w - nyqX, specH);

    // Frequency spectrum bars
    const numBars = Math.min(140, Math.floor(w / 4));
    const barW = Math.max(2, (w / numBars) - 1.2);

    for (let i = 0; i < numBars; i++) {
      const bin = Math.floor(i * (freqData.length / numBars));
      const val = freqData[bin] || (session.isPlaying ? 0 : Math.max(0, Math.round(140 * Math.exp(-i * 0.04))));
      const bH = (val / 255.0) * (specH - 26);
      const bx = i * (barW + 1.2);
      const by = h - bH - 4;

      ctx.fillStyle = (bx < nyqX) ? colors.fftActive : colors.fftCut;
      ctx.fillRect(bx, by, barW, bH);
    }

    // Dashed Nyquist frequency line
    ctx.strokeStyle = colors.nyquist;
    ctx.setLineDash([4, 3]);
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    ctx.moveTo(nyqX, specY);
    ctx.lineTo(nyqX, h);
    ctx.stroke();
    ctx.setLineDash([]);

    // Nyquist Frequency annotation
    ctx.fillStyle = colors.nyquist;
    ctx.font = "bold 10.5px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace";
    const tagX = Math.max(8, Math.min(w - 155, nyqX + 8));
    ctx.fillText(`Nyquist: ${(nyquistFreq / 1000.0).toFixed(1)} kHz`, tagX, specY + 18);

    // Spectrum scale labels
    ctx.fillStyle = colors.textMuted;
    ctx.font = "10px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace";
    ctx.fillText("0 Hz", 10, h - 6);
    ctx.fillText(`${(maxBandwidth / 2000.0).toFixed(0)} kHz`, Math.floor(w / 2) - 16, h - 6);
    ctx.fillText(`${(maxBandwidth / 1000.0).toFixed(0)} kHz`, w - 46, h - 6);

    ctx.restore();
  }

  // Initial load and mounting
  updateLabels();
  updatePlayButtonUi();
  loadBuffer(() => {
    if (session.isPlaying) {
      startPlayback(true);
    } else {
      drawFrame();
    }
  });

  setTimeout(() => {
    resizeCanvasToDisplaySize();
    drawFrame();
  }, 60);

  // Clean unmount teardown
  return () => {
    resizeObserver.disconnect();
    if (animId) cancelAnimationFrame(animId);
    model.off("change:b64_data", onDataChange);
    model.off("change:sr", onDataChange);
    model.off("change:nyquist_hz", onDataChange);
    model.off("change:duration_s", onDataChange);
    model.off("change:clip_name", onDataChange);
  };
}

export default { render };
