import React, { useState, useEffect } from 'react';

function TopProducts() {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchTopProducts();
    }, []);

    const fetchTopProducts = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/admin/top-products');
            const data = await res.json();
            setProducts(data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div>Loading...</div>;

    return (
        <div style={{ background: 'white', padding: '24px', borderRadius: '16px', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-sm)' }}>
            <h4 style={{ margin: '0 0 20px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px', fontSize: '14px' }}>
                Top Selling Products
            </h4>

            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead style={{ color: '#94a3b8', fontSize: '12px', borderBottom: '1px solid var(--border-color)' }}>
                    <tr>
                        <th style={{ padding: '8px 4px' }}>Rank</th>
                        <th style={{ padding: '8px 4px' }}>Product</th>
                        <th style={{ padding: '8px 4px', textAlign: 'right' }}>Orders</th>
                    </tr>
                </thead>
                <tbody>
                    {products.map((p, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                            <td style={{ padding: '12px 4px', color: '#cbd5e1', fontWeight: 700 }}>#{idx + 1}</td>
                            <td style={{ padding: '12px 4px', color: '#334155', fontWeight: 600 }}>{p.product_name}</td>
                            <td style={{ padding: '12px 4px', textAlign: 'right', color: 'var(--primary-color)', fontWeight: 700 }}>
                                {p.total_orders}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export default TopProducts;
