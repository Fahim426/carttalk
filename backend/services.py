import os
from google import genai
from db import get_products, create_order, get_orders
from gtts import gTTS
from io import BytesIO

class GeminiService:
    def __init__(self):
        # We assume GEMINI_API_KEY is set in environment
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
             print("Warning: GEMINI_API_KEY not found in environment variables.")
        self.client = genai.Client(api_key=api_key)
        self.histories = {} # To store conversation history for each call_id
    
    async def process_audio(self, call_id, audio_data, inventory_context):
        """Send audio to Gemini Live API, get response and convert to audio"""
        try:
            # Initialize history for this call if not exists
            if call_id not in self.histories:
                self.histories[call_id] = []
            
            # Construct current turn history
            
            # System Instruction (always first)
            system_instruction = """
You are CartTalk, a bilingual grocery assistant (English and Malayalam). 
Your top priority is to AUTO-DETECT the user's language and respond in the SAME language.

INSTRUCTIONS:
1. Listen to the audio.
2. EXTRACT what the user said into a line starting with "TRANSCRIPT: ".
3. Virtual Cart: Keep track of what the user wants to buy.
4. GENERATE your response for the user into a line starting with "RESPONSE: ".
5. If the user speaks English, reply in English.
6. If the user speaks Malayalam, reply in Malayalam.
7. Manage the shopping cart based on user requests (prices are in INR).
8. CONSULTATIVE SELLING: If the user asks for a category (e.g., "protein", "snacks") or mentions a problem (e.g., "headache"), SUGGEST relevant items from the inventory based on their Category or general knowledge.
9. Keep responses short (under 2 sentences).
10. CHECKOUT PHASE: After the user confirms the order or asks for the bill, YOU MUST ASK for their NAME and DELIVERY ADDRESS.
11. SAVING DATA: If the user provides Name and Address, output a separate line: "DATA: {\"name\": \"...\", \"address\": \"...\", \"cart\": [{\"id\": 123, \"qty\": 2, \"price\": 50}, ...]}". 
    -- IMPORTANT: You MUST include the 'cart' items with their IDs and Quantities.
    -- IMPORTANT: Use DOUBLE QUOTES for JSON keys and strings. Do not use single quotes in the JSON.
12. CONFIRMATION: Once you have Name and Address and Cart, output "COMMAND: CONFIRM_ORDER" to save it.
13. CLOSING: After successful order confirmation, say a natural "Thank you" message in the user's language.
14. **AUDIO OUTPUT RULES**: Do NOT read out 'ID', 'JSON status' or technical details (like 'ID 12'). Speak NATURALLY.

Inventory:
""" + inventory_context

            # specific instruction for the first turn
            if not self.histories[call_id]:
                 system_instruction += "\n\nSPECIAL INSTRUCTION: This is the first interaction. You MUST greet the user with 'Welcome to CartTalk! How can I help you?' (or its Malayalam equivalent if the user speaks Malayalam)."

            history_text = "\n".join(self.histories[call_id])
            
            final_prompt = system_instruction + "\n\nCONVERSATION HISTORY:\n" + history_text + "\n\nCURRENT AUDIO INPUT:"
            
            # Request
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[
                    {"role": "user", "parts": [
                        {"text": final_prompt},
                        {"inline_data": {"mime_type": "audio/webm", "data": audio_data}}
                    ]}
                ]
            )
            
            raw_text = response.text
            if not raw_text:
                return b""

            print(f"Raw Gemini Response: {raw_text[:100]}...")

            # Parse Output
            transcript = ""
            ai_response = raw_text
            extracted_data = None
            command = None
            
            import re
            import json
            
            # Improved Regex to handle nested JSON and newlines
            t_match = re.search(r'TRANSCRIPT:\s*(.*)', raw_text, re.IGNORECASE)
            # Capture DATA section: from DATA: until COMMAND: or End of String (DOTALL)
            d_match = re.search(r'DATA:\s*(.*?)(?=\s*COMMAND:|\Z)', raw_text, re.DOTALL | re.IGNORECASE)
            # Capture COMMAND:
            c_match = re.search(r'COMMAND:\s*(\w+)', raw_text, re.IGNORECASE)
            # Response is everything else, or captured specifically
            r_match = re.search(r'RESPONSE:\s*(.*?)(?=\s*DATA:|\s*COMMAND:|\Z)', raw_text, re.DOTALL | re.IGNORECASE)
            
            if t_match:
                transcript = t_match.group(1).strip()
            
            if r_match:
                ai_response = r_match.group(1).strip()
            if not ai_response and not t_match and not d_match and not c_match:
                ai_response = raw_text
            elif not ai_response and t_match:
                 ai_response = raw_text.replace(t_match.group(0), '')
            
            if d_match:
                json_str = d_match.group(1).strip()
                # Remove potential markdown code blocks
                json_str = json_str.replace('```json', '').replace('```', '').strip()
                
                try:
                    # 1. Try direct load
                    extracted_data = json.loads(json_str)
                except json.JSONDecodeError:
                    try:
                        # 2. Fix common AI JSON errors
                        # Replace single quotes with double quotes
                        # But be careful not to break apostrophes in text like "O'Neil" if they are inside double quotes already? 
                        # Simple approach: if it looks like python dict str, use ast.literal_eval or replace ' with "
                        import ast
                        extracted_data = ast.literal_eval(json_str)
                    except Exception:
                         try:
                            # 3. Last resort brute force fix
                            json_str = json_str.replace("'", '"')
                            # Fix booleans
                            json_str = json_str.replace("True", "true").replace("False", "false").replace("None", "null")
                            extracted_data = json.loads(json_str)
                         except Exception as e:
                            print(f"Final JSON Parse Error: {e} | Content: {json_str}")
                
                if extracted_data:
                    print(f"Extracted Data: {extracted_data}")
                    self.session_data = getattr(self, 'session_data', {})
                    if call_id not in self.session_data: self.session_data[call_id] = {}
                    self.session_data[call_id].update(extracted_data)

            if c_match:
                command = c_match.group(1).strip()
                if command == 'CONFIRM_ORDER':
                    # Save to DB
                    print("Executing Order Confirmation...")
                    session = getattr(self, 'session_data', {}).get(call_id, {})
                    
                    order_payload = {
                        'phone': 'VoiceUser',
                        'name': session.get('name', 'Unknown'),
                        'address': session.get('address', 'Unknown'),
                        'total': 0.0,
                        'language': 'en', 
                        'transcript': history_text,
                        'items': session.get('cart', [])
                    }
                    create_order(order_payload)
                    print("Order Saved to DB")

            # Update History
            if transcript:
                self.histories[call_id].append(f"User: {transcript}")
            self.histories[call_id].append(f"Model: {ai_response}")
            
            # Keep history manageable (last 10 turns)
            if len(self.histories[call_id]) > 20:
                self.histories[call_id] = self.histories[call_id][-20:]

            # Clean text for TTS
            clean_text = re.sub(r'\*+', '', ai_response)
            clean_text = re.sub(r'[#`]', '', clean_text)
            clean_text = clean_text.replace('RESPONSE:', '').strip()
            
            # AGGRESSIVE CLEANUP: Remove DATA and COMMAND blocks from spoken text
            clean_text = re.sub(r'DATA:\s*\{.*?\}', '', clean_text, flags=re.DOTALL | re.IGNORECASE)
            clean_text = re.sub(r'COMMAND:\s*\w+', '', clean_text, flags=re.IGNORECASE)
            
            # Remove any residual TRANSCRIPT lines if they leaked
            clean_text = re.sub(r'TRANSCRIPT:.*', '', clean_text, flags=re.IGNORECASE)

            # NEW: Remove ID references like (ID: 12) or [ID: 12] spoken by mistake
            clean_text = re.sub(r'[\[\(]ID:?\s*\d+[\]\)]', '', clean_text, flags=re.IGNORECASE)
            clean_text = re.sub(r'ID\s*\d+', '', clean_text, flags=re.IGNORECASE)
            
            clean_text = clean_text.strip()
            
            # Detect language
            lang = 'en'
            if any('\u0D00' <= char <= '\u0D7F' for char in clean_text):
                lang = 'ml'

            # clean text for TTS
            print(f"Generating audio for: '{clean_text[:50]}...' in lang: {lang}")
            
            tts = gTTS(text=clean_text, lang=lang)
            fp = BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            audio_bytes = fp.read()
            print(f"Audio generated, size: {len(audio_bytes)} bytes")
            
            return {
                "user_transcript": transcript,
                "ai_text": clean_text,
                "audio": audio_bytes
            }

        except Exception as e:
            print(f"Gemini/Audio API Error: {e}")
            import traceback
            traceback.print_exc()
            return None

class InventoryService:
    def __init__(self):
        # We re-fetch products to ensure freshness or cache it
        pass
    
    def get_context(self):
        """Return inventory context for Gemini"""
        products = get_products()
        # Include ID and Category for AI to track and recommend
        return "\n".join([f"[ID: {p['id']}] {p['name_en']}/{p['name_ml']} ({p.get('category','General')}): ₹{p['price']}, Stock: {p['stock']}" for p in products])
    
    def list_all(self):
        return get_products()

class OrderService:
    def create_order(self, data):
        """Save order to database"""
        return create_order(data)
    
    def get_all(self):
        """Get all orders"""
        return get_orders()
