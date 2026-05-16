"""
services.py
Core AI integration module for CartTalk.
Handles the interaction with Google Gemini 2.0 Flash, including
parsing user intent, maintaining sliding window context,
managing shopping cart state, and generating Neural TTS audio.
"""
import os
from datetime import datetime
from google import genai
from db import get_products, create_order, get_orders
from db import validate_cart_stock
try:
    import edge_tts
    USE_EDGE_TTS = True
    print("Using edge-tts (Neural voices)")
except ImportError:
    USE_EDGE_TTS = False
    print("edge-tts not found, falling back to gTTS")
from gtts import gTTS
from io import BytesIO

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.histories = {} 
        self.summaries = {} 

    async def process_audio(self, call_id, audio_data, inventory_context, user_id=None):
        """Processes binary audio input (Legacy Support)"""
        try:
            prompt = self._build_prompt(call_id, inventory_context, user_id)
            response = await self.client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    {"role": "user", "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": "audio/webm", "data": audio_data}}
                    ]}
                ]
            )
            return await self._handle_ai_logic(call_id, response.text, user_id)
        except Exception as e:
            return self._handle_error(e)

    async def process_text(self, call_id, user_text, inventory_context, user_id=None):
        """Processes high-speed text input from browser STT (Hybrid Architecture)"""
        try:
            prompt = self._build_prompt(call_id, inventory_context, user_id)
            # We append the user_text directly to the prompt to maintain the single-request flow
            full_input = f"{prompt}\n\nUSER INPUT: {user_text}"
            response = await self.client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=[{"role": "user", "parts": [{"text": full_input}]}]
            )
            return await self._handle_ai_logic(call_id, response.text, user_id)
        except Exception as e:
            return self._handle_error(e)

    def _build_prompt(self, call_id, inventory_context, user_id):
        if call_id not in self.histories:
            self.histories[call_id] = []
        
        now = datetime.now()
        time_context = now.strftime("%I:%M %p")

        # ADVANCED NLP & PERSONALITY SETTINGS
        system_instruction = f"""
You are the voice of CartTalk, a sophisticated and helpful bilingual personal shopper.
Time: {time_context}

PERSONALITY:
- Tone: Professional, warm, and highly efficient (like a premium store assistant).
- Natural Flow: Use natural fillers and transitions. Avoid sounding like a bot.
- Language: Use high-standard, natural Malayalam. 
  * CRITICAL: Never use "കൊട്ട" (Kotta) or "ബാസ്കറ്റ്". Always use the English word "Cart" (കാർട്ട്) even in Malayalam sentences.
  * Example: "നിങ്ങളുടെ Cart-ൽ ഇത് ചേർത്തിട്ടുണ്ട്" instead of "കൊട്ടയിൽ ഇട്ടിട്ടുണ്ട്".

RULES:
1. BILINGUAL ADAPTABILITY: You MUST detect the language the user is speaking and reply in that EXACT same language. If the user speaks English, you MUST reply entirely in English. If the user speaks Malayalam, reply in natural, high-standard Malayalam.
2. PROACTIVITY (RECIPES): If the user mentions a recipe or dish (e.g., "Chicken Curry", "Sambar"), act as an expert chef and shopper. Instantly identify the main protein/vegetable, appropriate oil, and 3-4 key spices from the inventory. Add them all to the Cart immediately in one batch. Inform the user gracefully: "I've added the essentials for Chicken Curry to your Cart."
3. QUANTITY CONFIRMATION: When a user asks for a product but does not specify the amount, you MUST ask them for the specific quantity or weight (e.g., "How many kilograms of Tomatoes would you like?"). Do NOT assume a default quantity. Only add the item to the cart after they confirm the amount.
4. BRAND AMBIGUITY: If a user asks for a generic product (e.g., "Milk" or "Rice") and there are multiple brands or specific varieties of that product available in the Inventory, you MUST ask the user which specific one they prefer before adding it to the cart. Do NOT guess or pick one arbitrarily.
5. TERMINOLOGY: Consistently use the word "Cart" (കാർട്ട്) for the shopping list.
6. CROSS-SELL BEFORE CHECKOUT: When the user indicates they are done shopping, BEFORE calculating the total and asking for checkout confirmation, you MUST check the "Frequent" or "Essentials" items provided in your system instructions. Compare them against the items currently in the Cart. If there are frequent items that are NOT YET in the Cart, gently ask the user if they want to add those specific missing items (e.g., "I see you usually buy Milk, would you like to add it?"). DO NOT suggest items they have already added. Only proceed to the final checkout AFTER they respond to this suggestion.
7. CHECKOUT PROCESS: When the user is ready to finalize the order (after responding to your cross-sell), DO NOT use COMMAND: CONFIRM_ORDER immediately. First, calculate the exact Grand Total using the prices from the Inventory, state the total amount clearly to the user, and ask for their final confirmation (e.g., "Your total is ₹250. Shall I confirm the order?"). Only use COMMAND: CONFIRM_ORDER *after* they explicitly say "Yes" or "Confirm".

OUTPUT FORMAT:
TRANSCRIPT: [Translate the user's exact words into English. Always write this in English, even if the user spoke Malayalam]
DATA: ```json
{{
  "cart": [
    {{"id": 101, "name": "Red Onion", "quantity": 1}}
  ]
}}
```
COMMAND: UPDATE_CART | CONFIRM_ORDER | NONE
RESPONSE_TEXT: [Translate your reply entirely into English for the screen display.]
RESPONSE_AUDIO: [Write your natural reply in the language the user spoke. If Malayalam, CRITICAL: You MUST transliterate all English product names into Malayalam script (e.g. write 'ആപ്പിൾ' instead of 'Apple', 'ബനാന' instead of 'Banana') so the Malayalam TTS pronounces them perfectly.]

CRITICAL RULES:
1. PERSISTENCE: Always include the FULL existing cart in the DATA section. Never return an empty cart unless the user explicitly says "Clear my cart" or "Remove everything".
2. IDENTIFIERS: Always use the #ID from the inventory context for the "id" field.
3. QUANTITY FORMAT: The "quantity" field MUST be a pure decimal number representing standard units (Kg or pieces). If the user asks for "500 grams" or "half kg", write 0.5. If they ask for "250g", write 0.25. Never write 500 or use text.
Inventory:
{inventory_context}
"""
        # User History (Concise)
        if user_id:
            from db import get_user_frequent_items, get_user_monthly_essentials
            freq = get_user_frequent_items(user_id)
            if freq: system_instruction += f"\nFrequent: [{', '.join([i['name'] for i in freq])}]"
            ess = get_user_monthly_essentials(user_id)
            if ess: system_instruction += f"\nEssentials: [{', '.join([i['name'] for i in ess])}]"

        if not self.histories[call_id]:
            msg = "Welcome back to CartTalk!" if user_id else "Welcome to CartTalk!"
            system_instruction += f"\n\nSPECIAL INSTRUCTION: This is the START of the call. Regardless of the input language, you MUST respond ONLY in ENGLISH for this turn. Start exactly with '{msg}' then ask how you can help. Do NOT use Malayalam in this turn."

        summary = f"Summary: {self.summaries.get(call_id, '')}\n" if call_id in self.summaries else ""
        return system_instruction + "\n\n" + summary + "Recent Chat:\n" + "\n".join(self.histories[call_id])

    async def _handle_ai_logic(self, call_id, raw_text, user_id):
        if not raw_text: return None
        print("Gemini response received.")

        import re
        import json
        
        # Sections
        t_match = re.search(r'TRANSCRIPT:\s*(.*)', raw_text, re.IGNORECASE)
        d_match = re.search(r'DATA:\s*(.*?)(?=\s*COMMAND:|\Z)', raw_text, re.DOTALL | re.IGNORECASE)
        c_match = re.search(r'COMMAND:\s*(\w+)', raw_text, re.IGNORECASE)
        
        # New split responses for screen vs audio
        r_text_match = re.search(r'RESPONSE_TEXT:\s*(.*?)(?=\s*RESPONSE_AUDIO:|\Z)', raw_text, re.DOTALL | re.IGNORECASE)
        r_audio_match = re.search(r'RESPONSE_AUDIO:\s*(.*)', raw_text, re.DOTALL | re.IGNORECASE)
        
        # Fallback to RESPONSE if the model ignores the new prompt instructions
        if not r_text_match and not r_audio_match:
            r_fallback = re.search(r'RESPONSE:\s*(.*)', raw_text, re.DOTALL | re.IGNORECASE)
            ai_response = r_fallback.group(1).strip() if r_fallback else raw_text
            ai_text = ai_response
            ai_audio = ai_response
        else:
            ai_text = r_text_match.group(1).strip() if r_text_match else ""
            ai_audio = r_audio_match.group(1).strip() if r_audio_match else ai_text

        transcript = t_match.group(1).strip() if t_match else ""
        
        # Remove tags from ai_text if regex missed
        ai_text = re.sub(r'TRANSCRIPT:.*?\n', '', ai_text, flags=re.DOTALL | re.IGNORECASE)
        ai_text = re.sub(r'DATA:.*?```', '', ai_text, flags=re.DOTALL | re.IGNORECASE)
        ai_text = re.sub(r'COMMAND:.*?\n', '', ai_text, flags=re.IGNORECASE)
        ai_text = ai_text.replace('RESPONSE_TEXT:', '').strip()
        ai_text = re.sub(r'```.*', '', ai_text, flags=re.DOTALL).strip()
        
        ai_audio = ai_audio.replace('RESPONSE_AUDIO:', '').strip()

        # Session Data Management
        self.session_data = getattr(self, 'session_data', {})
        if call_id not in self.session_data: self.session_data[call_id] = {}
        
        if d_match:
            json_str = d_match.group(1).strip().replace('```json', '').replace('```', '').strip()
            try:
                extracted = json.loads(json_str)
                self.session_data[call_id].update(extracted)
                
                # ── STOCK VALIDATION: Clamp cart to live DB stock ──
                raw_cart = self.session_data[call_id].get('cart', [])
                if raw_cart:
                    stock_check = validate_cart_stock(raw_cart)
                    self.session_data[call_id]['cart'] = stock_check['valid_cart']
                    self.session_data[call_id]['stock_violations'] = stock_check['violations']
                    if stock_check['violations']:
                        viol_names = ', '.join(
                            f"{v['name']} (asked {v['requested']}, only {v['available']} available)"
                            for v in stock_check['violations']
                        )
                        print(f"[STOCK GUARD] Violations found: {viol_names}")
                else:
                    self.session_data[call_id]['stock_violations'] = []

                # Enrich cart with live prices
                from db import get_products
                db_products = {p['id']: p['price'] for p in get_products()}
                for item in self.session_data[call_id].get('cart', []):
                    if isinstance(item, dict):
                        pid_raw = item.get('id') or item.get('product_id')
                        try:
                            if pid_raw is not None and int(pid_raw) in db_products:
                                item['price'] = db_products[int(pid_raw)]
                        except (ValueError, TypeError):
                            pass
            except Exception as parse_err:
                print(f"[JSON PARSE ERROR] {parse_err}")

        command = c_match.group(1).strip() if c_match else "NONE"
        if command in ['UPDATE_CART', 'CONFIRM_ORDER'] and user_id:
            from db import save_cart
            cart_data = self.session_data[call_id].get('cart', [])
            if isinstance(cart_data, list):
                # Clean cart: only keep dicts with an ID
                clean_cart = [
                    item for item in cart_data 
                    if isinstance(item, dict) and (item.get('id') or item.get('product_id') or item.get('item_id'))
                ]
                save_cart(user_id, clean_cart)
                # Update session with cleaned cart
                self.session_data[call_id]['cart'] = clean_cart
            
        if command == 'CONFIRM_ORDER':
            await self._execute_order(call_id, user_id)

        # Update History
        if transcript: self.histories[call_id].append(f"User: {transcript}")
        self.histories[call_id].append(f"Model: {ai_text}")

        # Keep history manageable with sliding window + background summarization
        MAX_RECENT = 12
        if len(self.histories[call_id]) > MAX_RECENT + 6:
            to_summarize = self.histories[call_id][:-MAX_RECENT]
            self.histories[call_id] = self.histories[call_id][-MAX_RECENT:]
            
            async def run_summary(cid, entries):
                try:
                    text = "\n".join(entries)
                    resp = await self.client.aio.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=[{"role": "user", "parts": [{"text": f"Summarize short: {text}"}]}]
                    )
                    self.summaries[cid] = (self.summaries.get(cid, '') + "\n" + resp.text).strip()
                except: pass

            import asyncio
            asyncio.create_task(run_summary(call_id, to_summarize))

        # Clean for TTS
        clean_text = re.sub(r'\(.*?\)', '', ai_text)
        clean_text = re.sub(r'[#\*`]', '', clean_text).strip()
        
        clean_audio = re.sub(r'\(.*?\)', '', ai_audio)
        clean_audio = re.sub(r'[#\*`]', '', clean_audio).strip()

        return {
            "user_transcript": transcript,
            "ai_text": clean_text,
            "ai_audio": clean_audio,
            "terminate": (command == 'CONFIRM_ORDER'),
            "cart": self.session_data[call_id].get('cart', []),
            "stock_violations": self.session_data[call_id].get('stock_violations', [])
        }

    async def _execute_order(self, call_id, user_id):
        session = self.session_data.get(call_id, {})
        from db import get_products, create_order, validate_cart_stock

        # BUG 4 FIX: Re-validate stock one final time before committing the order
        # (stock may have changed since the cart was built, e.g. concurrent users)
        final_stock_check = validate_cart_stock(session.get('cart', []))
        if final_stock_check['violations']:
            viol_names = ', '.join(f"{v['name']}" for v in final_stock_check['violations'])
            print(f"[ORDER GUARD] Final stock check found violations at checkout: {viol_names}")
        confirmed_cart = final_stock_check['valid_cart']

        db_products = {p['id']: p['price'] for p in get_products()}
        valid_cart = []
        total = 0
        for item in confirmed_cart:
            if not isinstance(item, dict):
                print(f"Skipping malformed order item: {item}")
                continue

            pid_raw = item.get('id') or item.get('item_id') or item.get('product_id')
            try:
                if pid_raw is not None:
                    actual_pid = int(pid_raw)
                    if actual_pid in db_products:
                        price = db_products[actual_pid]
                        raw_qty = str(item.get('quantity', item.get('qty', 1)))
                        import re
                        q_match = re.search(r'[\d\.]+', raw_qty)
                        qty = float(q_match.group()) if q_match else 1.0
                        total += price * qty
                        item['price'] = price
                        item['id'] = actual_pid
                        valid_cart.append(item)
            except (ValueError, TypeError):
                print(f"Skipping item with invalid ID: {pid_raw}")
                continue

        order_payload = {
            'phone': user_id or 'VoiceUser',
            'name': session.get('name', 'Guest'),
            'address': session.get('address', 'Unknown'),
            'total': round(total, 2),
            'items': valid_cart,
            'language': 'en',
            'transcript': "\n".join(self.histories[call_id])
        }
        create_order(order_payload)
        from ws_manager import admin_ws_manager
        await admin_ws_manager.broadcast({"type": "NEW_ORDER"})


    def _handle_error(self, e):
        """Centralized AI error handler with detailed logging"""
        import traceback
        error_msg = f"Gemini API Error: {str(e)}"
        print(f"CRITICAL ERROR: {error_msg}")
        with open("error_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {error_msg}\n{traceback.format_exc()}\n{'-'*40}\n")

        # BUG 8 FIX: Return all keys that main.py expects, not just a subset
        return {
            "user_transcript": "",
            "ai_text": "I'm sorry, I'm having a bit of trouble connecting right now. Please try again.",
            "ai_audio": "I'm sorry, I'm having a bit of trouble connecting right now. Please try again.",
            "cart": None,
            "stock_violations": [],
            "terminate": False,
            "command": "NONE"
        }
    @staticmethod
    async def generate_tts(text):
        """Generate TTS audio from text. Returns bytes or None."""
        import re

        # Detect language with a bias towards Malayalam if mixed
        # (English voices completely fail on Malayalam Unicode characters)
        lang = 'en'
        ml_chars = sum(1 for c in text if '\u0D00' <= c <= '\u0D7F')
        
        # If more than 5% of the string is Malayalam, or if it contains any ML characters 
        # and is reasonably long, use the Malayalam voice.
        if ml_chars > 0:
            lang = 'ml'

        # Text fed strictly into the TTS engine (invisible to the UI transcript)
        spoken_text = text.replace("-", " ") 
        if lang == 'ml':
            # Premium/Natural phonetic tuning for brand names and common items in Malayalam
            replacements = {
                "CartTalk": " കാർട്ട് ടോക്ക് ",
                "Cart": " കാർട്ട് ",
                "Welcome back to CartTalk": " കാർട്ട് ടോക്കിലേക്ക് വീണ്ടും സ്വാഗതം ",
                "Welcome to CartTalk": " കാർട്ട് ടോക്കിലേക്ക് സ്വാഗതം ",
                "Chicken": " ചിക്കൻ ",
                "Turmeric": " മഞ്ഞൾ ",
                "Chili": " ചില്ലി ",
                "Powder": " പൗഡർ ",
                "Coriander": " മല്ലി ",
                "Masala": " മസാല ",
                "Milma": " മിൽമ ",
                "milma": " മിൽമ ",
                "Nandhini": " നന്ദിനി ",
                "nandhini": " നന്ദിനി ",
                "Maggi": " മാഗി ",
                "maggi": " മാഗി ",
                "Yippee": " യിപ്പി ",
                "yippee": " യിപ്പി ",
                "Noodles": " നൂഡിൽസ് ",
                "noodles": " നൂഡിൽസ് ",
                "Atta": " ആട്ട ",
                "atta": " ആട്ട ",
                "Oats": " ഓട്സ് ",
                "oats": " ഓട്സ് ",
                "Basmati": " ബസ്മതി ",
                "basmati": " ബസ്മതി ",
                "Matta": " മട്ട ",
                "matta": " മട്ട ",
                "Apple": " ആപ്പിൾ ",
                "apple": " ആപ്പിൾ ",
                "Banana": " ബനാന ",
                "banana": " ബനാന ",
                "Orange": " ഓറഞ്ച് ",
                "orange": " ഓറഞ്ച് ",
                "Mango": " മാംഗോ ",
                "mango": " മാംഗോ ",
                "Grapes": " ഗ്രേപ്സ് ",
                "grapes": " ഗ്രേപ്സ് ",
                "Beef": " ബീഫ് ",
                "beef": " ബീഫ് "
            }
            for eng, mal in replacements.items():
                spoken_text = spoken_text.replace(eng, mal)

        print(f"Generating TTS in lang: {lang}")

        audio_bytes = None

        if USE_EDGE_TTS:
            try:
                voice = 'ml-IN-SobhanaNeural' if lang == 'ml' else 'en-US-AriaNeural'
                communicate = edge_tts.Communicate(spoken_text, voice, rate="+0%")
                fp = BytesIO()
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        fp.write(chunk["data"])
                fp.seek(0)
                audio_bytes = fp.read()
                if len(audio_bytes) > 0:
                    print(f"Edge-TTS audio: {len(audio_bytes)} bytes")
                else:
                    raise Exception("Edge-TTS returned empty audio")
            except Exception as e:
                print(f"Edge-TTS failed: {e}, falling back to gTTS")
                audio_bytes = None

        if audio_bytes is None:
            tts = gTTS(text=spoken_text, lang=lang)
            fp = BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            audio_bytes = fp.read()
            print(f"gTTS audio: {len(audio_bytes)} bytes")

        return audio_bytes

    @staticmethod
    async def stream_tts(text):
        """Zero-latency TTS streaming generator. Yields byte chunks."""
        import re
        
        lang = 'en'
        ml_chars = sum(1 for c in text if '\u0D00' <= c <= '\u0D7F')
        if ml_chars > 0:
            lang = 'ml'

        spoken_text = text.replace("-", " ") 
        if lang == 'ml':
            replacements = {
                "CartTalk": " കാർട്ട് ടോക്ക് ",
                "Cart": " കാർട്ട് ",
                "Welcome back to CartTalk": " കാർട്ട് ടോക്കിലേക്ക് വീണ്ടും സ്വാഗതം ",
                "Welcome to CartTalk": " കാർട്ട് ടോക്കിലേക്ക് സ്വാഗതം ",
                "Chicken": " ചിക്കൻ ",
                "Turmeric": " മഞ്ഞൾ ",
                "Chili": " ചില്ലി ",
                "Powder": " പൗഡർ ",
                "Coriander": " മല്ലി ",
                "Masala": " മസാല ",
                "Milma": " മിൽമ ",
                "milma": " മിൽമ ",
                "Nandhini": " നന്ദിനി ",
                "nandhini": " നന്ദിനി ",
                "Maggi": " മാഗി ",
                "maggi": " മാഗി ",
                "Yippee": " യിപ്പി ",
                "yippee": " യിപ്പി ",
                "Noodles": " നൂഡിൽസ് ",
                "noodles": " നൂഡിൽസ് ",
                "Atta": " ആട്ട ",
                "atta": " ആട്ട ",
                "Oats": " ഓട്സ് ",
                "oats": " ഓട്സ് ",
                "Basmati": " ബസ്മതി ",
                "basmati": " ബസ്മതി ",
                "Matta": " മട്ട ",
                "matta": " മട്ട ",
                "Apple": " ആപ്പിൾ ",
                "apple": " ആപ്പിൾ ",
                "Banana": " ബനാന ",
                "banana": " ബനാന ",
                "Orange": " ഓറഞ്ച് ",
                "orange": " ഓറഞ്ച് ",
                "Mango": " മാംഗോ ",
                "mango": " മാംഗോ ",
                "Grapes": " ഗ്രേപ്സ് ",
                "grapes": " ഗ്രേപ്സ് ",
                "Beef": " ബീഫ് ",
                "beef": " ബീഫ് "
            }
            for eng, mal in replacements.items():
                spoken_text = spoken_text.replace(eng, mal)

        print(f"Streaming TTS in lang: {lang}")

        if USE_EDGE_TTS:
            try:
                voice = 'ml-IN-SobhanaNeural' if lang == 'ml' else 'en-US-AriaNeural'
                communicate = edge_tts.Communicate(spoken_text, voice, rate="+10%")
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        yield chunk["data"]
                return
            except Exception as e:
                print(f"Edge-TTS stream failed: {e}, falling back to gTTS")
                # Fallback to standard blocking execution if edge-tts stream fails

        # Fallback (non-streaming but works)
        tts = gTTS(text=spoken_text, lang=lang)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        yield fp.read()

