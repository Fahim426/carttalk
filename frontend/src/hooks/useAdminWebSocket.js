import { useEffect } from 'react';

// Shared WebSocket instance to prevent making multiple connections per component
let ws = null;
const listeners = new Set();

export function initAdminWebSocket() {
    if (ws) return;
    ws = new WebSocket('ws://localhost:8000/api/admin/ws');

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            listeners.forEach(callback => callback(data));
        } catch (e) {
            console.error("WS Message Error:", e);
        }
    };

    ws.onclose = () => {
        console.log("Admin WS Closed - Reconnecting...");
        ws = null;
        setTimeout(initAdminWebSocket, 3000);
    };
}

export function useAdminWebSocket(callback) {
    useEffect(() => {
        initAdminWebSocket();
        listeners.add(callback);
        return () => {
            listeners.delete(callback);
        };
    }, [callback]);
}
