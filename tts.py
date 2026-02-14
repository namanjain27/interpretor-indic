from sarvamai import SarvamAI

client = SarvamAI(
    api_subscription_key="sk_s38hjjp8_HYDn5680HYwTsbkplbrSYFvI",
)

response = client.text_to_speech.convert(
    text="""नमस्ते! Sarvam AI में आपका स्वागत है। """,
    target_language_code="hi-IN",
    speaker="shubh",
    pace=1.1,
    speech_sample_rate=22050,
    enable_preprocessing=True,
    model="bulbul:v3"
)

print(response)