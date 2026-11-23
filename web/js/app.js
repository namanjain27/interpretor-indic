import * as sarvam from "./sarvam.js";
import { decodeTo16kMono, splitAtPauses, encodeWav, concatWavs } from "./audio.js";

const $ = (id) => document.getElementById(id);
const KEY = "sarvamKey";
const PREFS = "interpreterPrefs";

// ------------------------------------------------------------ storage (never throws)

const store = {
  get(k, session = false) { try { return (session ? sessionStorage : localStorage).getItem(k); } catch { return null; } },
  set(k, v, session = false) { try { (session ? sessionStorage : localStorage).setItem(k, v); } catch {} },
  del(k) { try { localStorage.removeItem(k); sessionStorage.removeItem(k); } catch {} },
};
const getKey = () => store.get(KEY) || store.get(KEY, true);
const prefs = () => { try { return JSON.parse(store.get(PREFS)) || {}; } catch { return {}; } };
const savePrefs = (p) => store.set(PREFS, JSON.stringify({ ...prefs(), ...p }));

// ------------------------------------------------------------ screens

let pendingShared = null; // a file shared in before a key was entered

function showScreen() {
  const key = getKey();
  $("keyScreen").hidden = !!key;
  $("mainScreen").hidden = !key;
  $("settingsBtn").hidden = !key;
  $("who").textContent = key ? `Saved on this device, ending …${key.slice(-4)}` : "";
  if (key && pendingShared) { const { blob, name } = pendingShared; pendingShared = null; run(blob, name); }
}

$("keyForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const key = $("keyInput").value.trim();
  $("keyError").hidden = true;
  $("keyBtn").disabled = true;
  $("keyBtn").textContent = "Checking key…";
  try {
    await sarvam.validateKey(key);
    store.set(KEY, key, !$("remember").checked);
    $("keyInput").value = "";
    showScreen();
  } catch (err) {
    $("keyError").textContent = err.message;
    $("keyError").hidden = false;
  } finally {
    $("keyBtn").disabled = false;
    $("keyBtn").textContent = "Get started";
  }
});

$("settingsBtn").addEventListener("click", () => $("settings").showModal());
$("helpBtn").addEventListener("click", () => $("help").showModal());
for (const d of document.querySelectorAll("dialog.sheet")) {
  d.addEventListener("click", (e) => { if (e.target === d) d.close(); }); // tap backdrop to close
}

$("forgetBtn").addEventListener("click", () => {
  store.del(KEY);
  $("settings").close();
  resetResult();
  showScreen();
});

// ------------------------------------------------------------ options

const langSel = $("lang");
for (const [code, name] of Object.entries(sarvam.LANGUAGES)) langSel.add(new Option(name, code));
const p0 = prefs();
langSel.value = p0.lang || "hi-IN";
if (p0.gender) document.querySelector(`input[name=gender][value=${p0.gender}]`).checked = true;
if (p0.speak === false) $("speakToggle").checked = false;
if (p0.pace) $("pace").value = p0.pace;

const opts = () => ({
  target: langSel.value,
  gender: document.querySelector("input[name=gender]:checked").value,
  speak: $("speakToggle").checked,
  pace: parseFloat($("pace").value),
});
const updatePace = () => {
  $("paceOut").textContent = `${parseFloat($("pace").value).toFixed(2)}×`;
  $("pace").disabled = !$("speakToggle").checked;
};
updatePace();
document.addEventListener("change", (e) => {
  if (e.target.closest("#settings") || e.target === langSel) {
    const o = opts();
    savePrefs({ lang: o.target, gender: o.gender, speak: o.speak, pace: o.pace });
    updatePace();
  }
});
$("pace").addEventListener("input", updatePace);

// ------------------------------------------------------------ input: file & record

$("fileInput").addEventListener("change", (e) => {
  const f = e.target.files[0];
  e.target.value = ""; // allow picking the same file again
  if (f) run(f, f.name);
});

