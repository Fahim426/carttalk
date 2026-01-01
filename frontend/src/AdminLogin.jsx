import React, { useState } from 'react';
import './AdminLogin.css';

function AdminLogin({ onLogin }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        // Simple hardcoded check for demo realism
        // In a real app, this would hit an API endpoint
        if (username === 'admin' && password === 'admin123') {
            onLogin();
        } else {
            setError('Invalid credentials');
        }
    };

    return (
        <div className="login-container">
            <div className="login-card">
                <div className="login-header">
                    <div className="logo-icon-lg">C</div>
                    <h2>Merchant Login</h2>
                    <p>Enter your credentials to access the dashboard</p>
                </div>

                <form onSubmit={handleSubmit} className="login-form">
                    <div className="form-group">
                        <label>Username</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="admin"
                        />
                    </div>

                    <div className="form-group">
                        <label>Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="admin123"
                        />
                    </div>

                    {error && <div className="error-message">{error}</div>}

                    <button type="submit" className="btn-login-submit">
                        Sign In
                    </button>
                </form>

                <div className="login-footer">
                    <p>Forgot password? Contact Support</p>
                </div>
            </div>
        </div>
    );
}

export default AdminLogin;