class InventoryService:
    def __init__(self):
        # We re-fetch products to ensure freshness or cache it
        pass
    
    def get_context(self):
        """Return inventory context for Gemini"""
        products = get_products()
        
        # Group by Category for better AI context
        grouped = {}
        for p in products:
            cat = p.get('category', 'General')
            if cat not in grouped: grouped[cat] = []
            
            # Safety Stock Logic
            buffer_val = p.get('safety_stock', 5)
            safe_stock = max(0, p['stock'] - buffer_val)
            
            grouped[cat].append({
                'id': p['id'],
                'name': f"{p['name_en']}/{p['name_ml']}",
                'price': p['price'],
                'stock': safe_stock
            })
            
        context_lines = []
        for cat, items in grouped.items():
            context_lines.append(f"{cat}:")
            for i in items:
                s = f"({i['stock']})" if i['stock'] > 0 else "(OOS)"
                context_lines.append(f"#{i['id']} {i['name']} ₹{i['price']} {s}")
            
        return "\n".join(context_lines)
    
    def list_all(self):
        return get_products()

class OrderService:
    def create_order(self, data):
        """Save order to database"""
        return create_order(data)
    
    def get_all(self):
        """Get all orders"""
        return get_orders()

def get_admin_analytics():
    """
    Service to fetch key analytics metrics for the Admin Dashboard
    Queries the SQLite db directly.
    """
    import sqlite3
    from datetime import date, timedelta
    from db import DB_FILE
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''
        SELECT COUNT(id), SUM(total)
        FROM orders
    ''')
    orders_today, revenue_today = c.fetchone()
    
    c.execute('''
        SELECT 
            COUNT(id) as total_products,
            SUM(CASE WHEN stock < 5 THEN 1 ELSE 0 END) as low_stock_products
        FROM products
    ''')
    total_products, low_stock_products = c.fetchone()
    
    c.execute('''
        SELECT p.name_en, SUM(oi.quantity) as total_qty
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        GROUP BY p.id
        ORDER BY total_qty DESC
        LIMIT 1
    ''')
    most_sold_row = c.fetchone()
    most_sold_product = most_sold_row[0] if most_sold_row else "N/A"
    
    orders_last_7_days = []
    c.execute('''
        SELECT date(created_at) as order_date, COUNT(id) as order_count
        FROM orders
        GROUP BY date(created_at)
        ORDER BY date(created_at) DESC
        LIMIT 7
    ''')
    db_counts_list = c.fetchall()
    db_counts_list.reverse() # Make chronological
    
    for row in db_counts_list:
        orders_last_7_days.append({
            "date": row[0],
            "orders": row[1]
        })
        
    if not orders_last_7_days:
        orders_last_7_days = [{"date": date.today().strftime('%Y-%m-%d'), "orders": 0}]
        
    conn.close()
    
    return {
        "orders_today": orders_today or 0,
        "revenue_today": revenue_today or 0,
        "total_products": total_products or 0,
        "low_stock_products": low_stock_products or 0,
        "most_sold_product": most_sold_product,
        "orders_last_7_days": orders_last_7_days
    }


def get_recent_orders(limit=10):
    import sqlite3
    from db import DB_FILE
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        SELECT id, customer_name, total, status, created_at
        FROM orders
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))
    
    orders = []
    columns = [desc[0] for desc in c.description]
    for row in c.fetchall():
        order_dict = dict(zip(columns, row))
        
        # Get items for this order
        c.execute('''
            SELECT p.name_en, oi.quantity
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        ''', (order_dict['id'],))
        
        items = [f"{item[0]} (x{item[1]})" for item in c.fetchall()]
        
        orders.append({
            "order_id": order_dict['id'],
            "customer_name": order_dict['customer_name'] or "Unknown",
            "items": ", ".join(items) if items else "No items",
            "total_amount": order_dict['total'],
            "status": order_dict['status'],
            "created_at": order_dict['created_at'][:16] # Truncate seconds out
        })
        
    conn.close()
    return orders

def get_low_stock_products():
    import sqlite3
    from db import DB_FILE
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Using safety_stock from earlier schema if available, else comparing against 5
    c.execute('''
        SELECT id, name_en, stock, safety_stock
        FROM products
        WHERE stock < COALESCE(safety_stock, 5)
        ORDER BY stock ASC
    ''')
    
    results = [{"product_id": row[0], "product_name": row[1], "stock": row[2], "safety_stock": row[3] or 5} for row in c.fetchall()]
    conn.close()
    return results

def get_top_products(limit=5):
    import sqlite3
    from db import DB_FILE
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        SELECT p.name_en, SUM(oi.quantity) as total_orders
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        GROUP BY p.id
        ORDER BY total_orders DESC
        LIMIT ?
    ''', (limit,))
    
    results = [{"product_name": row[0], "total_orders": row[1]} for row in c.fetchall()]
    conn.close()
    return results

def log_voice_interaction(voice_input, ai_interpretation, action_performed):
    import sqlite3
    from db import DB_FILE
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO voice_logs (voice_input, ai_interpretation, action_performed)
            VALUES (?, ?, ?)
        ''', (voice_input, ai_interpretation, action_performed))
        conn.commit()
    except sqlite3.OperationalError:
        pass # Table might not exist if init_db wasn't run recently
    conn.close()

def get_voice_logs(limit=20):
    import sqlite3
    from db import DB_FILE
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute('''
            SELECT id, voice_input, ai_interpretation, action_performed, timestamp
            FROM voice_logs
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        columns = [desc[0] for desc in c.description]
        results = [dict(zip(columns, row)) for row in c.fetchall()]
    except sqlite3.OperationalError:
        results = [] # In case table doesn't exist
    conn.close()
    return results