let recorder = null, recTimer = null;
$("recBtn").addEventListener("click", async () => {
  if (recorder) { recorder.stop(); return; }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const chunks = [];
    recorder = new MediaRecorder(stream);
    recorder.ondataavailable = (e) => e.data.size && chunks.push(e.data);
    recorder.onstop = () => {
      stream.getTracks().forEach((t) => t.stop());
      const type = recorder.mimeType || "audio/webm";
      recorder = null;
      setRecUi(false);
      const ext = type.includes("mp4") ? "m4a" : type.includes("ogg") ? "ogg" : "webm";
      run(new Blob(chunks, { type }), `recording.${ext}`);
    };
    recorder.start();
    setRecUi(true);
  } catch {
    showError("Microphone access was blocked. Allow it in your browser settings to record.");
  }
});
function setRecUi(on) {
  const btn = $("recBtn");
  btn.classList.toggle("recording", on);
  btn.querySelector("use").setAttribute("href", on ? "#i-stop" : "#i-mic");
  clearInterval(recTimer);
  if (on) {
    const t0 = Date.now();
    const tick = () => ($("recLabel").textContent = `Stop · ${fmt((Date.now() - t0) / 1000)}`);
    tick(); recTimer = setInterval(tick, 500);
  } else {
    $("recLabel").textContent = "Record";
  }
}

// ------------------------------------------------------------ pipeline

let busy = false;

async function run(blob, filename) {
  if (busy) return;
  const key = getKey();
  if (!key) { pendingShared = { blob, name: filename }; showScreen(); return; }
  busy = true;
  const o = opts();
  const t0 = performance.now();
  const timings = {};
  let mark = performance.now();
  const lap = (k) => { const now = performance.now(); timings[k] = (now - mark) / 1000; mark = now; };

  resetResult();
  startProgress(o.speak);
  try {
    setStep("listen", "active", "Preparing audio…");
    let clips;
    try {
      const samples = await decodeTo16kMono(blob);
      clips = splitAtPauses(samples).map((s, i) => ({ blob: encodeWav(s), name: `clip${i}.wav` }));
    } catch {
      clips = [{ blob, name: filename || "audio" }]; // browser can't decode it: let Sarvam try
    }
    if (!clips.length) throw new Error("This audio seems to be empty.");

    setStep("listen", "active", clips.length > 1 ? `Long note: listening to ${clips.length} parts at once…` : "Working out the language…");
    const parts = await mapLimit(clips, 4, (c) => sarvam.transcribe(key, c.blob, c.name));
    const transcript = parts.map((p) => p.transcript).filter(Boolean).join(" ");
    if (!transcript) throw new Error("No speech detected in this audio.");
    const source = dominantLanguage(parts);
    lap("listen");
    setStep("listen", "done", `Heard ${sarvam.languageName(source)}`);

    let translation = transcript;
    const skipped = source === o.target;
    if (skipped) {
      setStep("translate", "skipped", `Already in ${sarvam.languageName(o.target)}`);
    } else {
      setStep("translate", "active", `${sarvam.languageName(source)} → ${sarvam.languageName(o.target)}`);
      translation = await sarvam.translate(key, transcript, source, o.target, o.gender);
      setStep("translate", "done", `${sarvam.languageName(source)} → ${sarvam.languageName(o.target)}`);
    }
    lap("translate");
    showText(transcript, translation, source, o.target, skipped);

    if (o.speak) {
      setStep("speak", "active", `${o.gender === "male" ? "Male" : "Female"} voice`);
      const wavs = await sarvam.speak(key, translation, o.target, o.gender, o.pace);
      const wav = concatWavs(wavs);
      lap("speak");
      await showAudio(wav, filename, o.target);
    }
    const total = (performance.now() - t0) / 1000;
    const bits = [`Listened ${timings.listen.toFixed(1)}s`];
    if (!skipped) bits.push(`translated ${timings.translate.toFixed(1)}s`);
    if (timings.speak) bits.push(`voiced ${timings.speak.toFixed(1)}s`);
    $("timing").textContent = `Done in ${total.toFixed(1)}s · ${bits.join(" · ")}`;
  } catch (err) {
    showError(err.message || String(err));
  } finally {
    stopProgress();
    busy = false;
  }
}

