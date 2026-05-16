import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: No API key found in .env")
else:
    print(f"API Key found: {api_key[:5]}...{api_key[-5:]}")

try:
    client = genai.Client(api_key=api_key)
    print("\nAttempting to list ALL models...")
    models = list(client.models.list())
    if not models:
        print("No models returned by list().")
    for m in models:
        print(f"- Name: {m.name} | Display: {m.display_name} | Methods: {m.supported_generation_methods}")
except Exception as e:
    print(f"\nFATAL ERROR while listing models: {e}")
