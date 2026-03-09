import React, { useState } from 'react';
import CallInterface from './CallInterface';
import AdminDashboard from './AdminDashboard';
import AdminLogin from './AdminLogin';
import ProductGrid from './ProductGrid';
import OrderHistory from './OrderHistory';
import './App.css';

function App() {
    // AOS Removed for performance

    const [isCallActive, setIsCallActive] = useState(false);
    const [callId, setCallId] = useState(null);
    const [viewMode, setViewMode] = useState('home'); // home | login | admin | history
    const [user, setUser] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');

    const startCall = async () => {
        let currentUser = user;

        // Identity Verification: Enforce Login before call
        if (!currentUser) {
            const phone = prompt("To ensure we save your order history, please enter your Phone Number:");
            if (!phone) return; // User cancelled

            try {
                const res = await fetch('http://localhost:8000/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ phone })
                });
                const data = await res.json();
                if (data.user) {
                    setUser(data.user);
                    currentUser = data.user; // Use immediately
                } else {
                    alert("Login failed. Please try again.");
                    return;
                }
            } catch (e) {
                console.error("Login Error", e);
                alert("Login system error. Please try again.");
                return;
            }
        }

        const body = currentUser ? { user_id: currentUser.phone } : {};
        try {
            const res = await fetch('http://localhost:8000/api/call/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            const data = await res.json();
            setCallId(data.call_id);
            setIsCallActive(true);
        } catch (e) {
            console.error("Start Call Error", e);
            alert("Could not start call. Please check backend.");
        }
    };

    // handleCustomerLogin removed as it's no longer used in UI directly

    const handleMerchantLogin = () => {
        if (user) {
            const confirmLogout = window.confirm("You are currently logged in as a Customer. Switch to Merchant login? This will log you out.");
            if (!confirmLogout) return;
            setUser(null); // Logout customer
        }
        setViewMode('login');
    };

    if (viewMode === 'admin') {
        return (
            <div style={{ position: 'relative' }}>
                <button
                    style={{ position: 'absolute', top: 15, right: 40, zIndex: 1000, background: '#f8fafc', color: '#ef4444', border: '1px solid #fecaca', fontWeight: 600, padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}
                    onClick={() => setViewMode('home')}
                >
                    Logout to Store ➡️
                </button>
                <AdminDashboard />
            </div>
        );
    }

    if (viewMode === 'history') {
        return <OrderHistory user={user} onBack={() => setViewMode('home')} />;
    }

    if (viewMode === 'login') {
        return (
            <div>
                <button
                    style={{ position: 'absolute', top: 20, left: 20, zIndex: 1000, background: 'transparent', color: '#64748b', border: 'None', cursor: 'pointer', fontSize: '16px' }}
                    onClick={() => setViewMode('home')}
                >
                    ← Back to Store
                </button>
                <AdminLogin onLogin={() => setViewMode('admin')} />
            </div>
        );
    }

    return (
        <div className="app">
            {/* Navigation */}
            <nav className="navbar">
                <div className="nav-left">
                    <div className="logo" onClick={() => setViewMode('home')}>
                        <span className="logo-icon">🛒</span>
                        CartTalk.
                    </div>
                </div>

                <div className="nav-center">
                    <div className="search-bar">
                        <input
                            type="text"
                            placeholder="Search for grocery, vegetables, spices..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                        <button className="search-btn">🔍</button>
                    </div>
                </div>

                <div className="nav-right">
                    {user && (
                        <button className="btn-merchant" onClick={() => setViewMode('history')} style={{ color: '#10b981' }}>
                            📋 My Orders
                        </button>
                    )}
                    <button className="btn-merchant" onClick={handleMerchantLogin}>Merchant</button>
                    <div className="user-avatar" onClick={startCall} title={user ? `Logged in: ${user.name || user.phone}` : 'Click to start shopping'}>
                        {user ? (
                            <span style={{ fontSize: '12px', color: 'white', fontWeight: 700 }}>
                                {(user.name || user.phone || '?')[0].toUpperCase()}
                            </span>
                        ) : (
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                        )}
                    </div>
                    {user && <span style={{ fontSize: '12px', color: '#64748b', maxWidth: '80px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user.name || user.phone}</span>}
                </div>
            </nav>

            {!isCallActive ? (
                <>
                    <div className="hero-section">
                        <div className="hero-content">
                            <h1>Speak. Shop.<br /><span className="highlight-text">Delivered.</span></h1>

                            <p className="hero-subtext">
                                Discover the freshest and finest groceries<br />
                                delivered quickly and conveniently.
                            </p>

                            <div className="hero-actions">
                                <button className="btn-shop-now" onClick={startCall}>
                                    Shop Now
                                    <span className="btn-icon">🛍️</span>
                                </button>
                            </div>
                        </div>

                        <div className="hero-visual">
                            {/* AI generated image */}
                            <img src="./my-grocery.jpeg" alt="Groceries in paper bag" className="hero-bag-img" />
                        </div>
                    </div>

                    {/* How It Works */}
                    <div className="how-it-works">
                        <h2 className="section-title" style={{ textAlign: 'center', borderLeft: 'none', paddingLeft: 0 }}>How It Works</h2>
                        <p className="section-subtitle" style={{ textAlign: 'center' }}>Three simple steps to get your groceries</p>
                        <div className="steps-row">
                            <div className="step-card">
                                <div className="step-icon">🎙️</div>
                                <div className="step-number">1</div>
                                <h3>Speak</h3>
                                <p>Tell our AI assistant what groceries you need — in English or Malayalam</p>
                            </div>
                            <div className="step-connector">→</div>
                            <div className="step-card">
                                <div className="step-icon">🛒</div>
                                <div className="step-number">2</div>
                                <h3>Cart</h3>
                                <p>AI builds your cart automatically, suggests recipes, and calculates total</p>
                            </div>
                            <div className="step-connector">→</div>
                            <div className="step-card">
                                <div className="step-icon">🚚</div>
                                <div className="step-number">3</div>
                                <h3>Delivered</h3>
                                <p>Confirm your order and get fresh groceries delivered to your doorstep</p>
                            </div>
                        </div>
                    </div>

                    <ProductGrid searchQuery={searchQuery} />
                </>
            ) : (
                <CallInterface callId={callId} onEndCall={() => setIsCallActive(false)} />
            )}

            {/* Footer */}
            {!isCallActive && (
                <footer style={{
                    textAlign: 'center',
                    padding: '30px 20px',
                    borderTop: '1px solid var(--border-color)',
                    color: '#94a3b8',
                    fontSize: '13px',
                    marginTop: '40px'
                }}>
                    <div style={{ marginBottom: '8px' }}>
                        <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>🛒 CartTalk</span> — Speak. Shop. Delivered.
                    </div>
                    <div>Powered by Google Gemini AI &bull; © {new Date().getFullYear()} CartTalk</div>
                </footer>
            )}
        </div>
    );
}

export default App;