function dominantLanguage(parts) {
  const weight = {};
  for (const p of parts) weight[p.language] = (weight[p.language] || 0) + p.transcript.length;
  return Object.entries(weight).sort((a, b) => b[1] - a[1])[0][0];
}

async function mapLimit(items, limit, fn) {
  const out = new Array(items.length);
  let next = 0;
  const worker = async () => { while (next < items.length) { const i = next++; out[i] = await fn(items[i]); } };
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, worker));
  return out;
}

// ------------------------------------------------------------ progress UI

let elapsedTimer = null;

function startProgress(speak) {
  for (const li of document.querySelectorAll(".steps li")) {
    li.className = "";
    li.querySelector("[data-detail]").textContent = "";
  }
  document.querySelector('[data-step="speak"]').hidden = !speak;
  $("inputCard").hidden = true;
  $("progress").hidden = false;
  const t0 = Date.now();
  const tick = () => ($("elapsed").textContent = `${Math.floor((Date.now() - t0) / 1000)}s`);
  tick(); elapsedTimer = setInterval(tick, 1000);
}

function setStep(step, state, detail) {
  const li = document.querySelector(`[data-step="${step}"]`);
  li.className = state;
  if (detail !== undefined) li.querySelector("[data-detail]").textContent = detail;
}

function stopProgress() {
  clearInterval(elapsedTimer);
  $("progress").hidden = true;
  $("inputCard").hidden = false;
  $("inputCard").classList.toggle("compact", !$("result").hidden);
}

function showError(msg) {
  $("error").textContent = msg;
  $("error").hidden = false;
}

// ------------------------------------------------------------ result UI

const player = $("player");
let audioUrl = null;

function resetResult() {
  player.pause();
  $("error").hidden = true;
  $("result").hidden = true;
  $("audioBox").hidden = true;
  $("audioActions").hidden = true;
  $("timing").textContent = "";
  $("inputCard").classList.remove("compact");
}

function showText(transcript, translation, source, target, skipped) {
  $("translation").textContent = translation;
  $("transcript").textContent = transcript;
  $("targetLabel").textContent = sarvam.languageName(target);
  $("sourceLabel").textContent = skipped
    ? `Original · ${sarvam.languageName(source)}`
    : `Original · ${sarvam.languageName(source)}`;
  $("transcript").classList.add("clamp");
  $("result").hidden = false;
  requestAnimationFrame(() => {
    const t = $("transcript");
    $("moreBtn").hidden = t.scrollHeight <= t.clientHeight + 2;
    $("moreBtn").textContent = "Show full original";
  });
  $("result").scrollIntoView({ behavior: "smooth", block: "start" });
}

$("moreBtn").addEventListener("click", () => {
  const clamped = $("transcript").classList.toggle("clamp");
  $("moreBtn").textContent = clamped ? "Show full original" : "Show less";
});

async function showAudio(wavBlob, filename, target) {
  if (audioUrl) URL.revokeObjectURL(audioUrl);
  audioUrl = URL.createObjectURL(wavBlob);
  const base = (filename || "voice").replace(/\.[^.]+$/, "");
  const outName = `${base}_${target}.wav`;
  player.src = audioUrl;
  $("saveBtn").href = audioUrl;
  $("saveBtn").download = outName;
  const file = new File([wavBlob], outName, { type: "audio/wav" });
  const canShare = !!(navigator.canShare && navigator.canShare({ files: [file] }));
  $("shareBtn").hidden = !canShare;
  $("shareBtn").onclick = () => navigator.share({ files: [file], title: "Translated voice note" }).catch(() => {});
  drawWave(await wavBlob.arrayBuffer());
  $("audioBox").hidden = false;
  $("audioActions").hidden = false;
  player.play().catch(() => {}); // autoplay may be blocked; the play button is right there
}

