import React, { useState, useEffect, useRef } from 'react';

function CallInterface({ callId, onEndCall }) {
    const [status, setStatus] = useState('initializing'); // initializing, listening, speaking, processing, ai_speaking
    const [messages, setMessages] = useState([]);

    // Refs for audio
    const wsRef = useRef(null);
    const audioContextRef = useRef(null);
    const mediaStreamRef = useRef(null);
    const analyserRef = useRef(null);
    const silenceTimerRef = useRef(null);
    const isSpeakingRef = useRef(false);
    const currentAudioRef = useRef(null);
    const audioChunksRef = useRef([]);

    const VAD_THRESHOLD = 15;
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
                } catch (e) { console.error(e); }
                return;
            }

            // 2. Audio Message (Binary)
            if (event.data.size === 0) {
                startListening();
                return;
            }

            setStatus('ai_speaking');

            const blob = new Blob([event.data], { type: 'audio/mp3' });
            const url = URL.createObjectURL(blob);
            const audio = new Audio(url);
            currentAudioRef.current = audio;

            audio.onprev = () => { }; // No-op

            audio.onended = () => {
                currentAudioRef.current = null;
                setIsSpeaking(false);
                setStatus('listening');
                startListening();
            };

            audio.play().catch(e => {
                console.error("Audio play error", e);
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
                setStatus('listening');
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

            setStatus('listening');
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

    const detectVoiceActivity = () => {
        if (!analyserRef.current) return;
        loop();
    };

    const loopRef = useRef(null);
    const loop = () => {
        if (!analyserRef.current) return;
        const bufferLength = analyserRef.current.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyserRef.current.getByteFrequencyData(dataArray);
        const volume = dataArray.reduce((a, b) => a + b) / bufferLength;

        if (volume > VAD_THRESHOLD) {
            if (!isSpeakingRef.current) {
                isSpeakingRef.current = true;
                setStatus('speaking');
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
                    if (loopRef.current) cancelAnimationFrame(loopRef.current);
                    return;
                }, SILENCE_DURATION);
            }
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
        setStatus('processing');
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

    return (
        <div className="dashboard-container">
            {/* Sidebar */}
            <div className="sidebar">
                <div className="agent-info">
                    <div className="agent-avatar">🛒</div>
                    <div className="agent-name">CartTalk Agent</div>
                    <div className="agent-status">
                        <div className="status-dot"></div> Online
                    </div>
                </div>

                <div style={{ marginTop: 'auto' }}>
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
