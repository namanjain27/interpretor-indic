// Thin client for the Sarvam REST API, called straight from the browser.
// The key goes only to api.sarvam.ai (enforced by the page's CSP connect-src).

const BASE = "https://api.sarvam.ai";

export const STT_MODEL = "saaras:v4";
export const TRANSLATE_MODEL = "sarvam-translate:v1";
export const TTS_MODEL = "bulbul:v4-flash";

export const LANGUAGES = {
  "hi-IN": "Hindi", "en-IN": "English", "bn-IN": "Bengali", "gu-IN": "Gujarati",
  "kn-IN": "Kannada", "ml-IN": "Malayalam", "mr-IN": "Marathi", "od-IN": "Odia",
  "pa-IN": "Punjabi", "ta-IN": "Tamil", "te-IN": "Telugu",
};

const EXTRA_NAMES = {
  "as-IN": "Assamese", "ur-IN": "Urdu", "ne-IN": "Nepali", "kok-IN": "Konkani",
  "ks-IN": "Kashmiri", "sd-IN": "Sindhi", "sa-IN": "Sanskrit", "sat-IN": "Santali",
  "mni-IN": "Manipuri", "brx-IN": "Bodo", "mai-IN": "Maithili", "doi-IN": "Dogri",
};

export const languageName = (code) => LANGUAGES[code] || EXTRA_NAMES[code] || code;

// bulbul:v4-flash personas. Native where the catalog has one, else a Hindi
// conversational persona (verified to work across languages).
const DEFAULT_VOICE = { female: "simran_hi_conversation", male: "shubh_hi_customer" };
const VOICES = {
  "hi-IN": { female: "simran_hi_conversation", male: "shubh_hi_customer" },
  "en-IN": { female: "simran_en_conversation", male: "dev_en_conversational" },
  "bn-IN": { female: "roopa_bn_conversational", male: "arnab_bn_conversation" },
  "gu-IN": { female: "pooja_gu_conversational", male: "bhavik_gu_conversation" },
  "kn-IN": { female: "chaitra_kn_conversation", male: "chetan_kn_conversation" },
  "mr-IN": { female: "ishita_mr_conversational", male: "nilesh_mr_conversation" },
  "pa-IN": { female: "harpreet_pa_narration", male: "anand_pa_conversation" },
  "ta-IN": { female: DEFAULT_VOICE.female, male: "gokul_ta_narration" },
  "te-IN": { female: "kavitha_te_conversation", male: "tarun_te_narration" },
};
const voiceFor = (lang, gender) => (VOICES[lang] || DEFAULT_VOICE)[gender];

export class SarvamError extends Error {
  constructor(message, status) { super(message); this.status = status; }
}

async function call(key, path, { json, form, method = "POST" } = {}) {
  const headers = { "api-subscription-key": key };
  let body;
  if (json) { headers["content-type"] = "application/json"; body = JSON.stringify(json); }
  if (form) body = form;
  let res;
  try {
    res = await fetch(`${BASE}/${path}`, { method, headers, body });
  } catch {
    throw new SarvamError("Couldn't reach Sarvam. Check your internet connection.", 0);
  }
  if (res.ok) return res.json();
  let msg = "";
  try { const b = await res.json(); msg = b?.error?.message || b?.detail || ""; } catch {}
  throw new SarvamError(friendly(res.status, msg), res.status);
}

function friendly(status, msg) {
  if (status === 401 || status === 403) return "Your Sarvam API key was rejected. Check it at dashboard.sarvam.ai.";
  if (status === 429) return "Rate limit or credits exhausted on this key. Wait a minute or top up credits.";
  if (status >= 500) return "Sarvam's servers had a hiccup. Please try again in a moment.";
  return `Sarvam couldn't process this: ${msg || "bad request"}`;
}

export async function validateKey(key) {
  if (!key || !key.trim().startsWith("sk_")) {
    throw new SarvamError("That doesn't look like a Sarvam key. It should start with 'sk_'.", 0);
  }
  await call(key.trim(), "v2/models", { method: "GET" });
}

/** Transcribe one clip (must be under 30s). Returns {transcript, language_code}. */
export async function transcribe(key, blob, filename) {
  const form = new FormData();
  form.append("file", blob, filename);
  form.append("model", STT_MODEL);
  form.append("mode", "transcribe");
  form.append("language_code", "unknown");
  const r = await call(key, "speech-to-text", { form });
  return { transcript: (r.transcript || "").trim(), language: r.language_code || "en-IN" };
}

export async function translate(key, text, source, target, gender) {
  const parts = await Promise.all(chunkText(text, 1800).map((input) =>
    call(key, "translate", {
      json: {
        input, source_language_code: source, target_language_code: target,
        speaker_gender: gender === "male" ? "Male" : "Female", model: TRANSLATE_MODEL,
      },
    }).then((r) => r.translated_text)));
  return parts.join(" ");
}

/** Returns an array of WAV ArrayBuffers (one per text chunk), in order. */
export async function speak(key, text, lang, gender, pace = 1.0) {
  return Promise.all(chunkText(text, 2400).map((chunk) =>
    call(key, "text-to-speech", {
      json: {
        text: chunk, language_code: lang, speaker: voiceFor(lang, gender),
        model: TTS_MODEL, pace, speech_sample_rate: 22050,
      },
    }).then((r) => base64ToBuffer(r.audios.join("")))));
}

export function chunkText(text, limit) {
  text = text.trim();
  if (text.length <= limit) return text ? [text] : [];
  const sentences = text.split(/(?<=[.!?।॥])\s+/);
  const chunks = [];
  let cur = "";
  for (let s of sentences) {
    while (s.length > limit) {
      let cut = s.lastIndexOf(" ", limit);
      if (cut <= 0) cut = limit;
      if (cur) { chunks.push(cur); cur = ""; }
      chunks.push(s.slice(0, cut).trim());
      s = s.slice(cut).trim();
    }
    if (cur.length + s.length + 1 > limit) { chunks.push(cur); cur = s; }
    else cur = (cur + " " + s).trim();
  }
  if (cur) chunks.push(cur);
  return chunks.filter(Boolean);
}

function base64ToBuffer(b64) {
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out.buffer;
}