// Waveform: 44-byte header written by concatWavs, then 16-bit PCM.
const BARS = 44;
function drawWave(buf) {
  const pcm = new Int16Array(buf, 44, (buf.byteLength - 44) >> 1);
  const per = Math.max(1, Math.floor(pcm.length / BARS));
  const peaks = [];
  for (let b = 0; b < BARS; b++) {
    let sum = 0;
    for (let i = b * per; i < (b + 1) * per && i < pcm.length; i += 4) sum += pcm[i] * pcm[i];
    peaks.push(Math.sqrt(sum / (per / 4)));
  }
  const max = Math.max(...peaks, 1);
  const wave = $("wave");
  wave.replaceChildren(...peaks.map((p) => {
    const bar = document.createElement("i");
    bar.style.height = `${Math.max(12, Math.round((p / max) * 100))}%`;
    return bar;
  }));
  paintProgress();
}

function paintProgress() {
  const frac = player.duration ? player.currentTime / player.duration : 0;
  const on = Math.round(frac * BARS);
  [...$("wave").children].forEach((b, i) => b.classList.toggle("on", i < on));
  const shown = player.paused && !player.currentTime ? player.duration : player.currentTime;
  $("time").textContent = fmt(isFinite(shown) ? shown : 0);
}

player.addEventListener("timeupdate", paintProgress);
player.addEventListener("loadedmetadata", paintProgress);
player.addEventListener("play", () => setPlayIcon(true));
player.addEventListener("pause", () => setPlayIcon(false));
player.addEventListener("ended", () => { player.currentTime = 0; paintProgress(); });
$("playBtn").addEventListener("click", () => (player.paused ? player.play() : player.pause()));
function setPlayIcon(playing) {
  $("playIcon").setAttribute("href", playing ? "#i-pause" : "#i-play");
  $("playBtn").setAttribute("aria-label", playing ? "Pause" : "Play");
}
function seek(e) {
  const r = $("wave").getBoundingClientRect();
  if (!player.duration) return;
  player.currentTime = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)) * player.duration;
  paintProgress();
}
$("wave").addEventListener("pointerdown", (e) => { seek(e); $("wave").setPointerCapture(e.pointerId); });
$("wave").addEventListener("pointermove", (e) => { if (e.buttons) seek(e); });

function fmt(s) {
  s = Math.max(0, Math.round(s));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

// ------------------------------------------------------------ copy

document.addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-copy]");
  if (!btn) return;
  const text = $(btn.dataset.copy).textContent;
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const ta = Object.assign(document.createElement("textarea"), { value: text });
    document.body.append(ta); ta.select(); document.execCommand("copy"); ta.remove();
  }
  toast("Copied to clipboard");
});

let toastTimer;
function toast(msg) {
  $("toast").textContent = msg; $("toast").hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => ($("toast").hidden = true), 1600);
}

// ------------------------------------------------------------ PWA: install, share target, SW

let installEvt = null;
window.addEventListener("beforeinstallprompt", (e) => { e.preventDefault(); installEvt = e; $("installBtn").hidden = false; });
$("installBtn").addEventListener("click", async () => {
  if (!installEvt) return;
  installEvt.prompt();
  await installEvt.userChoice;
  installEvt = null; $("installBtn").hidden = true;
});

async function takeSharedFile() {
  const params = new URLSearchParams(location.search);
  if (!params.has("shared")) return;
  history.replaceState(null, "", location.pathname);
  if (params.get("shared") === "none") { showError("Nothing to translate was shared. Try sharing the voice note again."); return; }
  try {
    const cache = await caches.open("share-target");
    const res = await cache.match("shared-audio");
    if (!res) return;
    await cache.delete("shared-audio");
    const name = decodeURIComponent(res.headers.get("x-filename") || "voice-note.opus");
    const file = new File([await res.blob()], name, { type: res.headers.get("content-type") || "" });
    run(file, name);
  } catch {}
}

if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
showScreen();
takeSharedFile();
