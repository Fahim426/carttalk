import React, { useState, useEffect, useRef } from 'react';
import './CallInterface.css';
import Logo from './components/Logo';

function CallInterface({ callId, onEndCall }) {
    const [status, setStatus] = useState('initializing'); // initializing, listening, speaking, processing, ai_speaking
    const statusRef = useRef('initializing'); 
    const setStatusWithRef = (newStatus) => {
        statusRef.current = newStatus;
        setStatus(newStatus);
    };
    const [messages, setMessages] = useState([]);
    const [cart, setCart] = useState([]);
    const [orderConfirmed, setOrderConfirmed] = useState(false);
    const [stockWarning, setStockWarning] = useState('');

    const wsRef = useRef(null);
    const audioContextRef = useRef(null);
    const mediaStreamRef = useRef(null);
    const analyserRef = useRef(null);
    const currentAudioRef = useRef(null);
    const endCallAfterAudioRef = useRef(false);

    const chatEndRef = useRef(null);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, status]);

    useEffect(() => {
        wsRef.current = new WebSocket(`ws://localhost:8000/api/call/${callId}/stream`);

        wsRef.current.onopen = () => {
            console.log("WebSocket connected");
            setStatusWithRef('listening');
            startListening();
        };

        wsRef.current.onmessage = async (event) => {
            if (typeof event.data === 'string') {
                try {
                    const msg = JSON.parse(event.data);
                    if (msg.type === 'transcript') setMessages(prev => [...prev, { role: msg.role, text: msg.text }]);
                    if (msg.type === 'cart') setCart(msg.cart || []);
                    if (msg.type === 'control' && msg.action === 'terminate') endCallAfterAudioRef.current = true;
                    if (msg.type === 'stock_warning') {
                        setStockWarning(msg.text);
                        // Auto-dismiss after 8 seconds
                        setTimeout(() => setStockWarning(''), 8000);
                    }
                    if (msg.type === 'error') {
                        setStatusWithRef('listening');
                        alert(msg.text);
                        startListening();
                    }
                } catch (e) { console.error(e); }
                return;
            }

            if (event.data.size > 0) {
                setStatusWithRef('ai_speaking');
                if (recognitionRef.current) {
                    try { recognitionRef.current.stop(); } catch(e) {}
                }

                const blob = new Blob([event.data], { type: 'audio/mp3' });
                const url = URL.createObjectURL(blob);
                const audio = new Audio(url);
                currentAudioRef.current = audio;

                audio.onended = () => {
                    URL.revokeObjectURL(url);
                    currentAudioRef.current = null;
                    if (endCallAfterAudioRef.current) {
                        setOrderConfirmed(true);
                    } else {
                        setStatusWithRef('listening');
                        startListening();
                    }
                };
                audio.play().catch(e => {
                    console.error("Audio play error", e);
                    if (endCallAfterAudioRef.current) setOrderConfirmed(true);
                    else startListening();
                });
            }
        };

        wsRef.current.onerror = (e) => console.error("WS Error", e);
        wsRef.current.onclose = () => {
            if (!endCallAfterAudioRef.current) {
                setStatusWithRef('disconnected');
            }
        };
        return () => { stopEverything(); };
    }, [callId]);

    const recognitionRef = useRef(null);
    const [interimTranscript, setInterimTranscript] = useState('');

    const startListening = async () => {
        try {
            if (!audioContextRef.current) {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaStreamRef.current = stream;
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                audioContextRef.current = audioContext;
                const source = audioContext.createMediaStreamSource(stream);
                const analyser = audioContext.createAnalyser();
                analyser.fftSize = 256;
                source.connect(analyser);
                analyserRef.current = analyser;
                detectVoiceActivity();
            } else if (audioContextRef.current.state === 'suspended') {
                await audioContextRef.current.resume();
            }

            if (!recognitionRef.current) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SpeechRecognition) {
                    alert("Your browser does not support Speech Recognition. Please use Chrome.");
                    return;
                }
                const recognition = new SpeechRecognition();
                recognition.continuous = true; 
                recognition.interimResults = true;
                recognition.lang = 'en-IN'; // en-IN handles both English and Malayalam phonetics correctly

                recognition.onstart = () => {
                    setStatusWithRef('listening');
                    setInterimTranscript('');
                };

                recognition.onresult = (event) => {
                    let finalTranscript = '';
                    let interim = '';
                    for (let i = event.resultIndex; i < event.results.length; ++i) {
                        if (event.results[i].isFinal) finalTranscript += event.results[i][0].transcript;
                        else interim += event.results[i][0].transcript;
                    }
                    if (interim) {
                        setInterimTranscript(interim);
                        if (statusRef.current !== 'speaking') setStatusWithRef('speaking');
                    }
                    if (finalTranscript) {
                        setInterimTranscript('');
                        sendTextAndProcess(finalTranscript);
                    }
                };

                recognition.onend = () => {
                    if (statusRef.current === 'listening' || statusRef.current === 'speaking' || statusRef.current === 'user_voice_detected') {
                        try { recognition.start(); } catch(e) {}
                    }
                };
                recognitionRef.current = recognition;
            }
            try {
                if (statusRef.current !== 'processing' && statusRef.current !== 'ai_speaking') {
                    recognitionRef.current.start();
                }
            } catch (e) {}
        } catch (e) { console.error(e); }
    };

    const sendTextAndProcess = (text) => {
        if (!text.trim()) return;
        setStatusWithRef('processing');
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'text', text: text }));
        }
    };

    const stopEverything = () => {
        if (wsRef.current) wsRef.current.close();
        if (mediaStreamRef.current) mediaStreamRef.current.getTracks().forEach(t => t.stop());
        if (audioContextRef.current) audioContextRef.current.close();
        if (recognitionRef.current) recognitionRef.current.stop();
        if (currentAudioRef.current) {
            currentAudioRef.current.pause();
            currentAudioRef.current = null;
        }
    };

    const loopRef = useRef(null);
    const detectVoiceActivity = () => {
        if (!analyserRef.current) return;
        if (loopRef.current) cancelAnimationFrame(loopRef.current);
        loop();
    };

    const loop = () => {
        if (!analyserRef.current) return;
        const bufferLength = analyserRef.current.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyserRef.current.getByteFrequencyData(dataArray);

        // Calculate volume for status feedback
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) sum += dataArray[i];
        const average = sum / bufferLength;

        // Threshold for "User Speaking" visual feedback (approx 15-20 for normal speech)
        if (average > 15 && statusRef.current === 'listening') {
            setStatusWithRef('user_voice_detected');
        } else if (average < 5 && statusRef.current === 'user_voice_detected') {
            setStatusWithRef('listening');
        }

        const canvas = document.getElementById('voice-visualizer');
        if (canvas) {
            const ctx = canvas.getContext('2d');
            const w = canvas.width;
            const h = canvas.height;
            ctx.clearRect(0, 0, w, h);
            const barWidth = (w / bufferLength) * 2.5;
            let x = 0;
            for(let i = 0; i < bufferLength; i++) {
                const barHeight = dataArray[i] / 4;
                ctx.fillStyle = i % 2 === 0 ? '#fb923c' : '#f97316';
                ctx.fillRect(x, h - barHeight, barWidth, barHeight);
                x += barWidth + 1;
            }
        }
        loopRef.current = requestAnimationFrame(loop);
    };

    const getStatusLabel = () => {
        switch (status) {
            case 'listening': return 'Listening...';
            case 'user_voice_detected':
            case 'speaking': return 'User Speaking';
            case 'processing': return 'Thinking...';
            case 'ai_speaking': return 'Agent Speaking';
            case 'disconnected': return 'Connection Lost';
            default: return 'Connecting...';
        }
    };

    if (orderConfirmed) {
        const cartTotal = cart.reduce((sum, item) => sum + (parseFloat(item.price || 0) * parseFloat(item.qty || item.quantity || 1)), 0);
        return (
            <div className="confirmation-container">
                <div className="confirmation-card">
                    <span className="success-icon">✅</span>
                    <h2>Order Confirmed!</h2>
                    <p style={{ color: '#64748b', marginBottom: '24px' }}>Your groceries will be delivered shortly.</p>

                    {cart.length > 0 && (
                        <div style={{ textAlign: 'left', marginBottom: '32px' }}>
                            <div className="summary-title">Order Summary</div>
                            <div>
                                {cart.map((item, idx) => (
                                    <div key={idx} className="summary-item">
                                        <span style={{ fontWeight: 600 }}>{item.name || `Item #${item.id}`}</span>
                                        <span>x{item.qty || item.quantity} — ₹{(parseFloat(item.price || 0) * parseFloat(item.qty || item.quantity || 1)).toFixed(0)}</span>
                                    </div>
                                ))}
                            </div>
                            <div className="cart-total-container" style={{ marginTop: '16px' }}>
                                <span>Grand Total</span>
                                <span style={{ color: '#059669', fontSize: '18px' }}>₹{cartTotal.toFixed(2)}</span>
                            </div>
                        </div>
                    )}

                    <button className="btn-start" onClick={onEndCall} style={{ width: '100%' }}>
                        Return to Store
                    </button>
                    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '6px', marginTop: '16px', fontSize: '12px', color: '#94a3b8' }}>
                        Thank you for using CartTalk <Logo size={16} showText={false} />
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="call-interface-container">
            <div className="sidebar">
                <div className="agent-info">
                    <div className={`agent-avatar ${status === 'listening' || status === 'ai_speaking' ? 'animate-glow' : ''}`} style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                        <Logo size={40} showText={false} />
                    </div>
                    <div className="agent-name">CartTalk Assistant</div>
                    <div className="agent-status"><div className="status-dot"></div> Online</div>
                    <div className="visualizer-container">
                        <canvas id="voice-visualizer" width="200" height="40"></canvas>
                    </div>
                </div>

                <div className="cart-section">
                    <div className="cart-title">Live Cart</div>
                    {cart.length === 0 ? (
                        <div className="cart-empty">Your cart is empty</div>
                    ) : (
                        <div>
                            {cart.map((item, idx) => (
                                <div key={idx} className="cart-item">
                                    <span className="cart-item-name">{item.name || `Item #${item.id || item.product_id}`}</span>
                                    <span>x{item.qty || item.quantity}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {cart.length > 0 && (
                    <div className="cart-total-container">
                        <span style={{ color: '#475569' }}>Total</span>
                        <span style={{ color: '#059669' }}>
                            ₹{cart.reduce((sum, item) => sum + (parseFloat(item.price || 0) * parseFloat(item.qty || item.quantity || 1)), 0).toFixed(2)}
                        </span>
                    </div>
                )}

                <div style={{ marginTop: 'auto', paddingTop: '20px' }}>
                    <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '1px' }}>Call Identity</div>
                    <div style={{ fontSize: '12px', fontFamily: 'monospace', color: '#cbd5e1' }}>{callId.slice(0, 12)}</div>
                </div>
            </div>

            <div className="main-content">
                <div className="chat-area">
                    {messages.length === 0 && (
                        <div className="chat-empty-state">
                            <div style={{ fontSize: '56px', marginBottom: '20px' }}>🎙️</div>
                            <h3>Voice Shopping Active</h3>
                            <p>Try saying "Add 2kg tomatoes" or "How to make chicken curry?"</p>
                        </div>
                    )}

                    {messages.map((msg, i) => (
                        <div key={i} className={`message ${msg.role}`}>
                            <div className="bubble">{msg.text}</div>
                        </div>
                    ))}

                    {status === 'processing' && (
                        <div className="message ai">
                            <div className="bubble thinking-bubble">
                                <div className="dot-flashing"></div>
                                <span style={{ marginLeft: '15px' }}>Thinking...</span>
                            </div>
                        </div>
                    )}
                    
                    {interimTranscript && (
                        <div className="message user" style={{ opacity: 0.6 }}>
                            <div className="bubble" style={{ borderStyle: 'dashed', borderWidth: '2px' }}>
                                {interimTranscript}...
                            </div>
                        </div>
                    )}
                    <div ref={chatEndRef} />
                </div>

                {stockWarning && (
                    <div style={{
                        margin: '0 0 12px 0',
                        padding: '12px 16px',
                        background: 'rgba(239,68,68,0.15)',
                        border: '1px solid rgba(239,68,68,0.5)',
                        borderRadius: '10px',
                        color: '#fca5a5',
                        fontSize: '13px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px'
                    }}>
                        <span style={{ fontSize: '18px' }}>⚠️</span>
                        <span style={{ flex: 1 }}>{stockWarning}</span>
                        <button
                            onClick={() => setStockWarning('')}
                            style={{ background: 'none', border: 'none', color: '#fca5a5', cursor: 'pointer', fontSize: '16px', padding: '0 4px' }}
                        >✕</button>
                    </div>
                )}

                <div className="controls-area">
                    <div className="status-badge" data-status={status}>
                        <div className={`status-dot ${status === 'speaking' || status === 'ai_speaking' ? 'pulse-animation' : ''}`}></div>
                        {getStatusLabel()}
                    </div>

                    <button className="btn-end" onClick={onEndCall}>
                        End Session
                    </button>
                </div>
            </div>
        </div>
    );
}

export default CallInterface;
