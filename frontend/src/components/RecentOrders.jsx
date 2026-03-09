import React, { useState, useEffect } from 'react';

function RecentOrders() {
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchRecentOrders();
    }, []);

    const fetchRecentOrders = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/admin/recent-orders');
            const data = await res.json();
            setOrders(data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div>Loading Recent Orders...</div>;
    if (orders.length === 0) return <div>No recent orders.</div>;

    return (
        <div className="recent-orders-card" style={{ background: 'white', padding: '24px', borderRadius: '16px', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-sm)' }}>
            <h4 style={{ margin: '0 0 20px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px', fontSize: '14px' }}>
                Recent Orders
            </h4>
            <div style={{ overflowX: 'auto' }}>
                <table className="admin-table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead>
                        <tr style={{ borderBottom: '1px solid var(--border-color)', color: '#94a3b8', fontSize: '12px' }}>
                            <th style={{ padding: '12px 16px' }}>Order ID</th>
                            <th style={{ padding: '12px 16px' }}>Customer</th>
                            <th style={{ padding: '12px 16px' }}>Items</th>
                            <th style={{ padding: '12px 16px' }}>Amount</th>
                            <th style={{ padding: '12px 16px' }}>Status</th>
                            <th style={{ padding: '12px 16px' }}>Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        {orders.map(order => (
                            <tr key={order.order_id} style={{ borderBottom: '1px solid #f1f5f9', fontSize: '13px' }}>
                                <td style={{ padding: '12px 16px', fontWeight: 600 }}>#{order.order_id}</td>
                                <td style={{ padding: '12px 16px' }}>{order.customer_name}</td>
                                <td style={{ padding: '12px 16px', maxWidth: '200px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={order.items}>{order.items}</td>
                                <td style={{ padding: '12px 16px', color: '#059669', fontWeight: 600 }}>₹{order.total_amount?.toFixed(2)}</td>
                                <td style={{ padding: '12px 16px' }}>
                                    <span style={{ padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', background: order.status === 'Delivered' ? '#dcfce7' : '#fef9c3', color: order.status === 'Delivered' ? '#166534' : '#854d0e' }}>
                                        {order.status}
                                    </span>
                                </td>
                                <td style={{ padding: '12px 16px', color: '#64748b' }}>{order.created_at}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default RecentOrders;
