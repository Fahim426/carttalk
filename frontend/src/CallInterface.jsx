import React, { useState, useEffect, useRef } from 'react';

function CallInterface({ callId, onEndCall }) {
    const [transcript, setTranscript] = useState('Initializing...');
    const [status, setStatus] = useState('initializing'); // initializing, listening, speaking, processing, ai_speaking

    // Refs for audio handling
    const wsRef = useRef(null);
    const audioContextRef = useRef(null);
    const mediaStreamRef = useRef(null);
    const analyserRef = useRef(null);
    const silenceTimerRef = useRef(null);
    const isSpeakingRef = useRef(false);

    // Audio processing constants
    const VAD_THRESHOLD = 15; // Volume threshold (0-255)
    const SILENCE_DURATION = 1500;

    // Buffer to store audio chunks while speaking
    const audioChunksRef = useRef([]);

    // Ref to track currently playing audio
    const currentAudioRef = useRef(null);

    useEffect(() => {
        // 1. Setup WebSocket
        wsRef.current = new WebSocket(`ws://localhost:8000/api/call/${callId}/stream`);

        wsRef.current.onopen = () => {
            console.log("WebSocket connected");
            startListening();
        };

        wsRef.current.onmessage = (event) => {
            console.log("Received AI Audio, size:", event.data.size);
            if (event.data.size === 0) {
                setTranscript("Error: No audio from AI");
                startListening();
                return;
            }

            setStatus('ai_speaking');
            setTranscript("AI is speaking...");

            const blob = new Blob([event.data], { type: 'audio/mp3' });
            const url = URL.createObjectURL(blob);
            const audio = new Audio(url);
            currentAudioRef.current = audio; // Track current audio

            audio.onended = () => {
                currentAudioRef.current = null;
                setIsSpeaking(false);
                setStatus('listening');
                startListening();
                setTranscript("Listening...");
            };

            audio.play().catch(e => {
                console.error("Audio play error", e);
                startListening();
            });
        };

        wsRef.current.onerror = (e) => console.error("WS Error", e);

        // Cleanup
        return () => {
            stopEverything();
        };
    }, [callId]);

    const setIsSpeaking = (val) => {
        isSpeakingRef.current = val;
    }

    const startListening = async () => {
        try {
            if (audioContextRef.current?.state === 'suspended') {
                await audioContextRef.current.resume();
            }

            // If already set up, just resume logic
            if (mediaStreamRef.current) {
                setStatus('listening');
                setTranscript("Listening...");
                detectVoiceActivity();
                return;
            }

            // Init Audio Context & Stream
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
            setTranscript("Listening...");
            detectVoiceActivity();

        } catch (e) {
            console.error("Mic Access Error", e);
            setTranscript("Microphone Access Denied");
        }
    };

    const stopEverything = () => {
        if (wsRef.current) wsRef.current.close();
        if (mediaStreamRef.current) mediaStreamRef.current.getTracks().forEach(t => t.stop());
        if (audioContextRef.current) audioContextRef.current.close();
        // Stop any currently playing audio
        if (currentAudioRef.current) {
            currentAudioRef.current.pause();
            currentAudioRef.current = null;
        }
        clearTimeout(silenceTimerRef.current);
    };

    // VAD Loop
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

        // Determine if speaking based on threshold
        if (volume > VAD_THRESHOLD) {
            if (!isSpeakingRef.current) {
                console.log("Speech Started");
                isSpeakingRef.current = true;
                setStatus('speaking');
                setTranscript("I'm listening...");
                startRecordingChunk();
            }
            // Reset silence timer
            if (silenceTimerRef.current) {
                clearTimeout(silenceTimerRef.current);
                silenceTimerRef.current = null;
            }
        } else if (isSpeakingRef.current) {
            // Speech explicitly ended
            if (!silenceTimerRef.current) {
                silenceTimerRef.current = setTimeout(() => {
                    console.log("Silence Detected -> Sending");
                    stopRecordingAndSend();
                    if (loopRef.current) cancelAnimationFrame(loopRef.current);
                    return;
                }, SILENCE_DURATION);
            }
        }

        loopRef.current = requestAnimationFrame(loop);
    };


    // Recorder Logic
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
        } catch (e) {
            console.error("Recorder start error", e);
        }
    };

    const stopRecordingAndSend = () => {
        if (!recorderRef.current) return;

        setStatus('processing');
        setTranscript("Thinking...");
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

    // Status visual
    const getStatusColor = () => {
        switch (status) {
            case 'listening': return '#28a745'; // Green
            case 'speaking': return '#ffc107'; // Yellow
            case 'processing': return '#17a2b8'; // Blue
            case 'ai_speaking': return '#dc3545'; // Red
            default: return '#6c757d';
        }
    };

    const getStatusText = () => {
        switch (status) {
            case 'listening': return 'Waiting for you...';
            case 'speaking': return 'Listening to you...';
            case 'processing': return 'Thinking...';
            case 'ai_speaking': return 'AI Speaking...';
            default: return 'Initializing...';
        }
    }

    return (
        <div className="call-interface">
            <div className="transcript">
                <h2>Live Conversation</h2>
                <p>{transcript}</p>
            </div>

            <div className="status-indicator" style={{
                textAlign: 'center', margin: '20px 0', padding: '10px',
                backgroundColor: getStatusColor(), color: 'white', borderRadius: '5px',
                fontWeight: 'bold', transition: 'background-color 0.3s'
            }}>
                {getStatusText()}
            </div>

            <div className="controls">
                <button onClick={onEndCall} className="btn-secondary">
                    📞 End Call
                </button>
            </div>

            <div style={{ marginTop: '20px', fontSize: '0.8em', color: '#666', textAlign: 'center' }}>
                Hands-Free Mode Enabled. Speak naturally.
            </div>
        </div>
    );
}

export default CallInterface;
