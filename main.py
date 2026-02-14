"""
Audio-to-Audio Interpreter Pipeline
Converts audio from one language to another using:
  STT → Translate → TTS
"""

import os
import json
import base64
from sarvamai import SarvamAI

# Initialize client
API_KEY = "sk_s38hjjp8_HYDn5680HYwTsbkplbrSYFvI"
client = SarvamAI(api_subscription_key=API_KEY)

# Supported languages
LANGUAGES = {
    "1": ("hi-IN", "Hindi"),
    "2": ("bn-IN", "Bengali"),
    "3": ("kn-IN", "Kannada"),
    "4": ("ml-IN", "Malayalam"),
    "5": ("mr-IN", "Marathi"),
    "6": ("od-IN", "Odia"),
    "7": ("pa-IN", "Punjabi"),
    "8": ("ta-IN", "Tamil"),
    "9": ("te-IN", "Telugu"),
    "10": ("gu-IN", "Gujarati"),
    "11": ("en-IN", "English"),
}

# TTS speakers per language
SPEAKERS = {
    "hi-IN": "simran",
    "bn-IN": "simran",
    "kn-IN": "simran",
    "ml-IN": "simran",
    "mr-IN": "simran",
    "od-IN": "simran",
    "pa-IN": "simran",
    "ta-IN": "simran",
    "te-IN": "simran",
    "gu-IN": "simran",
    "en-IN": "simran",
}


def speech_to_text(audio_path: str, output_dir: str = "./stt_output") -> tuple[str, str]:
    """
    Convert speech to text using Sarvam AI batch API.
    Returns (transcribed_text, detected_language_code)
    """
    print(f"\n[STT] Processing: {audio_path}")
    
    # Create batch job
    job = client.speech_to_text_job.create_job(
        model="saaras:v3",
        mode="transcribe",
        language_code="unknown",
        with_diarization=False,
        num_speakers=1
    )
    
    # Upload and process
    job.upload_files(file_paths=[audio_path])
    job.start()
    print("[STT] Job started, waiting for completion...")
    job.wait_until_complete()
    
    # Get results
    file_results = job.get_file_results()
    
    if not file_results['successful']:
        raise Exception(f"STT failed: {file_results['failed']}")
    
    # Download outputs - this downloads JSON files with transcripts
    os.makedirs(output_dir, exist_ok=True)
    job.download_outputs(output_dir=output_dir)
    
    # Read the transcript from downloaded JSON file
    # The SDK downloads JSON with filename: <original_filename>.json (e.g., audio.mp3.json)
    transcribed_text = ""
    detected_language = "en-IN"
    
    # Find JSON file matching the input filename
    input_basename = os.path.basename(audio_path)
    expected_json_name = f"{input_basename}.json"
    json_path = os.path.join(output_dir, expected_json_name)
    
    if os.path.exists(json_path):
        print(f"[STT] Reading transcript from: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
        
        # Extract transcript and language from JSON
        transcribed_text = transcript_data.get('transcript', '')
        detected_language = transcript_data.get('language_code', 'en-IN')
        
        # Debug: print the JSON structure if transcript is empty
        if not transcribed_text:
            print(f"[STT] DEBUG - JSON content: {json.dumps(transcript_data, indent=2)[:500]}")
    else:
        print(f"[STT] Expected JSON file not found: {json_path}")
        # List available JSON files for debugging
        json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
        print(f"[STT] Available JSON files: {json_files}")
    
    print(f"[STT] Detected language: {detected_language}")
    print(f"[STT] Transcribed text: {transcribed_text[:100]}..." if len(transcribed_text) > 100 else f"[STT] Transcribed text: {transcribed_text}")
    
    return transcribed_text, detected_language


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """
    Translate text from source language to target language.
    """
    print(f"\n[Translate] {source_lang} → {target_lang}")
    
    response = client.text.translate(
        input=text,
        source_language_code=source_lang,
        target_language_code=target_lang,
        speaker_gender="Male",
        mode="formal",
        model="mayura:v1",
    )
    
    translated_text = response.translated_text
    print(f"[Translate] Result: {translated_text[:100]}..." if len(translated_text) > 100 else f"[Translate] Result: {translated_text}")
    
    return translated_text


def text_to_speech(text: str, target_lang: str, output_path: str) -> str:
    """
    Convert text to speech and save to file.
    Returns the output file path.
    """
    print(f"\n[TTS] Converting to speech in {target_lang}")
    
    speaker = SPEAKERS.get(target_lang, "simran")
    
    response = client.text_to_speech.convert(
        text=text,
        target_language_code=target_lang,
        speaker=speaker,
        pace=1.0,
        speech_sample_rate=22050,
        enable_preprocessing=True,
        model="bulbul:v3"
    )
    
    # Decode base64 audio and save
    audio_data = base64.b64decode(response.audios[0])
    
    with open(output_path, 'wb') as f:
        f.write(audio_data)
    
    print(f"[TTS] Saved to: {output_path}")
    return output_path


def display_languages():
    """Display available languages."""
    print("\nAvailable languages:")
    for key, (code, name) in LANGUAGES.items():
        print(f"  {key}. {name} ({code})")


def get_user_input() -> tuple[str, str]:
    """Get input file and target language from user."""
    # Get input file
    input_file = input("\nEnter path to input audio file (wav/mp3): ").strip()
    
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"File not found: {input_file}")
    
    # Get target language
    display_languages()
    choice = input("\nSelect target language (1-11): ").strip()
    
    if choice not in LANGUAGES:
        raise ValueError(f"Invalid choice: {choice}")
    
    target_lang_code, target_lang_name = LANGUAGES[choice]
    print(f"\nSelected: {target_lang_name} ({target_lang_code})")
    
    return input_file, target_lang_code


def run_pipeline(input_file: str, target_lang: str) -> str:
    """
    Run the full interpreter pipeline.
    Returns path to output audio file.
    """
    print("\n" + "="*50)
    print("Starting Audio-to-Audio Interpreter Pipeline")
    print("="*50)
    
    # Step 1: Speech to Text
    transcribed_text, source_lang = speech_to_text(input_file)
    
    if not transcribed_text:
        raise Exception("No text transcribed from audio")
    
    # Step 2: Translate (skip if same language)
    if source_lang == target_lang:
        print(f"\n[Skip] Source and target language are the same ({source_lang})")
        translated_text = transcribed_text
    else:
        translated_text = translate_text(transcribed_text, source_lang, target_lang)
    
    # Step 3: Text to Speech
    # Generate output filename
    input_basename = os.path.splitext(os.path.basename(input_file))[0]
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output_files")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{input_basename}_{target_lang}.wav")
    
    output_file = text_to_speech(translated_text, target_lang, output_path)
    
    print("\n" + "="*50)
    print("Pipeline Complete!")
    print(f"Output file: {output_file}")
    print("="*50)
    
    return output_file


def main():
    """Main entry point."""
    try:
        input_file, target_lang = get_user_input()
        run_pipeline(input_file, target_lang)
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    main()
