"""
services.py
Core AI integration module for CartTalk.
Handles the interaction with Google Gemini 2.5 Flash, including
parsing user intent, maintaining sliding window context,
managing shopping cart state, and generating Neural TTS audio.
"""
import os
from datetime import datetime
from google import genai
from db import get_products, create_order, get_orders
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
        # We assume GEMINI_API_KEY is set in environment
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
             print("Warning: GEMINI_API_KEY not found in environment variables.")
        self.client = genai.Client(api_key=api_key)
        self.histories = {} # To store conversation history for each call_id
        self.summaries = {} # Store summarized older context per call_id
    
    async def process_audio(self, call_id, audio_data, inventory_context, user_id=None):
        """Send audio to Gemini Live API, get response and convert to audio"""
        try:
            # Initialize history for this call if not exists
            if call_id not in self.histories:
                self.histories[call_id] = []
            
            # System Instruction (always first)
            now = datetime.now()
            time_context = now.strftime("%I:%M %p")

            system_instruction = f"""
You are CartTalk, a strict bilingual grocery assistant (English and Malayalam). 
Current Store Time: {time_context}
Your Goal: Act like a helpful but CONCISE Shopkeeper ("Kada Chettan").

CRITICAL INSTRUCTIONS:
1. LANGUAGE DETECTION:
   - If User speaks MALAYALAM -> PROCEED IN MALAYALAM ONLY. DO NOT output ANY English in the RESPONSE section.
   - If User speaks ENGLISH -> Proceed in English.
   - Exception: Your very first greeting must use "Welcome to CartTalk!".

2. MALAYALAM PERSONA (If User speaks Malayalam):
   - Greeting: ONLY say "നമസ്കാരം" (Namaskaram) or "ഹലോ" (Hello) in the VERY FIRST interaction. Do NOT repeat greetings throughout the rest of the conversation. NOT "Vanakkam".
   - Vocabulary: Use simple, everyday Malayalam words for common items (e.g., "Thakkali", "Ari", "Parippu"). DO NOT use overly formal words like "പലവ്യഞ്ജനങ്ങൾ".
   - Structure: Be extremely brief. Do not list categories. Just ask what they need.
   - Confirmation: "ഇതു എടുക്കട്ടെ?"
   - Price: "ഒരു കിലോയ്ക്ക് 35 രൂപയാണ്"
   - Example: 
     - User: "Oru kilo thakkali"
     - Bot (RESPONSE): "തക്കാളി ഉണ്ട്. കിലോയ്ക്ക് 35 രൂപയാണ്. ഒരു കിലോ എടുക്കട്ടെ?"

3. REQUIRED OUTPUT STRUCTURE (You MUST output EXACTLY these 4 sections in this EXACT order. Do NOT mix or merge them):
TRANSCRIPT: [Exact letters spoken by User in the original language. NO TRANSLATIONS].
DATA: ```json
{{"cart": [...]}}
``` or just ```json
{{}}
``` if no changes.
COMMAND: UPDATE_CART or CONFIRM_ORDER or NONE
RESPONSE: [Your actual spoken reply to the user. MUST be Malayalam ONLY if they spoke Malayalam. This section MUST NOT contain any JSON, code, or technical data. Only natural conversational text.]

5. ADVANCED INTELLIGENCE:
   - SLOT FILLING: If they ask a category (e.g., "Ari"), ask which type: "ഏത് അരിയാണ് വേണ്ടത്? മട്ടയും ബസ്മതിയും ഉണ്ട്."
   - DO NOT LIST INVENTORY: If they ask "What do you have?", say "അരി, പച്ചക്കറികൾ ഒക്കെ ഉണ്ട്. എന്താണ് വേണ്ടത്?" (Rice, vegetables, etc. What do you need?) Be short. Do NOT use the word പലവ്യഞ്ജനങ്ങൾ.
   - RECIPE CHEF MODE: If the User asks how to make a dish (e.g., "How to make Chicken Curry?", "Chicken Biriyani Recipe"), briefly explain the recipe, list the ingredients needed, and proactively ask if they want you to add those specific ingredients to their cart from the store inventory.
   - MONTHLY REMINDER: Before confirming the order, check USER ESSENTIALS and FORGOTTEN ITEMS lists. If any essential item is NOT in the current cart, you MUST proactively and naturally say something like: "I noticed you usually buy [item]. Would you like to add that too?" or "Last time you ordered [item] — should I add it?". Do this conversationally, not as a list dump.
   - LOW STOCK WARNING: If any LOW STOCK ALERT items are listed, mention it early: "Just a heads up, [item] is running low in stock. Want to grab some before it's out?"
   - IDENTITY CHECK: If the User Name is "Guest" or User Address is "Unknown", YOU MUST ASK for their Name and Address before finishing the order. When asking for the address, explicitly ask for their Street Name and Pincode (e.g., "പിൻകോഡും സ്ഥലവും കൂടി പറയാമോ?").
   - FINALIZING: ONLY output COMMAND: CONFIRM_ORDER when the user explicitly agrees to finalize the purchase AND you have their Name and Address.

5. JSON DATA PAYLOAD `DATA:`
   - Track items in `cart` list.
   - If User provides their Name or Address, update `name` and `address` fields in the JSON. YOU MUST ALWAYS TRANSLATE BOTH NAME AND ADDRESS TO ENGLISH IN THE JSON, regardless of the spoken language.

Inventory:
""" + inventory_context
            
            # Fetch User History for personalization
            if user_id:
                from db import get_user_frequent_items, get_user_monthly_essentials, get_forgotten_items
                
                # Frequent Items
                freq_items = get_user_frequent_items(user_id)
                if freq_items:
                    items_str = ", ".join([f"{i['name']} (Qty: {i['qty']})" for i in freq_items])
                    system_instruction += f"\n\nUSER HISTORY (Frequent Items): [{items_str}]"            

                # Monthly Essentials
                monthly_essentials = get_user_monthly_essentials(user_id)
                if monthly_essentials:
                     essentials_str = ", ".join([i['name'] for i in monthly_essentials])
                     system_instruction += f"\n\nUSER ESSENTIALS (Monthly Habits): [{essentials_str}]"
                
                # Forgotten Items (ordered ≥3 times but not in last 30 days)
                forgotten = get_forgotten_items(user_id)
                if forgotten:
                    forgot_str = ", ".join([f"{i['name']} (ordered {i['times_ordered']}x before)" for i in forgotten])
                    system_instruction += f"\n\nFORGOTTEN ITEMS (User hasn't ordered these recently): [{forgot_str}]"
                
                # Low Stock Alerts for user's frequent items
                if freq_items:
                    all_products = get_products()
                    low_stock_alerts = []
                    for fi in freq_items:
                        for p in all_products:
                            if p['id'] == fi['id'] and p['stock'] <= p.get('safety_stock', 5) and p['stock'] > 0:
                                low_stock_alerts.append(f"{p['name_en']} (only {p['stock']} left)")
                    if low_stock_alerts:
                        system_instruction += f"\n\nLOW STOCK ALERT (User's favorites running low): [{', '.join(low_stock_alerts)}]"
                     
            # specific instruction for the first turn
            if not self.histories[call_id]:
                if user_id:
                     system_instruction += f"\n\nSPECIAL INSTRUCTION: This is the FIRST interaction. You MUST start your response exactly with 'Welcome back to CartTalk!'. After this greeting, continue in the user's detected language."
                else:
                     system_instruction += "\n\nSPECIAL INSTRUCTION: This is the FIRST interaction. You MUST start your response exactly with 'Welcome to CartTalk!'. After this exact greeting, ask how you can help based on the user's detected language (English or Malayalam)."

            # Build history with summarization for long conversations
            summary_prefix = ""
            if call_id in self.summaries and self.summaries[call_id]:
                summary_prefix = f"CONVERSATION SUMMARY (older turns):\n{self.summaries[call_id]}\n\n"
            
            history_text = summary_prefix + "RECENT CONVERSATION:\n" + "\n".join(self.histories[call_id])
            
            final_prompt = system_instruction + "\n\nCONVERSATION HISTORY:\n" + history_text + "\n\nCURRENT AUDIO INPUT:"
            
            # Request
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
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
            
            # Robust Extraction of AI Response (Removing all backend tags)
            ai_response = raw_text
            ai_response = re.sub(r'TRANSCRIPT:\s*(.*?)(?=\s*DATA:|\s*COMMAND:|\s*RESPONSE:|\Z)', '', ai_response, flags=re.DOTALL | re.IGNORECASE)
            ai_response = re.sub(r'DATA:\s*(.*?)(?=\s*COMMAND:|\s*RESPONSE:|\Z)', '', ai_response, flags=re.DOTALL | re.IGNORECASE)
            ai_response = re.sub(r'COMMAND:\s*(.*?)(?=\s*RESPONSE:|\Z)', '', ai_response, flags=re.IGNORECASE)
            ai_response = re.sub(r'RESPONSE:\s*', '', ai_response, flags=re.IGNORECASE).strip()
            
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
                
                if command == 'UPDATE_CART' and user_id:
                     from db import save_cart
                     print("Saving Persistent Cart...")
                     session = getattr(self, 'session_data', {}).get(call_id, {})
                     cart_items = session.get('cart', [])
                     if cart_items:
                         valid_pids = {p['id'] for p in get_products()}
                         valid_cart = [item for item in cart_items if item.get('id') in valid_pids]
                         if len(valid_cart) < len(cart_items):
                             print("Warning: AI hallucinated product IDs removed")
                         print(f"Update DB Cart: {len(valid_cart)} items for {user_id}")
                         save_cart(user_id, valid_cart)

                if command == 'CONFIRM_ORDER':
                    # Save to DB
                    print("Executing Order Confirmation...")
                    session = getattr(self, 'session_data', {}).get(call_id, {})
                    
                    found_name = session.get('name', 'Unknown')
                    found_address = session.get('address', 'Unknown')
                    
                    if user_id:
                        from db import update_user, get_user
                        # Only overwrite if they actually gave a new one, else keep DB
                        db_user = get_user(user_id)
                        final_name = found_name if found_name != 'Unknown' else (db_user['name'] if db_user else 'Unknown')
                        final_address = found_address if found_address != 'Unknown' else (db_user['address'] if db_user else 'Unknown')
                        update_user(user_id, final_name, final_address)
                    else:
                        final_name = found_name
                        final_address = found_address
                        
                    # Filter invalid IDs out and calculate actual total
                    cart_items = session.get('cart', [])
                    db_products = {p['id']: p['price'] for p in get_products()}
                    valid_cart = [item for item in cart_items if item.get('id') in db_products]
                    
                    order_total = 0.0
                    for item in valid_cart:
                        # Grab correct live price from DB
                        item_price = float(db_products.get(item.get('id'), 0))
                        item_qty = float(item.get('quantity', item.get('qty', 1)))
                        order_total += item_price * item_qty
                        item['price'] = item_price # Embed price into valid_cart so it goes to DB
                    
                    order_payload = {
                        'phone': user_id if user_id else 'VoiceUser',
                        'name': final_name,
                        'address': final_address,
                        'total': round(order_total, 2),
                        'language': 'en', 
                        'transcript': history_text,
                        'items': valid_cart
                    }
                    create_order(order_payload)
                    print(f"Order Saved to DB | Total: Rs.{order_total}")

            # Update History
            if transcript:
                self.histories[call_id].append(f"User: {transcript}")
            self.histories[call_id].append(f"Model: {ai_response}")
            
            # Keep history manageable with sliding window + summarization
            MAX_RECENT = 20  # Keep last 10 turns (20 entries) in full detail
            if len(self.histories[call_id]) > MAX_RECENT + 10:
                # Summarize the oldest entries before trimming
                old_entries = self.histories[call_id][:-MAX_RECENT]
                old_text = "\n".join(old_entries)
                
                try:
                    summary_resp = self.client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[{"role": "user", "parts": [{"text": f"Summarize this conversation in 2-3 sentences, focusing on: items discussed, items added to cart, customer preferences, name/address if mentioned. Be concise:\n\n{old_text}"}]}]
                    )
                    new_summary = summary_resp.text.strip()
                    # Append to existing summary
                    existing = self.summaries.get(call_id, '')
                    self.summaries[call_id] = (existing + "\n" + new_summary).strip()
                    print(f"Context summarized: {new_summary[:80]}...")
                except Exception as e:
                    print(f"Summarization failed: {e}")
                
                # Keep only recent entries
                self.histories[call_id] = self.histories[call_id][-MAX_RECENT:]

            # Clean text for TTS
            clean_text = ai_response
            
            # Ultra-Aggressive sweeping to ensure NO JSON or tags leak to users
            clean_text = re.sub(r'DATA:\s*\{.*?\}\s*', '', clean_text, flags=re.DOTALL | re.IGNORECASE)
            clean_text = re.sub(r'DATA:.*?$', '', clean_text, flags=re.DOTALL | re.IGNORECASE)
            clean_text = re.sub(r'COMMAND:\s*[A-Z_]+', '', clean_text, flags=re.IGNORECASE)
            clean_text = re.sub(r'\{"cart":.*?\}', '', clean_text, flags=re.DOTALL | re.IGNORECASE)

            # Standard cleanup
            clean_text = re.sub(r'\*+', '', clean_text)
            clean_text = re.sub(r'[#`]', '', clean_text)
            clean_text = clean_text.replace('RESPONSE:', '').strip()
            
            # Clean parenthetical translations e.g., (Hello)
            clean_text = re.sub(r'\(.*?\)', '', clean_text)
            
            # NEW: Remove ID references like (ID: 12) or [ID: 12] spoken by mistake
            clean_text = re.sub(r'[\[\(]ID:?\s*\d+[\]\)]', '', clean_text, flags=re.IGNORECASE)
            clean_text = re.sub(r'ID\s*\d+', '', clean_text, flags=re.IGNORECASE)

            # Final safety cleanup for leaking JSON brackets
            # Remove trailing "]}" or "}" or "]" if they are at the end of the line
            clean_text = re.sub(r'[\]\}]+\s*$', '', clean_text).strip()
            
            clean_text = clean_text.strip()
            
            # Fallback if no text to speak (e.g. only Command was output)
            if not clean_text:
                if command == 'CONFIRM_ORDER':
                    clean_text = "Order confirmed! Thank you."
                else:
                    clean_text = "Okay."

            # Detect language (ratio-based: use Malayalam voice only if majority is Malayalam)
            lang = 'en'
            ml_chars = sum(1 for c in clean_text if '\u0D00' <= c <= '\u0D7F')
            latin_chars = sum(1 for c in clean_text if c.isalpha() and ord(c) < 128)
            total_alpha = ml_chars + latin_chars
            if total_alpha > 0 and (ml_chars / total_alpha) > 0.4:
                lang = 'ml'
            
            # Generate TTS Audio
            print(f"Generating audio for: '{clean_text[:50]}...' in lang: {lang}")
            
            audio_bytes = None
            
            # Try edge-tts first (faster, better quality neural voices)
            if USE_EDGE_TTS:
                try:
                    voice = 'ml-IN-SobhanaNeural' if lang == 'ml' else 'en-US-AriaNeural'
                    communicate = edge_tts.Communicate(clean_text, voice)
                    fp = BytesIO()
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            fp.write(chunk["data"])
                    fp.seek(0)
                    audio_bytes = fp.read()
                    if len(audio_bytes) > 0:
                        print(f"Edge-TTS audio generated, size: {len(audio_bytes)} bytes")
                    else:
                        raise Exception("Edge-TTS returned empty audio")
                except Exception as e:
                    print(f"Edge-TTS failed: {e}, falling back to gTTS")
                    audio_bytes = None
            
            # Fallback to gTTS
            if audio_bytes is None:
                tts = gTTS(text=clean_text, lang=lang)
                fp = BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0)
                audio_bytes = fp.read()
                print(f"gTTS audio generated, size: {len(audio_bytes)} bytes")
            
            return {
                "user_transcript": transcript,
                "ai_text": clean_text,
                "audio": audio_bytes,
                "terminate": (command == 'CONFIRM_ORDER'),
                "cart": getattr(self, 'session_data', {}).get(call_id, {}).get('cart', [])
            }

        except Exception as e:
            print(f"Gemini/Audio API Error: {e}")
            import traceback
            traceback.print_exc()
            with open("error_log.txt", "a") as f:
                f.write(f"Timestamp: {datetime.now()}\n")
                f.write(f"Error: {e}\n")
                traceback.print_exc(file=f)
                f.write("\n" + "-"*20 + "\n")

            # Handle Rate Limit gracefully 
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                error_text = "Sorry, I am currently receiving too many requests. Please try again in about a minute."
                try:
                    tts = gTTS(text=error_text, lang='en')
                    fp = BytesIO()
                    tts.write_to_fp(fp)
                    fp.seek(0)
                    audio_bytes = fp.read()
                    return {
                        "user_transcript": "[Quota Exceeded]",
                        "ai_text": error_text,
                        "audio": audio_bytes,
                        "terminate": False
                    }
                except Exception as tts_e:
                    print(f"TTS fallback failed: {tts_e}")

            return None

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
            context_lines.append(f"Category: {cat}")
            for item in items:
                status = f"Stock: {item['stock']}" if item['stock'] > 0 else "OUT OF STOCK"
                context_lines.append(f"  - [ID: {item['id']}] {item['name']} @ ₹{item['price']} ({status})")
            
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
    
    today_str = date.today().strftime('%Y-%m-%d')
    c.execute('''
        SELECT COUNT(id), SUM(total)
        FROM orders
        WHERE date(created_at) = ?
    ''', (today_str,))
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
        WHERE date(created_at) >= date('now', '-6 days')
        GROUP BY date(created_at)
        ORDER BY date(created_at) ASC
    ''')
    db_counts = dict(c.fetchall())
    
    for i in range(6, -1, -1):
        target_date = (date.today() - timedelta(days=i)).strftime('%Y-%m-%d')
        orders_last_7_days.append({
            "date": target_date,
            "orders": db_counts.get(target_date, 0)
        })
        
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
