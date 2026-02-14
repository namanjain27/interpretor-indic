from sarvamai import SarvamAI

client = SarvamAI(
    api_subscription_key="sk_s38hjjp8_HYDn5680HYwTsbkplbrSYFvI",
)

response = client.text.translate(
    input="""hello bhaiya! how are you doing""",
    source_language_code="en-IN",
    target_language_code="hi-IN",
    speaker_gender="Male",
    mode="formal",
    model="mayura:v1",
    enable_preprocessing=False,
    numerals_format="native"
)

print(response)