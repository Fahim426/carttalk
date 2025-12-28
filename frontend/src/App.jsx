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
            {/* Navigation */}
            <nav className="navbar">
                <div className="logo">
                    <div className="logo-icon">C</div>
                    CartTalk
                </div>
                <div className="nav-links">
                    <span>Solution</span>
                    <span>Integration</span>
                    <span>Pricing</span>
                </div>
                <button className="btn-login" onClick={() => alert("Demo Mode Only")}>Login</button>
            </nav>

            {!isCallActive ? (
                <div className="hero-section">
                    <div className="hero-content">
                        <h1>Seamless, intelligent & human-like AI Shopping</h1>
                        <p className="hero-subtext">
                            Experience the future of grocery shopping. Just speak naturally to our AI agent to fill your cart, check prices, and place orders instantly.
                        </p>

                        <div className="hero-actions">
                            <button className="btn-start" onClick={startCall}>
                                Start Demo Call
                            </button>
                            <button className="btn-secondary-outline">
                                View Documentation
                            </button>
                        </div>

                        <div className="stats-row">
                            <div className="stat-item">
                                <span className="stat-number">24/7</span>
                                <span className="stat-label">Availability</span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-number">0.5s</span>
                                <span className="stat-label">Latency</span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-number">100%</span>
                                <span className="stat-label">Hassle Free</span>
                            </div>
                        </div>
                    </div>

                    <div className="hero-visual">
                        {/* Abstract Visual Representation */}
                        <div className="visual-card">
                            <div className="visual-header">
                                <div className="dot red"></div>
                                <div className="dot yellow"></div>
                                <div className="dot green"></div>
                            </div>
                            <div className="visual-body">
                                <div className="chat-mockup user">
                                    "I need 2kg of Tomatoes and some eggs"
                                </div>
                                <div className="chat-mockup ai">
                                    "Added to your cart! Anything else?"
                                </div>
                                <div className="chat-mockup user">
                                    "That will be all."
                                </div>
                                <div className="visual-wave">
                                    <div className="bar" style={{ height: '40%' }}></div>
                                    <div className="bar" style={{ height: '80%' }}></div>
                                    <div className="bar" style={{ height: '60%' }}></div>
                                    <div className="bar" style={{ height: '90%' }}></div>
                                    <div className="bar" style={{ height: '50%' }}></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            ) : (
                <CallInterface callId={callId} onEndCall={() => setIsCallActive(false)} />
            )}
        </div>
    );
}

export default App;
