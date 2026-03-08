import React, { useState } from 'react';
import './AdminLogin.css';

function AdminLogin({ onLogin }) {
    const [isLoginView, setIsLoginView] = useState(true);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [email, setEmail] = useState(''); // Just for show/validation if needed
    const [error, setError] = useState('');
    const [successMsg, setSuccessMsg] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        setError('');
        setSuccessMsg('');

        if (isLoginView) {
            // Login Logic
            const storedUsers = JSON.parse(localStorage.getItem('merchant_users') || '[]');

            const cleanInput = username.trim().toLowerCase();
            const cleanPass = password; // Passwords are case sensitive

            // Default admin check
            const isValidDefault = (cleanInput === 'admin') && (cleanPass === 'admin123');

            // Stored user check (Case insensitive username/email)
            const isValidStored = storedUsers.some(u =>
                ((u.username && u.username.toLowerCase() === cleanInput) ||
                    (u.email && u.email.toLowerCase() === cleanInput)) &&
                u.password === cleanPass
            );

            if (isValidDefault || isValidStored) {
                onLogin();
            } else {
                console.log("Login Failed. Input:", cleanInput, "Stored:", storedUsers);
                setError('Invalid credentials');
            }
        } else {
            // Sign Up Logic
            if (!username.trim() || !password || !email.trim()) {
                setError('All fields are required');
                return;
            }

            const storedUsers = JSON.parse(localStorage.getItem('merchant_users') || '[]');
            const cleanUser = username.trim().toLowerCase();
            const cleanEmail = email.trim().toLowerCase();

            const userExists = storedUsers.some(u =>
                (u.username && u.username.toLowerCase() === cleanUser) ||
                (u.email && u.email.toLowerCase() === cleanEmail)
            );

            if (userExists) {
                setError('Username or Email already exists');
                return;
            }

            const newUser = {
                username: username.trim(),
                email: email.trim(),
                password: password
            };

            const updatedUsers = [...storedUsers, newUser];
            localStorage.setItem('merchant_users', JSON.stringify(updatedUsers));

            setSuccessMsg('Account created! Please log in.');
            setIsLoginView(true);
            // Don't clear username so they can login easily
            // setUsername(username.trim()); 
            setPassword(''); // Clear password for security
        }
    };

    return (
        <div className="login-container">
            <div className="login-card">
                <div className="login-header">
                    <div className="logo-icon-lg">🛒</div>
                    <h2>{isLoginView ? 'Merchant Login' : 'Create Account'}</h2>
                    <p>{isLoginView ? 'Enter your credentials to access the dashboard' : 'Start managing your store inventory today'}</p>
                </div>

                <form onSubmit={handleSubmit} className="login-form">
                    {!isLoginView && (
                        <div className="form-group">
                            <label>Email Address</label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="merchant@example.com"
                            />
                        </div>
                    )}

                    <div className="form-group">
                        <label>Username</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder={isLoginView ? "admin" : "StoreName"}
                        />
                    </div>

                    <div className="form-group">
                        <label>Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                        />
                    </div>

                    {error && <div className="error-message">{error}</div>}
                    {successMsg && <div className="success-message" style={{ color: '#10b981', background: 'rgba(16, 185, 129, 0.1)', padding: '10px', borderRadius: '8px', marginBottom: '15px', textAlign: 'center' }}>{successMsg}</div>}

                    <button type="submit" className="btn-login-submit">
                        {isLoginView ? 'Sign In' : 'Register Merchant'}
                    </button>
                </form>

                <div className="login-footer">
                    <p onClick={() => { setIsLoginView(!isLoginView); setError(''); setSuccessMsg(''); }}>
                        {isLoginView ? "Don't have an account? Create one" : "Already have an account? Sign In"}
                    </p>
                </div>
            </div>
        </div>
    );
}

export default AdminLogin;
