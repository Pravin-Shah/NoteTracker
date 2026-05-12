import os
import google.generativeai as genai

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    # Try to load from .env
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("No API key found.")
else:
    genai.configure(api_key=api_key)
    print("Available models supporting generateContent:")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name} (Display: {m.display_name})")
    except Exception as e:
        print(f"Error listing models: {e}")
