# Audio-to-Audio Interpreter - Implementation Plan

## Overview
Build a simple pipeline that takes an audio file (wav/mp3), transcribes it, translates to a user-specified language, and generates output audio in the target language.

## Pipeline Flow

```
Input Audio (wav/mp3)
        ↓
   [1] STT (Speech-to-Text)
        ↓
   Detected Text + Source Language
        ↓
   [2] Translate
        ↓
   Translated Text
        ↓
   [3] TTS (Text-to-Speech)
        ↓
Output Audio File (wav)
```

## Components

### 1. Speech-to-Text (stt.py)
- Uses Sarvam AI `speech_to_text_job` API
- Auto-detects source language (`language_code="unknown"`)
- Model: `saaras:v3`
- Returns transcribed text with language info

### 2. Translation (translate.py)
- Uses Sarvam AI `text.translate` API
- Model: `mayura:v1`
- Requires: source_language_code, target_language_code

### 3. Text-to-Speech (tts.py)
- Uses Sarvam AI `text_to_speech.convert` API
- Model: `bulbul:v3`
- Returns base64 encoded audio

## Supported Languages
- Hindi (hi-IN)
- Bengali (bn-IN)
- Kannada (kn-IN)
- Malayalam (ml-IN)
- Marathi (mr-IN)
- Odia (od-IN)
- Punjabi (pa-IN)
- Tamil (ta-IN)
- Telugu (te-IN)
- Gujarati (gu-IN)
- English (en-IN)

## Implementation Steps

1. **User Input**
   - Accept input audio file path
   - Display supported languages
   - Get user's target language choice

2. **STT Stage**
   - Create batch job for single file
   - Upload and process audio
   - Extract transcribed text and detected language

3. **Translation Stage**
   - Pass transcribed text to translate API
   - Use detected language as source
   - User-selected language as target

4. **TTS Stage**
   - Convert translated text to speech
   - Decode base64 audio response
   - Save as output file

5. **Output**
   - Save final audio to `output_files/` directory
   - Display success message with file path

## File Structure
```
interpretor-app/
├── main.py          # Pipeline orchestration
├── stt.py           # Speech-to-text component
├── translate.py     # Translation component
├── tts.py           # Text-to-speech component
├── input_files/     # Place input audio here
└── output_files/    # Generated output audio
```

