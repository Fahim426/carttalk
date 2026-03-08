import React, { useState, useEffect, useRef } from 'react';

function CallInterface({ callId, onEndCall }) {
    const [status, setStatus] = useState('initializing'); // initializing, listening, speaking, processing, ai_speaking
    const statusRef = useRef('initializing'); // Keep track immediately for logic without stale closures
    const setStatusWithRef = (newStatus) => {
        statusRef.current = newStatus;
        setStatus(newStatus);
    };
    const [messages, setMessages] = useState([]);
    const [cart, setCart] = useState([]);
    const [orderConfirmed, setOrderConfirmed] = useState(false);

    // Refs for audio
    const wsRef = useRef(null);
    const audioContextRef = useRef(null);
    const mediaStreamRef = useRef(null);
    const analyserRef = useRef(null);
    const silenceTimerRef = useRef(null);
    const isSpeakingRef = useRef(false);
    const currentAudioRef = useRef(null);
    const audioChunksRef = useRef([]);
    const endCallAfterAudioRef = useRef(false);

    const VAD_THRESHOLD = 35; // Increased threshold to avoid background noise triggering quota exhaustion

    const SILENCE_DURATION = 1500;

    // Scroll ref
    const chatEndRef = useRef(null);

    useEffect(() => {
        // Scroll to bottom
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, status]);

    useEffect(() => {
        wsRef.current = new WebSocket(`ws://localhost:8000/api/call/${callId}/stream`);

        wsRef.current.onopen = () => {
            console.log("WebSocket connected");
            startListening();
        };

        wsRef.current.onmessage = (event) => {
            // 1. Text Message (JSON)
            if (typeof event.data === 'string') {
                try {
                    const msg = JSON.parse(event.data);

                    if (msg.type === 'transcript') {
                        setMessages(prev => [...prev, { role: msg.role, text: msg.text }]);
                    }

                    if (msg.type === 'cart') {
                        setCart(msg.cart || []);
                    }

                    if (msg.type === 'control' && msg.action === 'terminate') {
                        endCallAfterAudioRef.current = true;
                        // Trigger immediately if no audio reply was generated/received
                        if (!currentAudioRef.current) {
                            setOrderConfirmed(true);
                        }
                    }

                    if (msg.type === 'error') {
                        // Unblock UI
                        setStatusWithRef('listening');
                        alert(msg.text); // Optional visual feedback
                        startListening();
                    }

                } catch (e) { console.error(e); }
                return;
            }

            // 2. Audio Message (Binary)
            if (event.data.size === 0) {
                setStatusWithRef('listening');
                startListening();
                return;
            }

            setStatusWithRef('ai_speaking');

            const blob = new Blob([event.data], { type: 'audio/mp3' });
            const url = URL.createObjectURL(blob);
            const audio = new Audio(url);
            currentAudioRef.current = audio;

            audio.onprev = () => { }; // No-op

            audio.onended = () => {
                currentAudioRef.current = null;
                setIsSpeaking(false);

                if (endCallAfterAudioRef.current) {
                    setOrderConfirmed(true);
                    return;
                }

                setStatusWithRef('listening');
                startListening();
            };

            audio.play().catch(e => {
                console.error("Audio play error", e);
                currentAudioRef.current = null;

                if (endCallAfterAudioRef.current) {
                    setOrderConfirmed(true);
                    return;
                }
                startListening();
            });
        };

        wsRef.current.onerror = (e) => console.error("WS Error", e);

        return () => { stopEverything(); };
    }, [callId]);

    const setIsSpeaking = (val) => { isSpeakingRef.current = val; }

    const startListening = async () => {
        try {
            if (audioContextRef.current?.state === 'suspended') {
                await audioContextRef.current.resume();
            }
            if (mediaStreamRef.current) {
                setStatusWithRef('listening');
                detectVoiceActivity();
                return;
            }
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaStreamRef.current = stream;

            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            audioContextRef.current = audioContext;

            const source = audioContext.createMediaStreamSource(stream);
            const analyser = audioContext.createAnalyser();
            analyser.fftSize = 512;
            source.connect(analyser);
            analyserRef.current = analyser;

            setStatusWithRef('listening');
            detectVoiceActivity();
        } catch (e) {
            console.error(e);
            setMessages(prev => [...prev, { role: 'system', text: "Microphone Access Denied" }]);
        }
    };

    const stopEverything = () => {
        if (wsRef.current) wsRef.current.close();
        if (mediaStreamRef.current) mediaStreamRef.current.getTracks().forEach(t => t.stop());
        if (audioContextRef.current) audioContextRef.current.close();
        if (currentAudioRef.current) {
            currentAudioRef.current.pause();
            currentAudioRef.current = null;
        }
        clearTimeout(silenceTimerRef.current);
    };

    const loopRef = useRef(null);
    const detectVoiceActivity = () => {
        if (!analyserRef.current) return;
        if (loopRef.current) {
            cancelAnimationFrame(loopRef.current);
            loopRef.current = null;
        }
        loop();
    };


    const loop = () => {
        if (!analyserRef.current) return;
        const bufferLength = analyserRef.current.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyserRef.current.getByteFrequencyData(dataArray);
        const volume = dataArray.reduce((a, b) => a + b) / bufferLength;

        if (volume > VAD_THRESHOLD) {
            if (!isSpeakingRef.current) {
                isSpeakingRef.current = true;
                setStatusWithRef('speaking');
                startRecordingChunk();
            }
            if (silenceTimerRef.current) {
                clearTimeout(silenceTimerRef.current);
                silenceTimerRef.current = null;
            }
        } else if (isSpeakingRef.current) {
            if (!silenceTimerRef.current) {
                silenceTimerRef.current = setTimeout(() => {
                    stopRecordingAndSend();
                    if (loopRef.current) {
                        cancelAnimationFrame(loopRef.current);
                        loopRef.current = null;
                    }
                    return;
                }, SILENCE_DURATION);
            }
        }

        // Stop the loop completely if we are processing or playing AI audio
        // The startListening function will restart it when appropriate.
        if (!isSpeakingRef.current && statusRef && (statusRef.current === 'processing' || statusRef.current === 'ai_speaking')) {
            return;
        }

        loopRef.current = requestAnimationFrame(loop);
    };

    const recorderRef = useRef(null);
    const startRecordingChunk = () => {
        if (recorderRef.current && recorderRef.current.state !== 'inactive') return;
        try {
            const recorder = new MediaRecorder(mediaStreamRef.current);
            recorderRef.current = recorder;
            audioChunksRef.current = [];
            recorder.ondataavailable = (e) => {
                if (e.data.size > 0) audioChunksRef.current.push(e.data);
            };
            recorder.start();
        } catch (e) { console.error(e); }
    };

    const stopRecordingAndSend = () => {
        if (!recorderRef.current) return;
        setStatusWithRef('processing');
        isSpeakingRef.current = false;
        recorderRef.current.onstop = () => {
            const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
            if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                wsRef.current.send(blob);
            }
            audioChunksRef.current = [];
        };
        recorderRef.current.stop();
    };

    const getStatusLabel = () => {
        switch (status) {
            case 'listening': return 'Listening...';
            case 'speaking': return 'User Speaking...';
            case 'processing': return 'Thinking...';
            case 'ai_speaking': return 'Agent Speaking...';
            default: return 'Connecting...';
        }
    };

    if (orderConfirmed) {
        const cartTotal = cart.reduce((sum, item) => sum + (parseFloat(item.price || 0) * parseFloat(item.qty || item.quantity || 1)), 0);
        return (
            <div className="dashboard-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', background: '#f8fafc' }}>
                <div style={{ background: 'white', padding: '40px', borderRadius: '16px', boxShadow: '0 4px 20px rgba(0,0,0,0.1)', textAlign: 'center', maxWidth: '420px', width: '100%' }}>
                    <div style={{ fontSize: '64px', color: '#10b981', marginBottom: '16px' }}>✅</div>
                    <h2 style={{ marginBottom: '6px' }}>Order Confirmed!</h2>
                    <p style={{ color: '#64748b', marginBottom: '24px', fontSize: '14px' }}>Your groceries will be delivered shortly.</p>

                    {cart.length > 0 && (
                        <div style={{ textAlign: 'left', marginBottom: '24px' }}>
                            <div style={{ fontSize: '13px', fontWeight: 700, color: '#475569', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Order Summary</div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                {cart.map((item, idx) => (
                                    <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: '#f8fafc', borderRadius: '8px', fontSize: '13px' }}>
                                        <span style={{ color: '#334155', fontWeight: 500 }}>{item.name || `Item #${item.id}`}</span>
                                        <span style={{ color: '#64748b' }}>x{item.qty || item.quantity} — ₹{(parseFloat(item.price || 0) * parseFloat(item.qty || item.quantity || 1)).toFixed(0)}</span>
                                    </div>
                                ))}
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px', padding: '12px', background: '#ecfdf5', borderRadius: '10px', fontWeight: 700 }}>
                                <span style={{ color: '#475569' }}>Total</span>
                                <span style={{ color: '#059669', fontSize: '16px' }}>₹{cartTotal.toFixed(2)}</span>
                            </div>
                        </div>
                    )}

                    <button className="btn-start" onClick={onEndCall} style={{ width: '100%' }}>
                        Return to Store
                    </button>
                    <p style={{ fontSize: '12px', color: '#94a3b8', marginTop: '12px' }}>Thank you for using CartTalk 🛒</p>
                </div>
            </div>
        );
    }

    return (
        <div className="dashboard-container">
            {/* Sidebar */}
            <div className="sidebar" style={{ display: 'flex', flexDirection: 'column' }}>
                <div className="agent-info">
                    <div className={`agent-avatar ${status === 'listening' || status === 'ai_speaking' ? 'animate-glow' : ''}`}>🛒</div>
                    <div className="agent-name">CartTalk Agent</div>
                    <div className="agent-status">
                        <div className="status-dot"></div> Online
                    </div>
                </div>

                {/* Cart Visualization */}
                <div style={{ marginTop: '20px', flex: 1, overflowY: 'auto' }}>
                    <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#475569', marginBottom: '12px' }}>Your Cart</div>
                    {cart.length === 0 ? (
                        <div style={{ fontSize: '13px', color: '#94a3b8', fontStyle: 'italic' }}>Cart is empty</div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            {cart.map((item, idx) => (
                                <div key={idx} style={{ background: '#f1f5f9', padding: '10px', borderRadius: '8px', fontSize: '13px', display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ fontWeight: '500', color: '#334155', maxWidth: '120px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{item.name || `Item #${item.id || item.product_id}`}</span>
                                    <span style={{ color: '#64748b' }}>x{item.qty || item.quantity}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Cart Total */}
                {cart.length > 0 && (
                    <div style={{
                        marginTop: '12px',
                        padding: '12px',
                        background: '#ecfdf5',
                        borderRadius: '10px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        fontSize: '14px',
                        fontWeight: '700'
                    }}>
                        <span style={{ color: '#475569' }}>Total</span>
                        <span style={{ color: '#059669' }}>
                            ₹{cart.reduce((sum, item) => sum + (parseFloat(item.price || 0) * parseFloat(item.qty || item.quantity || 1)), 0).toFixed(2)}
                        </span>
                    </div>
                )}

                <div style={{ marginTop: '20px' }}>
                    <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>CALL ID</div>
                    <div style={{ fontSize: '14px', fontFamily: 'monospace', color: '#64748b' }}>{callId.slice(0, 8)}...</div>
                </div>
            </div>

            {/* Main Chat Area */}
            <div className="main-content">
                <div className="chat-area">
                    {messages.length === 0 && (
                        <div style={{ textAlign: 'center', color: '#94a3b8', marginTop: '100px' }}>
                            <div style={{ fontSize: '48px', marginBottom: '16px' }}>👋</div>
                            <p>Say "Hello" to start shopping!</p>
                        </div>
                    )}

                    {messages.map((msg, i) => (
                        <div key={i} className={`message ${msg.role}`}>
                            <div className="bubble">
                                {msg.text}
                            </div>
                        </div>
                    ))}

                    {/* Thinking Indicator */}
                    {status === 'processing' && (
                        <div className="message ai">
                            <div className="bubble" style={{ fontStyle: 'italic', color: '#94a3b8' }}>
                                Thinking...
                            </div>
                        </div>
                    )}
                    <div ref={chatEndRef} />
                </div>

                {/* Bottom Controls */}
                <div className="controls-area">
                    <div className="status-badge" data-status={status}>
                        <div className={`status-dot ${status === 'speaking' || status === 'ai_speaking' ? 'pulse-animation' : ''}`}></div>
                        {getStatusLabel()}
                    </div>

                    <button className="btn-end" onClick={onEndCall}>
                        End Call
                    </button>
                </div>
            </div>
        </div>
    );
}

export default CallInterface;
