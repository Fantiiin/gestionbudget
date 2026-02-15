"""Test ciblé modèle par modèle."""
import os
import time
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODELS_TO_TEST = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
]

for model_name in MODELS_TO_TEST:
    print(f"\n--- Test {model_name} ---")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Dis juste OK")
        print(f"  ✓ OK => {response.text.strip()[:50]}")
    except Exception as e:
        err = str(e)
        if "429" in err:
            print(f"  ✗ 429 Rate limit")
        else:
            print(f"  ✗ {err[:120]}")
    time.sleep(2)

print("\nTerminé.")
