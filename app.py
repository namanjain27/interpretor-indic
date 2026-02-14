"""
Streamlit UI for Audio-to-Audio Interpreter
"""

import os
import json
import base64
import tempfile
import traceback
import streamlit as st
from sarvamai import SarvamAI

# Page config
st.set_page_config(
    page_title="Audio Interpreter",
    page_icon="",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS - Neutral Elegance Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Source+Sans+Pro:wght@300;400;600&display=swap');
    
    .stApp {
        background: linear-gradient(145deg, #FFDBBB 0%, #CCBEB1 100%);
        min-height: 100vh;
    }
    
    .main .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 1rem;
        max-width: 580px;
    }
    
    /* Remove top padding/margin */
    .stApp > header {
        display: none;
    }
    
    div[data-testid="stAppViewContainer"] > div:first-child {
        padding-top: 0;
    }
    
    .app-header {
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .app-header h1 {
        font-family: 'Playfair Display', serif;
        color: #664930;
        font-size: 1.8rem;
        font-weight: 600;
        margin: 0;
    }
    
    .app-header p {
        color: #997E67;
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 0.9rem;
        margin-top: 0.25rem;
    }
    
    .section-label {
        font-family: 'Source Sans Pro', sans-serif;
        font-weight: 600;
        color: #664930 !important;
        font-size: 0.8rem;
        margin-bottom: 0.25rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* File uploader - dark style */
    .stFileUploader > div {
        background: #664930;
        border: none;
        border-radius: 8px;
        padding: 0.5rem;
    }
    
    .stFileUploader > div > div {
        color: #FFDBBB !important;
    }
    
    .stFileUploader label, .stFileUploader span, .stFileUploader p {
        color: #FFDBBB !important;
        font-family: 'Source Sans Pro', sans-serif;
    }
    
    .stFileUploader button {
        background: #997E67 !important;
        color: #FFDBBB !important;
        border: none !important;
    }
    
    /* Selectbox - dark style matching file uploader */
    .stSelectbox > div > div {
        background: #664930 !important;
        border: none;
        border-radius: 8px;
        color: #FFDBBB !important;
    }
    
    .stSelectbox > div > div > div {
        color: #FFDBBB !important;
    }
    
    .stSelectbox label {
        color: #664930 !important;
        font-family: 'Source Sans Pro', sans-serif;
    }
    
    .stSelectbox svg {
        fill: #FFDBBB !important;
    }
    
    /* Selectbox dropdown options */
    div[data-baseweb="popover"] {
        background: #664930 !important;
    }
    
    div[data-baseweb="popover"] li {
        color: #FFDBBB !important;
        background: #664930 !important;
    }
    
    div[data-baseweb="popover"] li:hover {
        background: #997E67 !important;
    }
    
    /* Voice toggle */
    .voice-toggle {
        display: flex;
        background: #664930;
        border-radius: 8px;
        padding: 4px;
        gap: 4px;
    }
    
    .voice-btn {
        flex: 1;
        padding: 8px 16px;
        border: none;
        border-radius: 6px;
        font-family: 'Source Sans Pro', sans-serif;
        font-weight: 500;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.2s ease;
        background: transparent;
        color: #CCBEB1;
    }
    
    .voice-btn.active {
        background: #997E67;
        color: #FFDBBB;
    }
    
    .voice-btn:hover:not(.active) {
        background: rgba(153, 126, 103, 0.3);
    }
    
    /* Toggle switch styling for streamlit */
    .stRadio > div {
        background: #664930;
        border-radius: 8px;
        padding: 0.4rem;
        display: flex;
        flex-direction: row !important;
    }
    
    .stRadio > div > label {
        flex: 1;
        text-align: center;
        padding: 0.4rem 0.8rem;
        border-radius: 6px;
        color: #CCBEB1 !important;
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.2s ease;
        margin: 0 2px;
    }
    
    .stRadio > div > label[data-checked="true"],
    .stRadio > div > label:has(input:checked) {
        background: #997E67;
        color: #FFDBBB !important;
    }
    
    .stRadio > div input {
        display: none;
    }
    
    /* Generate button */
    .stButton > button {
        background: linear-gradient(135deg, #664930 0%, #997E67 100%);
        color: #FFDBBB;
        font-family: 'Source Sans Pro', sans-serif;
        font-weight: 600;
        font-size: 0.95rem;
        padding: 0.6rem 1.5rem;
        border-radius: 8px;
        border: none;
        width: 100%;
        transition: all 0.2s ease;
        margin-top: 0.5rem;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #997E67 0%, #664930 100%);
        box-shadow: 0 4px 12px rgba(102, 73, 48, 0.3);
    }
    
    /* Download button */
    .stDownloadButton > button {
        background: #664930;
        color: #FFDBBB;
        font-family: 'Source Sans Pro', sans-serif;
        font-weight: 600;
        border-radius: 8px;
        border: none;
    }
    
    .stDownloadButton > button:hover {
        background: #997E67;
    }
    
    /* Progress steps */
    .step-box {
        background: #997E67;
        border-left: 3px solid #664930;
        padding: 0.5rem 0.75rem;
        margin: 0.4rem 0;
        border-radius: 0 6px 6px 0;
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 0.85rem;
        color: #FFDBBB;
    }
    
    .step-box.active {
        border-left-color: #FFDBBB;
        background: #664930;
    }
    
    .step-box.complete {
        border-left-color: #5a8a5a;
        background: rgba(90, 138, 90, 0.3);
    }
    
    .step-box .step-title {
        font-weight: 600;
        color: #FFDBBB;
    }
    
    .step-box .step-detail {
        font-size: 0.8rem;
        color: #CCBEB1;
        margin-top: 0.2rem;
    }
    
    .step-box .step-expand {
        font-size: 0.75rem;
        color: #FFDBBB;
        opacity: 0.8;
        margin-top: 0.15rem;
        cursor: pointer;
    }
    
    /* Error box */
    .error-container {
        background: rgba(180, 80, 80, 0.2);
        border: 1px solid #b45050;
        border-radius: 8px;
        padding: 0.75rem;
        margin-top: 0.5rem;
    }
    
    .error-title {
        font-family: 'Source Sans Pro', sans-serif;
        font-weight: 600;
        color: #8b3a3a;
        font-size: 0.9rem;
    }
    
    /* Success box */
    .success-container {
        background: rgba(90, 138, 90, 0.25);
        border: 1px solid #5a8a5a;
        border-radius: 8px;
        padding: 0.6rem;
        margin: 0.4rem 0;
    }
    
    .success-title {
        font-family: 'Source Sans Pro', sans-serif;
        font-weight: 600;
        color: #3d5c3d;
        font-size: 0.9rem;
        text-align: center;
    }
    
    /* Audio player */
    .stAudio {
        margin: 0.4rem 0;
    }
    
    /* Expander */
    .stExpander {
        background: #997E67;
        border: none;
        border-radius: 8px;
    }
    
    .stExpander > div > div > div > p {
        color: #FFDBBB !important;
        font-family: 'Source Sans Pro', sans-serif;
    }
    
    .stExpander svg {
        fill: #FFDBBB !important;
    }
    
    /* Text inside expanders */
    .text-content {
        background: rgba(255, 255, 255, 0.1);
        padding: 0.75rem;
        border-radius: 6px;
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 0.85rem;
        color: #FFDBBB;
        line-height: 1.5;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    
    # /* Hide streamlit branding */
    # #MainMenu {visibility: hidden;}
    # footer {visibility: hidden;}
    # header {visibility: hidden;}
    
    /* Reduce spacing */
    .stMarkdown {
        margin-bottom: 0;
    }
    
    div[data-testid="stVerticalBlock"] > div {
        padding-top: 0;
        padding-bottom: 0;
    }
    
    /* Custom toggle component */
    .toggle-container {
        background: #664930;
        border-radius: 8px;
        padding: 4px;
        display: flex;
        gap: 4px;
    }
    
    .toggle-option {
        flex: 1;
        text-align: center;
        padding: 8px 12px;
        border-radius: 6px;
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 0.85rem;
        color: #CCBEB1;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .toggle-option.selected {
        background: #997E67;
        color: #FFDBBB;
    }
</style>
""", unsafe_allow_html=True)

# Initialize client
API_KEY = "sk_s38hjjp8_HYDn5680HYwTsbkplbrSYFvI"

# Supported languages
LANGUAGES = {
    "Hindi": "hi-IN",
    "Bengali": "bn-IN",
    "Kannada": "kn-IN",
    "Malayalam": "ml-IN",
    "Marathi": "mr-IN",
    "Odia": "od-IN",
    "Punjabi": "pa-IN",
    "Tamil": "ta-IN",
    "Telugu": "te-IN",
    "Gujarati": "gu-IN",
    "English": "en-IN",
}


def speech_to_text(audio_path: str, output_dir: str) -> tuple[str, str]:
    """Convert speech to text using Sarvam AI batch API."""
    client = SarvamAI(api_subscription_key=API_KEY)
    
    job = client.speech_to_text_job.create_job(
        model="saaras:v3",
        mode="transcribe",
        language_code="unknown",
        with_diarization=False,
        num_speakers=1
    )
    
    job.upload_files(file_paths=[audio_path])
    job.start()
    job.wait_until_complete()
    
    file_results = job.get_file_results()
    
    if not file_results['successful']:
        raise Exception(f"STT failed: {file_results['failed']}")
    
    os.makedirs(output_dir, exist_ok=True)
    job.download_outputs(output_dir=output_dir)
    
    input_basename = os.path.basename(audio_path)
    expected_json_name = f"{input_basename}.json"
    json_path = os.path.join(output_dir, expected_json_name)
    
    transcribed_text = ""
    detected_language = "en-IN"
    
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
        transcribed_text = transcript_data.get('transcript', '')
        detected_language = transcript_data.get('language_code', 'en-IN')
    else:
        raise Exception(f"Transcript file not found: {json_path}")
    
    return transcribed_text, detected_language


def translate_text(text: str, source_lang: str, target_lang: str, speaker_gender: str) -> str:
    """Translate text from source language to target language."""
    client = SarvamAI(api_subscription_key=API_KEY)
    
    gender = "Male" if speaker_gender == "shubh" else "Female"
    
    response = client.text.translate(
        input=text,
        source_language_code=source_lang,
        target_language_code=target_lang,
        speaker_gender=gender,
        mode="formal",
        model="mayura:v1",
    )
    
    return response.translated_text


def text_to_speech(text: str, target_lang: str, speaker: str) -> bytes:
    """Convert text to speech and return audio bytes."""
    client = SarvamAI(api_subscription_key=API_KEY)
    
    response = client.text_to_speech.convert(
        text=text,
        target_language_code=target_lang,
        speaker=speaker,
        pace=1.0,
        speech_sample_rate=22050,
        enable_preprocessing=True,
        model="bulbul:v3"
    )
    
    return base64.b64decode(response.audios[0])


def run_pipeline(audio_bytes: bytes, filename: str, target_lang: str, speaker: str, step_placeholders: dict) -> tuple[bytes, dict]:
    """Run the full interpreter pipeline. Returns audio data and step details."""
    
    details = {
        "source_lang": "",
        "transcript": "",
        "translated": "",
        "skipped_translation": False
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save uploaded file
        input_path = os.path.join(temp_dir, filename)
        with open(input_path, 'wb') as f:
            f.write(audio_bytes)
        
        stt_output_dir = os.path.join(temp_dir, "stt_output")
        
        # Step 1: Speech to Text
        step_placeholders["step1"].markdown(
            '<div class="step-box active"><span class="step-title">Step 1: Speech to Text</span><div class="step-detail">Processing audio...</div></div>',
            unsafe_allow_html=True
        )
        
        transcribed_text, source_lang = speech_to_text(input_path, stt_output_dir)
        
        if not transcribed_text:
            raise Exception("No text transcribed from audio")
        
        details["source_lang"] = source_lang
        details["transcript"] = transcribed_text
        
        # Step 2: Translate
        if source_lang == target_lang:
            details["skipped_translation"] = True
            details["translated"] = transcribed_text
            translated_text = transcribed_text
        else:
            step_placeholders["step2"].markdown(
                f'<div class="step-box active"><span class="step-title">Step 2: Translation</span><div class="step-detail">{source_lang} to {target_lang}...</div></div>',
                unsafe_allow_html=True
            )
            
            translated_text = translate_text(transcribed_text, source_lang, target_lang, speaker)
            details["translated"] = translated_text
        
        # Step 3: Text to Speech
        step_placeholders["step3"].markdown(
            f'<div class="step-box active"><span class="step-title">Step 3: Text to Speech</span><div class="step-detail">Generating with {speaker} voice...</div></div>',
            unsafe_allow_html=True
        )
        
        audio_data = text_to_speech(translated_text, target_lang, speaker)
        
        return audio_data, details


def main():
    # Initialize session state for voice toggle
    if 'voice' not in st.session_state:
        st.session_state.voice = 'simran'
    
    # Header
    st.markdown('''
    <div class="app-header">
        <h1>Audio Interpreter</h1>
        <p>Convert audio from one language to another</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # File upload
    st.markdown('<p class="section-label">Input Audio</p>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload audio file",
        type=["wav", "mp3"],
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        st.audio(uploaded_file, format=f"audio/{uploaded_file.name.split('.')[-1]}")
    
    # Two columns for language and voice
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<p class="section-label">Target Language</p>', unsafe_allow_html=True)
        target_language = st.selectbox(
            "Select target language",
            options=list(LANGUAGES.keys()),
            index=0,
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown('<p class="section-label">Voice</p>', unsafe_allow_html=True)
        # Toggle button using columns
        toggle_col1, toggle_col2 = st.columns(2)
        with toggle_col1:
            if st.button("Female", use_container_width=True, type="primary" if st.session_state.voice == 'simran' else "secondary"):
                st.session_state.voice = 'simran'
                st.rerun()
        with toggle_col2:
            if st.button("Male", use_container_width=True, type="primary" if st.session_state.voice == 'shubh' else "secondary"):
                st.session_state.voice = 'shubh'
                st.rerun()
    
    # Generate button
    if st.button("Generate Translated Audio", use_container_width=True, key="generate"):
        if not uploaded_file:
            st.error("Please upload an audio file first")
            return
        
        # Create placeholders for each step
        step_placeholders = {
            "step1": st.empty(),
            "step2": st.empty(),
            "step3": st.empty(),
        }
        
        # Initialize step boxes
        step_placeholders["step1"].markdown(
            '<div class="step-box"><span class="step-title">Step 1: Speech to Text</span><div class="step-detail">Waiting...</div></div>',
            unsafe_allow_html=True
        )
        step_placeholders["step2"].markdown(
            '<div class="step-box"><span class="step-title">Step 2: Translation</span><div class="step-detail">Waiting...</div></div>',
            unsafe_allow_html=True
        )
        step_placeholders["step3"].markdown(
            '<div class="step-box"><span class="step-title">Step 3: Text to Speech</span><div class="step-detail">Waiting...</div></div>',
            unsafe_allow_html=True
        )
        
        result_container = st.container()
        
        try:
            target_lang_code = LANGUAGES[target_language]
            speaker = st.session_state.voice
            audio_bytes = uploaded_file.read()
            
            result_audio, details = run_pipeline(
                audio_bytes=audio_bytes,
                filename=uploaded_file.name,
                target_lang=target_lang_code,
                speaker=speaker,
                step_placeholders=step_placeholders
            )
            
            # Update step 1 with expander
            step_placeholders["step1"].empty()
            with step_placeholders["step1"].container():
                with st.expander(f"Step 1: Speech to Text - Detected: {details['source_lang']}", expanded=False):
                    st.markdown(f'<div class="text-content">{details["transcript"]}</div>', unsafe_allow_html=True)
            
            # Update step 2 with expander
            step_placeholders["step2"].empty()
            with step_placeholders["step2"].container():
                if details["skipped_translation"]:
                    st.markdown('<div class="step-box complete"><span class="step-title">Step 2: Translation</span><div class="step-detail">Skipped (same language)</div></div>', unsafe_allow_html=True)
                else:
                    with st.expander(f"Step 2: Translation - {details['source_lang']} to {target_lang_code}", expanded=False):
                        st.markdown(f'<div class="text-content">{details["translated"]}</div>', unsafe_allow_html=True)
            
            # Update step 3
            step_placeholders["step3"].markdown(
                '<div class="step-box complete"><span class="step-title">Step 3: Text to Speech</span><div class="step-detail">Audio generated successfully</div></div>',
                unsafe_allow_html=True
            )
            
            # Success
            with result_container:
                st.markdown('<div class="success-container"><p class="success-title">Translation Complete</p></div>', unsafe_allow_html=True)
                
                st.markdown('<p class="section-label">Preview</p>', unsafe_allow_html=True)
                st.audio(result_audio, format="audio/wav")
                
                output_filename = f"{os.path.splitext(uploaded_file.name)[0]}_{target_lang_code}.wav"
                st.download_button(
                    label="Download Translated Audio",
                    data=result_audio,
                    file_name=output_filename,
                    mime="audio/wav",
                    use_container_width=True
                )
            
        except Exception as e:
            error_message = str(e)
            error_traceback = traceback.format_exc()
            
            with result_container:
                st.markdown('<div class="error-container"><p class="error-title">Error Occurred</p></div>', unsafe_allow_html=True)
                st.error(f"{error_message}")
                
                with st.expander("Error Details (for developers)"):
                    error_text = f"Error: {error_message}\n\nTraceback:\n{error_traceback}"
                    st.code(error_traceback, language="python")
                    st.text_area(
                        "Copy this error",
                        value=error_text,
                        height=120,
                        label_visibility="collapsed"
                    )


if __name__ == "__main__":
    main()
