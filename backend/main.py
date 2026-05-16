"""
main.py
FastAPI entry point for CartTalk.
Provides REST APIs for frontend interaction (inventory, auth, orders)
and a WebSocket endpoint for real-time AI voice streaming.
"""
import shutil
import json
import uuid
import os
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from services import (
    GeminiService, InventoryService, OrderService, get_admin_analytics,
    get_recent_orders, get_low_stock_products, get_top_products, get_voice_logs,
    log_voice_interaction
)
from db import (
    init_db, get_products, get_user, get_cart, update_user,
    get_orders_by_user, update_order_status, add_product,
    update_product, delete_product, delete_order, save_cart
)
from ws_manager import admin_ws_manager

# Load environment variables
load_dotenv()

app = FastAPI(
    title="CartTalk API",
    description="AI-powered voice grocery assistant backend",
    version="1.0.0"
)

# Mount Static Files (Images)
os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize
init_db()
inventory = InventoryService()
gemini = GeminiService()
orders = OrderService()

# Store active calls -> user mapping
call_sessions = {}

# ─── Health Check ────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "service": "CartTalk API", "version": "1.0.0"}

# ─── Authentication ──────────────────────────────────────────

@app.post("/api/auth/login")
async def customer_login(data: dict):
    """Simple Phone Login — auto-creates user if not exists"""
    phone = data.get('phone')
    if not phone:
        return {"error": "Phone required"}
    
    user = update_user(phone) 
    cart = get_cart(phone)
    return {"user": user, "cart": cart}

# ─── Voice Call ──────────────────────────────────────────────

@app.post("/api/call/start")
async def start_call(data: dict = None):
    """Start new customer call session"""
    call_id = str(uuid.uuid4())
    
    user_id = data.get('user_id') if data else None
    if user_id:
        call_sessions[call_id] = user_id
        
    return {"call_id": call_id, "status": "ready"}

@app.websocket("/api/call/{call_id}/stream")
async def websocket_endpoint(websocket: WebSocket, call_id: str):
    """Real-time audio streaming via WebSocket"""
    await websocket.accept()
    try:
        while True:
            try:
                data = await websocket.receive()
            except WebSocketDisconnect:
                print(f"Client disconnected: {call_id}")
                break
            except Exception as e:
                print(f"WebSocket Receive Error: {e}")
                break  # break, not continue — socket is broken

            text_input = ""
            audio_data = None

            # Check for ASGI-level disconnect frame
            if data.get("type") == "websocket.disconnect":
                print(f"Client disconnected (frame): {call_id}")
                break

            # Route: binary audio OR text JSON
            if 'bytes' in data and data['bytes']:
                audio_data = data['bytes']
            elif 'text' in data and data['text']:
                try:
                    json_data = json.loads(data['text'])
                    if json_data.get('type') == 'text':
                        text_input = json_data.get('text', '')
                except Exception as je:
                    print(f"JSON parse error: {je}")

            if not text_input and not audio_data:
                continue

            # Context Preparation
            base_context = inventory.get_context()

            # Personalization — always provide Guest defaults so AI knows what's missing
            user_context = "User Name: Guest\nUser Address: Unknown\n"
            user_phone = call_sessions.get(call_id)
            if user_phone:
                u = get_user(user_phone)
                c = get_cart(user_phone)
                if u:
                    user_context = f"User Name: {u['name'] or 'Guest'}\nUser Address: {u['address'] or 'Unknown'}\n"
                if c:
                    cart_summary = ", ".join([f"{item['qty']}x {item['name']}" for item in c])
                    user_context += f"Previous Cart: {cart_summary}\n"

            final_context = user_context + "\n" + base_context

            if audio_data:
                result = await gemini.process_audio(call_id, audio_data, final_context, user_id=user_phone)
            else:
                result = await gemini.process_text(call_id, text_input, final_context, user_id=user_phone)
            
            if result:
                # ── PHASE 1: Send text instantly (sub-second) ──
                if result.get("user_transcript"):
                    await websocket.send_json({"type": "transcript", "role": "user", "text": result["user_transcript"]})
                
                if result.get("ai_text"):
                    await websocket.send_json({"type": "transcript", "role": "ai", "text": result["ai_text"]})
                
                if result.get("cart") is not None:
                    await websocket.send_json({"type": "cart", "cart": result["cart"]})

                # ── STOCK GUARD: Notify frontend if quantities were clamped ──
                violations = result.get("stock_violations", [])
                if violations:
                    warn_parts = []
                    for v in violations:
                        if v['available'] == 0:
                            warn_parts.append(f"{v['name']} is out of stock and was removed from your cart.")
                        else:
                            warn_parts.append(
                                f"Only {v['available']} unit(s) of {v['name']} available. "
                                f"Your cart has been updated to {v['available']}."
                            )
                    warning_text = " ".join(warn_parts)
                    await websocket.send_json({
                        "type": "stock_warning",
                        "text": warning_text,
                        "violations": violations
                    })

                # ── PHASE 2: Generate FULL TTS audio (Ensures clarity & natural flow) ──
                from services import GeminiService
                ai_audio = result.get("ai_audio", "") or result.get("ai_text", "")
                if ai_audio:
                    audio_bytes = await GeminiService.generate_tts(ai_audio)
                    if audio_bytes:
                        await websocket.send_bytes(audio_bytes)
                
                # Check for termination signal
                if result.get("terminate"):
                    await websocket.send_text(json.dumps({"type": "control", "action": "terminate"}))
                    action_perf = "Confirmed Order & Terminated"
                else:
                    action_perf = f"Updated Cart" if result.get("cart") is not None else "Responded"
                    
                # Log voice interaction
                if result.get("user_transcript"):
                    log_voice_interaction(
                        voice_input=result["user_transcript"],
                        ai_interpretation=result.get("ai_text", ""),
                        action_performed=action_perf
                    )
                    await admin_ws_manager.broadcast({"type": "VOICE_LOG_UPDATED"})
            else:
                # Error Case: Unblock Frontend
                await websocket.send_json({"type": "error", "text": "Sorry, I encountered an error. Please try again."})
    except Exception as e:
        print(f"WebSocket Error: {e}")

