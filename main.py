"""CLI: python main.py <audio file> [target-lang-code] [female|male]

Uses SARVAM_API_KEY from the environment / .env.
"""

import os
import sys

from dotenv import load_dotenv

import pipeline as p

load_dotenv()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("Languages:", ", ".join(f"{c} ({n})" for n, c in p.LANGUAGES.items()))
        sys.exit(1)
    path = sys.argv[1]
    target = sys.argv[2] if len(sys.argv) > 2 else "hi-IN"
    gender = sys.argv[3] if len(sys.argv) > 3 else "female"
    key = os.getenv("SARVAM_API_KEY") or sys.exit("Set SARVAM_API_KEY in your environment or .env")

    with open(path, "rb") as f:
        audio = f.read()
    r = p.interpret(key, audio, os.path.basename(path), target, gender,
                    on_step=lambda s, _: print(f"  {s}"))
    print(f"\n[{p.language_name(r.source_lang)}] {r.transcript}\n\n[{p.language_name(target)}] {r.translation}")

    os.makedirs("output_files", exist_ok=True)
    out = os.path.join("output_files", f"{os.path.splitext(os.path.basename(path))[0]}_{target}.wav")
    with open(out, "wb") as f:
        f.write(r.audio_wav)
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
