import json
from typing import List
from fastapi import WebSocket

class AdminConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"Admin WS send failed, removing connection: {e}")
                dead_connections.append(connection)
        # BUG 5 FIX: Remove dead connections after iteration to avoid memory leak
        for dead in dead_connections:
            self.disconnect(dead)

admin_ws_manager = AdminConnectionManager()
