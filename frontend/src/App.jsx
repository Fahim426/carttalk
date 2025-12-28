import React, { useState } from 'react';
import CallInterface from './CallInterface';
import './App.css';

function App() {
    const [isCallActive, setIsCallActive] = useState(false);
    const [callId, setCallId] = useState(null);

    const startCall = async () => {
        const res = await fetch('/api/call/start', { method: 'POST' });
        const data = await res.json();
        setCallId(data.call_id);
        setIsCallActive(true);
    };

    return (
        <div className="app">
            <header>
                <h1>🛒 CartTalk - Voice Grocery Assistant</h1>
            </header>

            {!isCallActive ? (
                <div className="welcome">
                    <p>Welcome to CartTalk! Start a call to order groceries.</p>
                    <button onClick={startCall}>Start Call</button>
                </div>
            ) : (
                <CallInterface callId={callId} onEndCall={() => setIsCallActive(false)} />
            )}
        </div>
    );
}

export default App;
