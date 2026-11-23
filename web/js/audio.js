// Browser-side audio helpers: decode any format the browser understands,
// downmix + resample to 16 kHz mono, split at quiet points into clips short
// enough for Sarvam's real-time STT endpoint, and stitch WAVs back together.

const TARGET_RATE = 16000;
const MAX_CLIP_S = 28;   // STT REST limit is 30 s
const MIN_CLIP_S = 18;   // look for a pause between 18 s and 28 s

/** Decode a File/Blob into 16 kHz mono Float32Array. Throws if the browser can't decode it. */
export async function decodeTo16kMono(blob) {
  const data = await blob.arrayBuffer();
  const Ctx = window.AudioContext || window.webkitAudioContext;
  const ctx = new Ctx();
  let decoded;
  try {
    decoded = await new Promise((resolve, reject) => {
      const p = ctx.decodeAudioData(data, resolve, reject); // callback form for old Safari
      if (p && p.catch) p.catch(reject);
    });
  } finally {
    ctx.close?.();
  }
  const length = Math.ceil(decoded.duration * TARGET_RATE);
  const off = new OfflineAudioContext(1, Math.max(length, 1), TARGET_RATE);
  const src = off.createBufferSource();
  src.buffer = decoded;
  src.connect(off.destination); // OfflineAudioContext with 1 channel downmixes
  src.start();
  const rendered = await off.startRendering();
  return rendered.getChannelData(0);
}

/** Split samples into clips <= MAX_CLIP_S, cutting at the quietest 100 ms window. */
export function splitAtPauses(samples, rate = TARGET_RATE) {
  const clips = [];
  const win = Math.round(rate * 0.1);
  let start = 0;
  while (samples.length - start > MAX_CLIP_S * rate) {
    const lo = start + MIN_CLIP_S * rate;
    const hi = start + MAX_CLIP_S * rate - win;
    let best = hi, bestEnergy = Infinity;
    for (let i = lo; i < hi; i += win) {
      let e = 0;
      for (let j = i; j < i + win; j++) e += samples[j] * samples[j];
      if (e < bestEnergy) { bestEnergy = e; best = i + (win >> 1); }
    }
    clips.push(samples.subarray(start, best));
    start = best;
  }
  if (samples.length - start > rate * 0.3) clips.push(samples.subarray(start));
  return clips;
}

/** Float32 mono samples -> 16-bit PCM WAV Blob. */
export function encodeWav(samples, rate = TARGET_RATE) {
  const buf = new ArrayBuffer(44 + samples.length * 2);
  const v = new DataView(buf);
  writeHeader(v, samples.length * 2, rate, 1);
  let o = 44;
  for (let i = 0; i < samples.length; i++, o += 2) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    v.setInt16(o, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  return new Blob([buf], { type: "audio/wav" });
}

/** Concatenate WAV ArrayBuffers that share the same format. */
export function concatWavs(buffers) {
  const parsed = buffers.map(parseWav);
  const { rate, channels } = parsed[0];
  const total = parsed.reduce((n, p) => n + p.pcm.byteLength, 0);
  const out = new Uint8Array(44 + total);
  writeHeader(new DataView(out.buffer), total, rate, channels);
  let o = 44;
  for (const p of parsed) { out.set(p.pcm, o); o += p.pcm.byteLength; }
  return new Blob([out], { type: "audio/wav" });
}

function parseWav(buffer) {
  const v = new DataView(buffer);
  let rate = 22050, channels = 1, off = 12;
  while (off + 8 <= v.byteLength) {
    const id = String.fromCharCode(v.getUint8(off), v.getUint8(off + 1), v.getUint8(off + 2), v.getUint8(off + 3));
    let size = v.getUint32(off + 4, true);
    if (id === "fmt ") { channels = v.getUint16(off + 10, true); rate = v.getUint32(off + 12, true); }
    if (id === "data") {
      size = Math.min(size, v.byteLength - off - 8); // streaming WAVs may use 0xFFFFFFFF
      return { rate, channels, pcm: new Uint8Array(buffer, off + 8, size) };
    }
    off += 8 + size + (size & 1);
  }
  throw new Error("Invalid WAV from TTS");
}

function writeHeader(v, dataBytes, rate, channels) {
  const str = (o, s) => [...s].forEach((c, i) => v.setUint8(o + i, c.charCodeAt(0)));
  str(0, "RIFF"); v.setUint32(4, 36 + dataBytes, true); str(8, "WAVE");
  str(12, "fmt "); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, channels, true);
  v.setUint32(24, rate, true); v.setUint32(28, rate * channels * 2, true);
  v.setUint16(32, channels * 2, true); v.setUint16(34, 16, true);
  str(36, "data"); v.setUint32(40, dataBytes, true);
}