# ─── Products ────────────────────────────────────────────────

@app.get("/api/products")
async def get_all_products():
    """Get all products"""
    return inventory.list_all()

@app.post("/api/products")
async def create_product(product: dict):
    """Add new product"""
    res = add_product(product)
    await admin_ws_manager.broadcast({"type": "INVENTORY_UPDATED"})
    return res

@app.put("/api/products/{product_id}")
async def update_product_endpoint(product_id: int, data: dict):
    """Update product (stock, price, image)"""
    res = update_product(product_id, data)
    await admin_ws_manager.broadcast({"type": "INVENTORY_UPDATED"})
    return res

@app.delete("/api/products/{product_id}")
async def delete_product_endpoint(product_id: int):
    """Delete a product"""
    res = delete_product(product_id)
    await admin_ws_manager.broadcast({"type": "INVENTORY_UPDATED"})
    return res

# ─── Orders ──────────────────────────────────────────────────

@app.post("/api/order/confirm")
async def confirm_order(order_data: dict):
    """Confirm and save order"""
    res = orders.create_order(order_data) # wait, the file doesn't have orders globally, it imports get_recent_orders etc. Wait, look at line 183 "orders.create_order(order_data)"
    await admin_ws_manager.broadcast({"type": "NEW_ORDER"})
    return res

@app.get("/api/orders")
async def get_orders_handler():
    """Get all orders (merchant dashboard)"""
    return orders.get_all()

@app.get("/api/orders/user")
async def get_user_orders(phone: str):
    """Get orders for a specific customer"""
    return get_orders_by_user(phone)

@app.put("/api/orders/{order_id}/status")
async def update_status(order_id: int, status_data: dict):
    """Update order status (e.g. delivered)"""
    new_status = status_data.get('status')
    res = update_order_status(order_id, new_status)
    await admin_ws_manager.broadcast({"type": "ORDER_UPDATED"})
    return res

@app.delete("/api/orders/{order_id}")
async def delete_order_endpoint(order_id: int):
    """Delete order"""
    res = delete_order(order_id)
    await admin_ws_manager.broadcast({"type": "ORDER_UPDATED"})
    return res

# ─── Cart ────────────────────────────────────────────────────

@app.post("/api/cart/add")
async def add_to_cart(data: dict):
    """Add item to user's persistent cart"""
    phone = data.get('phone')
    items = data.get('items', [])
    if not phone:
        return {"error": "Phone required"}
    save_cart(phone, items)
    return {"status": "updated", "items_count": len(items)}

# ─── Admin ───────────────────────────────────────────────────

@app.get("/api/admin/analytics")
async def get_analytics():
    """Get merchant dashboard analytics"""
    try:
        return get_admin_analytics()
    except Exception as e:
        print(f"Error fetching analytics: {e}")
        return {"error": "Failed to fetch analytics"}

@app.get("/api/admin/recent-orders")
async def fetch_recent_orders():
    return get_recent_orders(limit=10)

@app.get("/api/admin/low-stock")
async def fetch_low_stock():
    return get_low_stock_products()

@app.get("/api/admin/top-products")
async def fetch_top_products():
    return get_top_products(limit=5)

@app.get("/api/admin/voice-logs")
async def fetch_voice_logs():
    return get_voice_logs(limit=20)

@app.websocket("/api/admin/ws")
async def admin_websocket(websocket: WebSocket):
    await admin_ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except Exception as e:
        pass
    finally:
        admin_ws_manager.disconnect(websocket)

# ─── Uploads ─────────────────────────────────────────────────

@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    """Upload product image with unique filename to prevent overwrites"""
    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4()}{ext}"
    file_location = f"static/images/{unique_name}"
    
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"url": f"http://localhost:8000/{file_location}"}

# ─── Entry Point ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
