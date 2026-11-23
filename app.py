"""
Voice Note Interpreter (Streamlit)

Drop in a WhatsApp voice note (or record one) in any Indian language and get
it back as text + speech in your language. Powered by Sarvam AI.

Access modes
  * Bring your own key (always on): user pastes their Sarvam API key. It lives
    only in this browser session's memory on the server; never stored or logged.
  * Owner sign-in (optional): if APP_USERNAME and APP_PASSWORD_SHA256 are set,
    signing in uses the owner's SARVAM_API_KEY. That key is never shown to users.
"""

import hashlib
import hmac
import os
import time

import streamlit as st
from dotenv import load_dotenv

import pipeline as p

load_dotenv()

st.set_page_config(
    page_title="Voice Note Interpreter",
    page_icon="🗣️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

AUDIO_TYPES = {"opus", "ogg", "oga", "mp3", "m4a", "aac", "wav", "webm", "flac", "amr", "mp4", "3gp"}
MAX_LOGIN_ATTEMPTS = 5
REPO_URL = "https://github.com/namanjain27/interpretor-indic"
AUTHOR_URL = "https://namanjain27.github.io/"

WHATSAPP_GUIDE = """
**Android**
1. In the chat, long-press the voice note.
2. Tap **Share** (the ⋮ menu → Share on some phones).
3. Pick **Files / Save to device**, then come back here and tap **Upload**.

**iPhone**
1. Long-press the voice note → **Forward**.
2. Tap the **Share** icon at the bottom-right → **Save to Files**.
3. Come back here, tap **Upload** → **Browse** and pick the saved file.

**WhatsApp Web / Desktop**: hover the voice note → ⌄ → **Download**, then upload it here.

Any format works: WhatsApp's `.opus`, `.ogg`, `.m4a`, `.mp3`, `.wav`, `.aac`.
No conversion needed. Someone talking in front of you? Use the **Record** tab.
"""


# ---------------------------------------------------------------- config


def secret(name: str) -> str:
    """Read from Streamlit secrets (Streamlit Cloud) or env vars (.env / Docker)."""
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:  # no secrets.toml present
        pass
    return os.getenv(name, "")


OWNER_KEY = secret("SARVAM_API_KEY")
OWNER_USER = secret("APP_USERNAME")
OWNER_PASS_SHA256 = secret("APP_PASSWORD_SHA256").lower()
OWNER_LOGIN_ENABLED = bool(OWNER_KEY and OWNER_USER and OWNER_PASS_SHA256)


# ---------------------------------------------------------------- styles

st.markdown(
    """
<style>
  .stApp { background: linear-gradient(160deg, #FFE7D1 0%, #EADBCB 100%); }
  header[data-testid="stHeader"] { background: transparent; }
  .block-container { max-width: 560px; padding: 1.25rem 1rem 3rem; }
  h1.title { font-family: Georgia, serif; color: #5a3e28; font-size: 1.7rem; margin: 0; text-align: center; }
  p.sub { color: #8a6e57; text-align: center; margin: .2rem 0 1rem; font-size: .95rem; }
  .card { background: #fffaf5; border-radius: 14px; padding: 1rem 1.1rem; margin: .5rem 0;
          box-shadow: 0 1px 3px rgba(90,62,40,.12); color: #2d1f14; }
  .card .label { font-size: .72rem; letter-spacing: .06em; text-transform: uppercase; color: #8a6e57;
                 font-weight: 600; margin-bottom: .35rem; }
  .card .big { font-size: 1.15rem; line-height: 1.6; white-space: pre-wrap; }
  .muted { color: #8a6e57; font-size: .82rem; }
  /* Copyable text blocks (st.code) styled as readable cards, not code */
  [data-testid="stCode"] pre, [data-testid="stCode"] code {
      font-family: inherit !important; font-size: 1.08rem !important; line-height: 1.6 !important;
      background: #fffaf5 !important; color: #2d1f14 !important; white-space: pre-wrap !important; }
  [data-testid="stCode"] pre { border-radius: 14px; padding: 1rem 2.6rem 1rem 1.1rem !important;
      box-shadow: 0 1px 3px rgba(90,62,40,.12); }
  /* Copy icon is hover-only by default; phones can't hover, so always show it */
  [data-testid="stCode"] div:has([data-testid="stBaseButton-elementToolbar"]),
  [data-testid="stCode"] [data-testid="stBaseButton-elementToolbar"] {
      visibility: visible !important; opacity: 1 !important; }
  [data-testid="stCode"] [data-testid="stBaseButton-elementToolbar"] {
      color: #7a5236 !important; background: #f3e3d3 !important; border-radius: 8px !important;
      width: 34px !important; height: 34px !important; }
  .reassure { text-align: center; font-size: .8rem; color: #8a6e57; margin-top: .5rem; }
  .reassure a { color: #7a5236; }
  .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
      border-radius: 10px; min-height: 2.8rem; }
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- access gate


def sign_out():
    for k in ("api_key", "who", "results"):
        st.session_state.pop(k, None)


def access_gate():
    st.markdown('<h1 class="title">Voice Note Interpreter</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub">Understand any Indian-language voice note, in your language.</p>',
        unsafe_allow_html=True,
    )

    tabs = st.tabs(["Use my Sarvam key", "Sign in"] if OWNER_LOGIN_ENABLED else ["Use my Sarvam key"])

    with tabs[0]:
        with st.form("byok"):
            key = st.text_input("Sarvam API key", type="password", placeholder="sk_...")
            go = st.form_submit_button("Continue", type="primary", use_container_width=True)
        st.markdown(
            '<p class="muted">No key? Get one free at '
            '<a href="https://dashboard.sarvam.ai" target="_blank">dashboard.sarvam.ai</a>. '
            "Your key stays in this browser session only and is never saved.</p>",
            unsafe_allow_html=True,
        )
        reassurance()
        if go:
            with st.spinner("Checking key..."):
                try:
                    p.validate_key(key)
                except p.InterpreterError as e:
                    st.error(str(e))
                else:
                    st.session_state.api_key = key.strip()
                    st.session_state.who = "your key"
                    st.rerun()

    if OWNER_LOGIN_ENABLED:
        with tabs[1]:
            attempts = st.session_state.get("login_attempts", 0)
            if attempts >= MAX_LOGIN_ATTEMPTS:
                st.error("Too many attempts. Reload the page to try again.")
                return
            with st.form("login"):
                user = st.text_input("Username", autocomplete="username")
                pw = st.text_input("Password", type="password", autocomplete="current-password")
                go = st.form_submit_button("Sign in", type="primary", use_container_width=True)
            if go:
                digest = hashlib.sha256(pw.encode()).hexdigest()
                ok_user = hmac.compare_digest(user.strip().encode(), OWNER_USER.encode())
                ok_pass = hmac.compare_digest(digest, OWNER_PASS_SHA256)
                if ok_user and ok_pass:
                    st.session_state.api_key = OWNER_KEY
                    st.session_state.who = user.strip()
                    st.session_state.login_attempts = 0
                    st.rerun()
                else:
                    st.session_state.login_attempts = attempts + 1
                    time.sleep(1)
                    st.error("Wrong username or password.")


# ---------------------------------------------------------------- main screen


def remembered_language() -> str:
    code = st.query_params.get("to", "hi-IN")
    names = {v: k for k, v in p.LANGUAGES.items()}
    return names.get(code, "Hindi")


def render_result(r: p.Result, target_code: str, base_name: str):
    target_name = p.language_name(target_code)
    st.caption(f"**{target_name.upper()}** · tap the copy icon to copy")
    copyable(r.translation)
    if r.audio_wav:
        st.audio(r.audio_wav, format="audio/wav", autoplay=True)
        st.download_button(
            "Save audio",
            data=r.audio_wav,
            file_name=f"{base_name}_{target_code}.wav",
            mime="audio/wav",
            use_container_width=True,
        )
    src = p.language_name(r.source_lang)
    label = f"Original ({src})" + (" · already in your language" if r.skipped_translation else "")
    with st.expander(label):
        copyable(r.transcript)
    total = sum(r.timings.values())
    st.markdown(f'<p class="muted">Done in {total:.1f}s</p>', unsafe_allow_html=True)


def copyable(text: str):
    """Text block with Streamlit's built-in copy-to-clipboard button."""
    st.code(text, language=None, wrap_lines=True)


def reassurance():
    st.markdown(
        f'<p class="reassure">🔒 Open source. Your key is never saved or logged. '
        f'<a href="{REPO_URL}" target="_blank">Check the code on GitHub</a></p>'
        f'<p class="reassure">Built by <a href="{AUTHOR_URL}" target="_blank">Naman Jain</a>'
        f' · Powered by Sarvam AI</p>',
        unsafe_allow_html=True,
    )


def main_screen():
    st.markdown('<h1 class="title">Voice Note Interpreter</h1>', unsafe_allow_html=True)

    lang_names = list(p.LANGUAGES)
    target_name = st.selectbox(
        "Translate to", lang_names, index=lang_names.index(remembered_language())
    )
    target_code = p.LANGUAGES[target_name]
    if st.query_params.get("to") != target_code:
        st.query_params["to"] = target_code  # bookmark keeps your language

    with st.expander("Voice & options"):
        gender = st.radio("Voice", ["female", "male"], horizontal=True, format_func=str.title)
        speak = st.toggle("Read the translation aloud", value=True)
        pace = st.slider("Speed", 0.75, 1.5, 1.0, 0.05, disabled=not speak)

    up_tab, rec_tab = st.tabs(["Voice note / audio file", "Record"])
    with up_tab:
        uploaded = st.file_uploader(
            "Voice note",
            type=None,  # explicit types make iOS grey out WhatsApp .opus files
            label_visibility="collapsed",
        )
        if not uploaded:
            with st.expander("How do I get a voice note out of WhatsApp?"):
                st.markdown(WHATSAPP_GUIDE)
    with rec_tab:
        recorded = st.audio_input("Record someone speaking", label_visibility="collapsed")

    audio_file = recorded or uploaded
    if not audio_file:
        return

    ext = audio_file.name.rsplit(".", 1)[-1].lower() if "." in audio_file.name else ""
    if ext and ext not in AUDIO_TYPES:
        st.error(f"'.{ext}' isn't an audio file I can read. Try a voice note, mp3, m4a or wav.")
        return

    audio = audio_file.getvalue()
    run_key = (
        hashlib.sha1(audio).hexdigest(), target_code, gender, speak, round(pace, 2),
    )
    results = st.session_state.setdefault("results", {})

    if run_key not in results:
        status = st.status("Listening...", expanded=False)
        try:
            def on_step(step, r):
                if step == "transcribed":
                    status.update(label=f"Heard {p.language_name(r.source_lang)}. Translating...")
                elif step == "translated" and speak:
                    status.update(label="Generating voice...")

            results[run_key] = p.interpret(
                st.session_state.api_key, audio, audio_file.name or "audio.wav",
                target_code, gender, speak, pace, on_step,
            )
            status.update(label="Done", state="complete")
        except Exception as e:
            status.update(label="Failed", state="error")
            st.error(p.friendly_error(e))
            return

    base = (audio_file.name or "voice").rsplit(".", 1)[0]
    render_result(results[run_key], target_code, base)


def footer():
    st.divider()
    c1, c2 = st.columns([3, 1])
    c1.markdown(
        f'<p class="muted">Using {st.session_state.get("who", "")}</p>',
        unsafe_allow_html=True,
    )
    c2.button("Sign out", on_click=sign_out, use_container_width=True)
    reassurance()


if st.session_state.get("api_key"):
    main_screen()
    footer()
else:
    access_gate()
