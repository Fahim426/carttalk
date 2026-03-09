import React, { useState, useEffect } from 'react';

function LowStockProducts() {
    const [lowStock, setLowStock] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchLowStock();
    }, []);

    const fetchLowStock = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/admin/low-stock');
            const data = await res.json();
            setLowStock(data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div>Loading Low Stock...</div>;

    return (
        <div className="low-stock-card" style={{ background: '#fef2f2', padding: '24px', borderRadius: '16px', border: '1px solid #fecaca', boxShadow: '0 4px 10px rgba(239,68,68,0.05)' }}>
            <h4 style={{ margin: '0 0 20px', color: '#ef4444', textTransform: 'uppercase', letterSpacing: '0.5px', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '18px' }}>⚠️</span> Low Stock Products
            </h4>

            {lowStock.length === 0 ? (
                <div style={{ color: '#059669', fontWeight: 600 }}>All products are sufficiently stocked.</div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {lowStock.map(p => (
                        <div key={p.product_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', background: 'white', border: '1px solid #fca5a5', borderRadius: '8px' }}>
                            <span style={{ fontWeight: 600, color: '#475569' }}>{p.product_name}</span>
                            <span style={{ color: '#b91c1c', fontWeight: 800, fontSize: '16px' }}>
                                {p.stock}
                            </span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default LowStockProducts;
