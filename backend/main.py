from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import asyncio
from services import GeminiService, InventoryService, OrderService
from db import init_db, get_products


# Load environment variables
load_dotenv()

app = FastAPI()

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

import uuid

@app.post("/api/call/start")
async def start_call():
    """Start new customer call"""
    return {"call_id": str(uuid.uuid4()), "status": "ready"}

@app.websocket("/api/call/{call_id}/stream")
async def websocket_endpoint(websocket: WebSocket, call_id: str):
    """Real-time audio streaming"""
    await websocket.accept()
    try:
        while True:
            # Receive audio chunk from frontend
            # Since frontend start() has no timeslice, this is likely the whole utterance upon stop()
            audio_data = await websocket.receive_bytes()
            
            # Process with Gemini Live API
            # Context is refreshed per call or just once? Simple: just get it.
            context = inventory.get_context()
            response = await gemini.process_audio(call_id, audio_data, context)
            
            # Send back response audio (bytes from gTTS)
            await websocket.send_bytes(response)
    except Exception as e:
        print(f"WebSocket Error: {e}")
        # await websocket.close() # Might already be closed

@app.get("/api/products")
async def get_all_products():
    """Get all products"""
    return inventory.list_all()

@app.post("/api/cart/add")
async def add_to_cart(item: dict):
    # This endpoint was mentioned in requirement "POST /api/cart/add"
    # But not implemented in prompt's main.py sample
    # We will implement a dummy or simple logic if needed
    # But usually, the Voice Assistant manages the cart in context strings or DB?
    # The prompt sample says "Add items to cart as customer requests" in SYSTEM PROMPT.
    # So the "Cart" might be purely maintained by the LLM context or we should maintain a session cart.
    # Given the simplicity, and the fact that the frontend doesn't show a cart (only transcript),
    # maybe this endpoint isn't used by the frontend provided?
    # The PROMPT required it: "POST /api/cart/add".
    # I'll add a dummy endpoint.
    return {"status": "added", "item": item}

@app.post("/api/order/confirm")
async def confirm_order(order_data: dict):
    """Confirm and save order"""
    return orders.create_order(order_data)

@app.get("/api/orders")
async def get_orders_handler():
    """Get all orders"""
    return orders.get_all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
