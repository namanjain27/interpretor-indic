"""
Sarvam AI interpreter pipeline: speech -> text -> translation -> speech.

UI-agnostic so it can be reused from Streamlit (app.py), the CLI (main.py),
or a future API/PWA backend.

Models (latest as of sarvamai 0.1.48):
  STT        saaras:v4            (REST for short clips, Batch for long ones)
  Translate  sarvam-translate:v1  (22 Indian languages)
  TTS        bulbul:v4-flash      (persona voices)
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
import tempfile
import wave
from dataclasses import dataclass, field
from typing import Callable, Optional

from sarvamai import SarvamAI

STT_MODEL = "saaras:v4"
TRANSLATE_MODEL = "sarvam-translate:v1"
TTS_MODEL = "bulbul:v4-flash"

REST_STT_MAX_SECONDS = 29  # REST STT accepts < 30s; longer audio goes to the Batch API
TRANSLATE_CHUNK_CHARS = 1800  # API limit is 2000 for sarvam-translate:v1
TTS_CHUNK_CHARS = 2400  # API limit is 2500 for bulbul:v4-flash
TTS_SAMPLE_RATE = 22050

# Target languages: the ones bulbul can speak. (STT/translate support more.)
LANGUAGES = {
    "Hindi": "hi-IN",
    "English": "en-IN",
    "Bengali": "bn-IN",
    "Gujarati": "gu-IN",
    "Kannada": "kn-IN",
    "Malayalam": "ml-IN",
    "Marathi": "mr-IN",
    "Odia": "od-IN",
    "Punjabi": "pa-IN",
    "Tamil": "ta-IN",
    "Telugu": "te-IN",
}

LANGUAGE_NAMES = {
    **{code: name for name, code in LANGUAGES.items()},
    "as-IN": "Assamese", "ur-IN": "Urdu", "ne-IN": "Nepali", "kok-IN": "Konkani",
    "ks-IN": "Kashmiri", "sd-IN": "Sindhi", "sa-IN": "Sanskrit", "sat-IN": "Santali",
    "mni-IN": "Manipuri", "brx-IN": "Bodo", "mai-IN": "Maithili", "doi-IN": "Dogri",
}

# bulbul:v4-flash persona per (language, gender). Native personas where the
# catalog has one; otherwise a Hindi conversational persona (verified to work
# across languages).
_DEFAULT_VOICE = {"female": "simran_hi_conversation", "male": "shubh_hi_customer"}
VOICES = {
    "hi-IN": {"female": "simran_hi_conversation", "male": "shubh_hi_customer"},
    "en-IN": {"female": "simran_en_conversation", "male": "dev_en_conversational"},
    "bn-IN": {"female": "roopa_bn_conversational", "male": "arnab_bn_conversation"},
    "gu-IN": {"female": "pooja_gu_conversational", "male": "bhavik_gu_conversation"},
    "kn-IN": {"female": "chaitra_kn_conversation", "male": "chetan_kn_conversation"},
    "mr-IN": {"female": "ishita_mr_conversational", "male": "nilesh_mr_conversation"},
    "pa-IN": {"female": "harpreet_pa_narration", "male": "anand_pa_conversation"},
    "ta-IN": {"female": _DEFAULT_VOICE["female"], "male": "gokul_ta_narration"},
    "te-IN": {"female": "kavitha_te_conversation", "male": "tarun_te_narration"},
}


def voice_for(lang: str, gender: str) -> str:
    return VOICES.get(lang, _DEFAULT_VOICE)[gender]


def language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code)


class InterpreterError(Exception):
    """Error with a message that is safe and useful to show an end user."""


@dataclass
class Result:
    source_lang: str = ""
    transcript: str = ""
    translation: str = ""
    audio_wav: Optional[bytes] = None
    skipped_translation: bool = False
    timings: dict = field(default_factory=dict)


# ---------------------------------------------------------------- helpers


def audio_duration_seconds(audio: bytes) -> Optional[float]:
    """Best-effort duration for mp3/ogg/opus/m4a/wav/aac. None if unknown."""
    try:
        import mutagen

        f = mutagen.File(io.BytesIO(audio))
        if f is not None and f.info and f.info.length:
            return float(f.info.length)
    except Exception:
        pass
    try:
        with wave.open(io.BytesIO(audio)) as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return None


def chunk_text(text: str, limit: int) -> list[str]:
    """Split on sentence boundaries (incl. Indic danda) so each chunk <= limit."""
    text = text.strip()
    if len(text) <= limit:
        return [text] if text else []
    sentences = re.split(r"(?<=[.!?।॥])\s+", text)
    chunks, cur = [], ""
    for s in sentences:
        while len(s) > limit:  # a single giant "sentence": hard-split on spaces
            cut = s.rfind(" ", 0, limit)
            cut = cut if cut > 0 else limit
            if cur:
                chunks.append(cur)
                cur = ""
            chunks.append(s[:cut].strip())
            s = s[cut:].strip()
        if len(cur) + len(s) + 1 > limit:
            chunks.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        chunks.append(cur)
    return [c for c in chunks if c]


def concat_wavs(parts: list[bytes]) -> bytes:
    if len(parts) == 1:
        return parts[0]
    out = io.BytesIO()
    with wave.open(io.BytesIO(parts[0])) as first:
        params = first.getparams()
    with wave.open(out, "wb") as w:
        w.setparams(params)
        for p in parts:
            with wave.open(io.BytesIO(p)) as r:
                w.writeframes(r.readframes(r.getnframes()))
    return out.getvalue()


def friendly_error(e: Exception) -> str:
    """Map SDK/HTTP errors to something a phone user can act on."""
    status = getattr(e, "status_code", None)
    body = getattr(e, "body", None)
    msg = ""
    if isinstance(body, dict):
        msg = (body.get("error") or {}).get("message", "") if isinstance(body.get("error"), dict) else str(body)
    if status in (401, 403):
        return "Your Sarvam API key was rejected. Check it at dashboard.sarvam.ai and try again."
    if status == 429:
        return "Rate limit or credits exhausted on this Sarvam key. Wait a minute or top up credits."
    if status and 400 <= status < 500:
        return f"Sarvam couldn't process this request: {msg or 'bad request'}"
    if status and status >= 500:
        return "Sarvam's servers had a hiccup. Please try again in a moment."
    if isinstance(e, InterpreterError):
        return str(e)
    return f"Something went wrong: {e}"


# ---------------------------------------------------------------- steps


def make_client(api_key: str) -> SarvamAI:
    return SarvamAI(api_subscription_key=api_key, timeout=120)


def validate_key(api_key: str) -> None:
    """Raise if Sarvam rejects the key. Uses the free list-models endpoint."""
    if not api_key or not api_key.strip().startswith("sk_"):
        raise InterpreterError("That doesn't look like a Sarvam key. It should start with 'sk_'.")
    try:
        make_client(api_key.strip()).chat_completion.list_models_v2()
    except Exception as e:
        raise InterpreterError(friendly_error(e)) from e


def speech_to_text(client: SarvamAI, audio: bytes, filename: str) -> tuple[str, str]:
    """Return (transcript, detected_language_code)."""
    duration = audio_duration_seconds(audio)
    if duration is not None and duration <= REST_STT_MAX_SECONDS:
        resp = client.speech_to_text.transcribe(
            file=(filename, audio),
            model=STT_MODEL,
            mode="transcribe",
            language_code="unknown",
        )
        return (resp.transcript or "").strip(), resp.language_code or "en-IN"
    return _speech_to_text_batch(client, audio, filename)


def _speech_to_text_batch(client: SarvamAI, audio: bytes, filename: str) -> tuple[str, str]:
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", filename) or "audio"
    with tempfile.TemporaryDirectory() as tmp:
        in_path = os.path.join(tmp, safe_name)
        with open(in_path, "wb") as f:
            f.write(audio)
        job = client.speech_to_text_job.create_job(
            model=STT_MODEL, mode="transcribe", language_code="unknown"
        )
        job.upload_files(file_paths=[in_path])
        job.start()
        job.wait_until_complete()
        results = job.get_file_results()
        if not results["successful"]:
            failed = results["failed"][0]["error_message"] if results["failed"] else "unknown error"
            raise InterpreterError(f"Transcription failed: {failed}")
        out_dir = os.path.join(tmp, "out")
        os.makedirs(out_dir, exist_ok=True)
        job.download_outputs(output_dir=out_dir)
        jsons = [p for p in os.listdir(out_dir) if p.endswith(".json")]
        if not jsons:
            raise InterpreterError("Transcription finished but returned no transcript.")
        with open(os.path.join(out_dir, jsons[0]), encoding="utf-8") as f:
            data = json.load(f)
        return (data.get("transcript") or "").strip(), data.get("language_code") or "en-IN"


def translate(client: SarvamAI, text: str, source: str, target: str, gender: str) -> str:
    out = []
    for chunk in chunk_text(text, TRANSLATE_CHUNK_CHARS):
        resp = client.text.translate(
            input=chunk,
            source_language_code=source,
            target_language_code=target,
            speaker_gender="Male" if gender == "male" else "Female",
            model=TRANSLATE_MODEL,
        )
        out.append(resp.translated_text)
    return " ".join(out)


def text_to_speech(client: SarvamAI, text: str, lang: str, gender: str, pace: float = 1.0) -> bytes:
    parts = []
    for chunk in chunk_text(text, TTS_CHUNK_CHARS):
        resp = client.text_to_speech.convert(
            text=chunk,
            language_code=lang,
            speaker=voice_for(lang, gender),
            model=TTS_MODEL,
            pace=pace,
            speech_sample_rate=TTS_SAMPLE_RATE,
        )
        parts.append(base64.b64decode("".join(resp.audios)))
    return concat_wavs(parts)


# ---------------------------------------------------------------- orchestration


def interpret(
    api_key: str,
    audio: bytes,
    filename: str,
    target_lang: str,
    gender: str = "female",
    speak: bool = True,
    pace: float = 1.0,
    on_step: Callable[[str, Result], None] = lambda step, result: None,
) -> Result:
    """Run the pipeline. `on_step` is called with "transcribed", "translated",
    "spoken" as each stage finishes, so a UI can show partial results early."""
    import time

    client = make_client(api_key)
    r = Result()

    t = time.perf_counter()
    r.transcript, r.source_lang = speech_to_text(client, audio, filename)
    r.timings["stt"] = time.perf_counter() - t
    if not r.transcript:
        raise InterpreterError("No speech detected in this audio.")
    on_step("transcribed", r)

    t = time.perf_counter()
    if r.source_lang == target_lang:
        r.translation, r.skipped_translation = r.transcript, True
    else:
        r.translation = translate(client, r.transcript, r.source_lang, target_lang, gender)
    r.timings["translate"] = time.perf_counter() - t
    on_step("translated", r)

    if speak:
        t = time.perf_counter()
        r.audio_wav = text_to_speech(client, r.translation, target_lang, gender, pace)
        r.timings["tts"] = time.perf_counter() - t
        on_step("spoken", r)
    return r
