# Voice Note Interpreter

Got a WhatsApp voice note in a language you don't speak? Drop it in (or record
someone) and get it back as **text and speech in your language**, in a few seconds.
Built on Sarvam AI.

Two front-ends share the same models and flow:

- **`web/`: installable phone app (PWA).** Runs entirely in the browser; your key is
  stored on your device and sent only to `api.sarvam.ai` (enforced by the page's
  Content-Security-Policy). On Android it appears in WhatsApp's **Share** menu.
  Hosted free on GitHub Pages.
- **`app.py`: Streamlit app.** Same thing server-side, plus optional owner sign-in.

## Getting a voice note out of WhatsApp

**Android (easiest):** open the web app in Chrome → ⋮ → **Install app**. Then in
WhatsApp long-press the voice note → **Share** → **Interpreter**. It opens and
translates automatically.

**iPhone:** long-press the voice note → **Forward** → **Share** icon (bottom-right)
→ **Save to Files**. In the app, tap **Choose voice note** → **Browse** → pick it.
To install: Safari → Share → **Add to Home Screen**. (iOS doesn't let web apps
appear in the Share menu yet.)

**WhatsApp Web / Desktop:** hover the voice note → ⌄ → **Download**, then choose it.

No conversion needed: `.opus`/`.ogg` (WhatsApp's format), `.m4a`, `.mp3`, `.wav`,
`.aac` all work. For someone speaking in front of you, use **Record**.

| Step | Model |
|---|---|
| Speech → text (auto language detect) | `saaras:v4` (REST for ≤29s, Batch API for longer) |
| Translation (22 Indian languages) | `sarvam-translate:v1` |
| Text → speech | `bulbul:v4-flash` persona voices |

## Access

- **Bring your own key** (always on): paste a Sarvam API key from
  [dashboard.sarvam.ai](https://dashboard.sarvam.ai). It's checked once, kept only
  in that browser session's memory, and never stored or logged.
- **Owner sign-in** (optional): set `SARVAM_API_KEY`, `APP_USERNAME` and
  `APP_PASSWORD_SHA256` and a "Sign in" tab appears that uses the owner's key.
  Generate the hash with:

  ```bash
  python3 -c "import hashlib,getpass;print(hashlib.sha256(getpass.getpass().encode()).hexdigest())"
  ```

Config is read from Streamlit secrets (`.streamlit/secrets.toml` / Streamlit Cloud
"Secrets") or environment variables / `.env`. See `.env.example`.

## Run locally

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run app.py
```

CLI: `python main.py voice.opus hi-IN female`

## Web app (PWA)

Plain static files, no build step. Run locally:

```bash
cd web && python3 -m http.server 8600
```

Long audio is decoded in the browser, resampled to 16 kHz and split at pauses into
<28 s clips that are transcribed in parallel, so there's no batch-job wait.

**Deploy free:** push to GitHub, then repo **Settings → Pages → Source: GitHub
Actions**. `.github/workflows/pages.yml` publishes `web/` on every push to `main`,
at `https://<user>.github.io/<repo>/`. When you change files in `web/`, bump
`VERSION` in `web/sw.js` so installed apps pick up the update.

## Deploy the Streamlit app free (Streamlit Community Cloud)

1. Push this repo to GitHub.
2. share.streamlit.io → New app → pick the repo, `app.py`.
3. (Optional) Advanced settings → Secrets:
   ```toml
   SARVAM_API_KEY = "sk_..."
   APP_USERNAME = "you"
   APP_PASSWORD_SHA256 = "<hash>"
   ```

Files: `pipeline.py` (all Sarvam calls, UI-agnostic) · `app.py` (Streamlit UI) · `main.py` (CLI)
