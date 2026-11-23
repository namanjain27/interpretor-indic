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
  $("forgetBtn").hidden = !key;
  $("who").textContent = key ? `Using your key (…${key.slice(-4)})` : "";
  if (key && pendingShared) { const f = pendingShared; pendingShared = null; run(f, f.name); }
}

$("keyForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const key = $("keyInput").value.trim();
  $("keyError").hidden = true;
  $("keyBtn").disabled = true;
  $("keyBtn").textContent = "Checking…";
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
    $("keyBtn").textContent = "Continue";
  }
});

$("forgetBtn").addEventListener("click", () => {
  store.del(KEY);
  $("result").hidden = true;
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
const updatePace = () => { $("paceOut").textContent = `${parseFloat($("pace").value).toFixed(2)}×`; $("pace").disabled = !$("speakToggle").checked; };
updatePace();
document.addEventListener("change", (e) => {
  if (e.target.closest(".options") || e.target === langSel) {
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

let recorder = null;
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
  $("recBtn").textContent = on ? "■ Stop & translate" : "● Record";
  $("recBtn").classList.toggle("recording", on);
}

// ------------------------------------------------------------ pipeline

let busy = false;
let audioUrl = null;

async function run(blob, filename) {
  if (busy) return;
  const key = getKey();
  if (!key) { pendingShared = blob; showScreen(); return; }
  busy = true;
  const o = opts();
  const t0 = performance.now();
  $("error").hidden = true;
  $("result").hidden = true;
  $("help").open = false;
  setBusy(true);
  try {
    setStatus("Preparing audio…");
    let clips;
    try {
      const samples = await decodeTo16kMono(blob);
      clips = splitAtPauses(samples).map((s, i) => ({ blob: encodeWav(s), name: `clip${i}.wav` }));
    } catch {
      clips = [{ blob, name: filename || "audio" }]; // browser can't decode it: let Sarvam try
    }
    if (!clips.length) throw new Error("This audio seems to be empty.");

    setStatus(clips.length > 1 ? `Listening (${clips.length} parts)…` : "Listening…");
    const parts = await mapLimit(clips, 4, (c) => sarvam.transcribe(key, c.blob, c.name));
    const transcript = parts.map((p) => p.transcript).filter(Boolean).join(" ");
    if (!transcript) throw new Error("No speech detected in this audio.");
    const source = dominantLanguage(parts);

    let translation = transcript;
    const skipped = source === o.target;
    if (!skipped) {
      setStatus(`Heard ${sarvam.languageName(source)}. Translating…`);
      translation = await sarvam.translate(key, transcript, source, o.target, o.gender);
    }
    showText(transcript, translation, source, o.target, skipped);

    if (o.speak) {
      setStatus("Generating voice…");
      const wavs = await sarvam.speak(key, translation, o.target, o.gender, o.pace);
      showAudio(concatWavs(wavs), filename, o.target);
    }
    $("timing").textContent = `Done in ${((performance.now() - t0) / 1000).toFixed(1)}s`;
  } catch (err) {
    showError(err.message || String(err));
  } finally {
    setStatus("");
    setBusy(false);
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

// ------------------------------------------------------------ rendering

function setStatus(msg) { $("status").textContent = msg; $("status").hidden = !msg; }
function setBusy(on) {
  $("recBtn").disabled = on && !recorder;
  document.querySelector(".file-btn").classList.toggle("disabled", on);
}
function showError(msg) { $("error").textContent = msg; $("error").hidden = false; }

function showText(transcript, translation, source, target, skipped) {
  $("translation").textContent = translation;
  $("transcript").textContent = transcript;
  $("targetLabel").textContent = sarvam.languageName(target);
  $("sourceLabel").textContent = `Original (${sarvam.languageName(source)})` + (skipped ? " · already in your language" : "");
  $("audioBox").hidden = true;
  $("timing").textContent = "";
  $("result").hidden = false;
  $("result").scrollIntoView({ behavior: "smooth", block: "start" });
}

function showAudio(wavBlob, filename, target) {
  if (audioUrl) URL.revokeObjectURL(audioUrl);
  audioUrl = URL.createObjectURL(wavBlob);
  const base = (filename || "voice").replace(/\.[^.]+$/, "");
  const outName = `${base}_${target}.wav`;
  $("player").src = audioUrl;
  $("saveBtn").href = audioUrl;
  $("saveBtn").download = outName;
  const file = new File([wavBlob], outName, { type: "audio/wav" });
  const canShare = !!(navigator.canShare && navigator.canShare({ files: [file] }));
  $("shareBtn").hidden = !canShare;
  $("shareBtn").onclick = () => navigator.share({ files: [file], title: "Translated voice note" }).catch(() => {});
  $("audioBox").hidden = false;
  $("player").play().catch(() => {}); // autoplay may be blocked; controls are there
}

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
  toast("Copied");
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
