import React, { useState, useEffect } from 'react';
import './OrderHistory.css';

function OrderHistory({ user, onBack }) {
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchOrders();
    }, [user]);

    const fetchOrders = async () => {
        if (!user || !user.phone) return;
        try {
            const res = await fetch(`http://localhost:8000/api/orders/user?phone=${user.phone}`);
            const data = await res.json();
            setOrders(data);
            setLoading(false);
        } catch (e) {
            console.error("Failed to fetch orders", e);
            setLoading(false);
        }
    };

    return (
        <div className="order-history-container">
            <div className="header-row">
                <button className="btn-back" onClick={onBack}>← Back to Store</button>
                <h2>My Orders</h2>
                <div></div>
            </div>

            {loading ? (
                <div className="loading-state">Loading your orders...</div>
            ) : orders.length === 0 ? (
                <div className="empty-state">
                    <h3>No orders yet!</h3>
                    <p>Start a call to place your first order.</p>
                </div>
            ) : (
                <div className="orders-list">
                    {orders.map(order => (
                        <div key={order.id} className="order-item-card">
                            <div className="order-header">
                                <span className="order-id">Order #{order.id}</span>
                                <span className={`order-status status-${order.status.toLowerCase()}`}>
                                    {order.status}
                                </span>
                            </div>
                            <div className="order-body">
                                <div className="order-info">
                                    <span className="label">Date:</span>
                                    <span className="value">{new Date(order.created_at).toLocaleString()}</span>
                                </div>
                                <div className="order-info">
                                    <span className="label">Address:</span>
                                    <span className="value">{order.customer_address}</span>
                                </div>
                                <div className="order-info" style={{ marginTop: '10px' }}>
                                    <span className="label">Order Request (Transcript):</span>
                                    <div className="value" style={{ background: '#f8fafc', padding: '10px', borderRadius: '8px', fontSize: '13px', fontStyle: 'italic', marginTop: '5px', color: '#475569' }}>
                                        {order.transcript || "No details captured."}
                                    </div>
                                </div>
                                <div className="order-total">
                                    Total: ₹{order.total}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default OrderHistory;
