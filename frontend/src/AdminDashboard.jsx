import React, { useState, useEffect } from 'react';
import './AdminDashboard.css';

function AdminDashboard() {
    const [orders, setOrders] = useState([]);
    const [products, setProducts] = useState([]);
    const [activeTab, setActiveTab] = useState('overview'); // overview | orders | inventory
    const [expandedTranscripts, setExpandedTranscripts] = useState({});

    const toggleTranscript = (id) => {
        setExpandedTranscripts(prev => ({ ...prev, [id]: !prev[id] }));
    };

    // Auto-refresh initial data
    useEffect(() => {
        fetchOrders();
        fetchProducts(); // Need products initially for Low Stock Dashboard
        const interval = setInterval(() => {
            fetchOrders();
        }, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchOrders = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/orders');
            const data = await res.json();
            setOrders(data);
        } catch (e) { console.error(e); }
    };

    const fetchProducts = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/products');
            const data = await res.json();
            setProducts(data);
        } catch (e) { console.error(e); }
    };

    const updateStatus = async (id, status) => {
        await fetch(`http://localhost:8000/api/orders/${id}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        fetchOrders();
    };

    const [showForm, setShowForm] = useState(false);
    const [editingId, setEditingId] = useState(null);
    const [newProduct, setNewProduct] = useState({
        name_en: '', name_ml: '', category: 'Vegetables', price: '', stock: '', image_url: '', safety_stock: 5
    });

    const handleEdit = (product) => {
        setNewProduct({ ...product, safety_stock: product.safety_stock || 5 });
        setEditingId(product.id);
        setShowForm(true);
    };

    const handleUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('http://localhost:8000/api/upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            setNewProduct(prev => ({ ...prev, image_url: data.url }));
        } catch (err) {
            alert("Upload failed");
        }
    };

    const handleSaveProduct = async (e) => {
        e.preventDefault();
        const payload = {
            ...newProduct,
            price: parseFloat(newProduct.price),
            stock: parseInt(newProduct.stock),
            safety_stock: parseInt(newProduct.safety_stock || 5)
        };

        try {
            if (editingId) {
                // Update
                await fetch(`http://localhost:8000/api/products/${editingId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            } else {
                // Create
                await fetch('http://localhost:8000/api/products', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            }
            setShowForm(false);
            setEditingId(null);
            setNewProduct({ name_en: '', name_ml: '', category: 'Vegetables', price: '', stock: '', image_url: '', safety_stock: 5 });
            fetchProducts();
        } catch (err) {
            alert("Failed to save product");
        }
    };

    const cancelEdit = () => {
        setShowForm(false);
        setEditingId(null);
        setNewProduct({ name_en: '', name_ml: '', category: 'Vegetables', price: '', stock: '', image_url: '', safety_stock: 5 });
    };

    const deleteOrder = async (id) => {
        if (!confirm("Are you sure you want to delete this order?")) return;
        try {
            await fetch(`http://localhost:8000/api/orders/${id}`, { method: 'DELETE' });
            fetchOrders();
        } catch (e) {
            alert("Failed to delete order");
        }
    };

    const deleteProduct = async (id) => {
        if (!confirm("Are you sure you want to delete this product?")) return;
        try {
            await fetch(`http://localhost:8000/api/products/${id}`, { method: 'DELETE' });
            fetchProducts();
        } catch (e) {
            alert("Failed to delete product");
        }
    };

    return (
        <div className="admin-container">
            <div className="admin-sidebar">
                <h2>CartTalk Admin</h2>
                <div
                    className={`menu-item ${activeTab === 'overview' ? 'active' : ''}`}
                    onClick={() => setActiveTab('overview')}
                >
                    📊 Overview
                </div>
                <div
                    className={`menu-item ${activeTab === 'orders' ? 'active' : ''}`}
                    onClick={() => setActiveTab('orders')}
                >
                    📦 Orders
                </div>
                <div
                    className={`menu-item ${activeTab === 'inventory' ? 'active' : ''}`}
                    onClick={() => setActiveTab('inventory')}
                >
                    🥬 Inventory
                </div>
            </div>

            <div className="admin-content">
                {activeTab === 'overview' ? (
                    <div className="overview-view">
                        <h3>Dashboard Overview</h3>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px', marginBottom: '30px' }}>
                            <div className="metric-card">
                                <h4>Total Revenue</h4>
                                <div className="metric-value">₹{(orders.reduce((sum, o) => sum + (o.total || 0), 0)).toFixed(2)}</div>
                            </div>
                            <div className="metric-card">
                                <h4>Pending Orders</h4>
                                <div className="metric-value">{orders.filter(o => o.status !== 'Delivered').length}</div>
                            </div>
                            <div className="metric-card" style={{ background: '#fef2f2', border: '1px solid #fecaca' }}>
                                <h4 style={{ color: '#ef4444' }}>Low Stock Items</h4>
                                <div className="metric-value" style={{ color: '#b91c1c' }}>{products.filter(p => p.stock <= (p.safety_stock || 5)).length}</div>
                            </div>
                        </div>

                        <h3 style={{ marginTop: '40px' }}>Low Stock Alerts</h3>
                        {products.filter(p => p.stock <= (p.safety_stock || 5)).length > 0 ? (
                            <table className="admin-table">
                                <thead><tr><th>Item</th><th>Current Stock</th><th>Safe Limit</th></tr></thead>
                                <tbody>
                                    {products.filter(p => p.stock <= (p.safety_stock || 5)).map(p => (
                                        <tr key={p.id}>
                                            <td>{p.name_en}</td>
                                            <td style={{ color: '#ef4444', fontWeight: 'bold' }}>{p.stock}</td>
                                            <td>{p.safety_stock || 5}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        ) : (
                            <div style={{ padding: '20px', background: 'white', borderRadius: '12px', border: '1px solid var(--border-color)', color: '#059669', fontWeight: 500 }}>
                                ✅ All products are well stocked.
                            </div>
                        )}
                    </div>
                ) : activeTab === 'orders' ? (
                    <div className="orders-view">
                        <h3>Live Orders</h3>
                        <table className="admin-table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Customer</th>
                                    <th>Address</th>
                                    <th>Items</th>
                                    <th>Status</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {orders.map(order => (
                                    <tr key={order.id}>
                                        <td>#{order.id}</td>
                                        <td>{order.customer_name || 'Unknown'}</td>
                                        <td>{order.customer_address || '-'}</td>
                                        <td style={{ maxWidth: '300px', fontSize: '13px' }}>
                                            {order.items && order.items.length > 0 ? (
                                                <div style={{ marginBottom: '10px' }}>
                                                    {order.items.map((item, idx) => (
                                                        <div key={idx} style={{ padding: '4px 0', borderBottom: '1px solid #f1f5f9' }}>
                                                            <strong style={{ color: 'var(--primary-color)' }}>{item.quantity}x</strong> {item.name}
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : (
                                                <div style={{ color: '#94a3b8', fontStyle: 'italic', marginBottom: '10px' }}>No items parsed</div>
                                            )}

                                            <button
                                                onClick={() => toggleTranscript(order.id)}
                                                style={{ background: 'transparent', color: '#64748b', boxShadow: 'none', padding: '0', fontSize: '12px', textDecoration: 'underline' }}
                                            >
                                                {expandedTranscripts[order.id] ? 'Hide Transcript' : 'Show Original Transcript'}
                                            </button>

                                            {expandedTranscripts[order.id] && (
                                                <div style={{ marginTop: '10px', maxHeight: '100px', overflowY: 'auto', background: '#f8fafc', padding: '8px', borderRadius: '4px', whiteSpace: 'pre-wrap', fontSize: '12px', border: '1px solid var(--border-color)' }}>
                                                    {order.transcript ? order.transcript : <span style={{ color: '#94a3b8', fontStyle: 'italic' }}>No transcript available</span>}
                                                </div>
                                            )}
                                        </td>
                                        <td>
                                            <span className={`badge ${order.status}`}>
                                                {order.status}
                                            </span>
                                        </td>
                                        <td style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                                            {order.status !== 'Delivered' && (
                                                <button onClick={() => updateStatus(order.id, 'Delivered')} style={{ fontSize: '12px' }}>
                                                    Mark Delivered
                                                </button>
                                            )}
                                            <button
                                                onClick={() => deleteOrder(order.id)}
                                                style={{ background: '#ef4444', fontSize: '12px' }}
                                            >
                                                Delete
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="inventory-view">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <h3>Product Inventory</h3>
                            <button onClick={() => { setShowForm(true); setEditingId(null); setNewProduct({ name_en: '', name_ml: '', category: 'Vegetables', price: '', stock: '', image_url: '', safety_stock: 5 }); }}>
                                + Add Product
                            </button>
                        </div>

                        {showForm && (
                            <form className="add-product-form" onSubmit={handleSaveProduct}>
                                <h4 style={{ gridColumn: 'span 2', margin: '0 0 10px' }}>{editingId ? 'Edit Product' : 'New Product'}</h4>

                                <input placeholder="Name (English)" required value={newProduct.name_en} onChange={e => setNewProduct({ ...newProduct, name_en: e.target.value })} />
                                <input placeholder="Name (Malayalam)" value={newProduct.name_ml} onChange={e => setNewProduct({ ...newProduct, name_ml: e.target.value })} />
                                <select value={newProduct.category} onChange={e => setNewProduct({ ...newProduct, category: e.target.value })}>
                                    <option>Vegetables</option>
                                    <option>Fruits</option>
                                    <option>Meat</option>
                                    <option>Dairy</option>
                                    <option>Spices</option>
                                    <option>Grains</option>
                                    <option>Beverages</option>
                                    <option>Oils</option>
                                    <option>Pantry</option>
                                </select>
                                <input type="number" placeholder="Price (₹)" required value={newProduct.price} onChange={e => setNewProduct({ ...newProduct, price: e.target.value })} />
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                                    <input type="number" placeholder="Stock" required value={newProduct.stock} onChange={e => setNewProduct({ ...newProduct, stock: e.target.value })} />
                                    <input type="number" placeholder="Safe Limit" title="Min stock kept for walk-ins" value={newProduct.safety_stock} onChange={e => setNewProduct({ ...newProduct, safety_stock: e.target.value })} />
                                </div>

                                <div style={{ gridColumn: 'span 2', display: 'flex', gap: '10px' }}>
                                    <input placeholder="Image URL (Unsplash/Imgur)" value={newProduct.image_url} onChange={e => setNewProduct({ ...newProduct, image_url: e.target.value })} style={{ flex: 1 }} />
                                    <div style={{ position: 'relative', overflow: 'hidden', display: 'inline-block' }}>
                                        <button type="button">Upload 📁</button>
                                        <input type="file" onChange={handleUpload} style={{ position: 'absolute', left: 0, top: 0, opacity: 0, cursor: 'pointer' }} />
                                    </div>
                                </div>
                                {newProduct.image_url && <img src={newProduct.image_url} alt="preview" style={{ width: '50px', height: '50px', borderRadius: '4px', marginTop: '5px' }} />}

                                <div style={{ gridColumn: 'span 2', display: 'flex', gap: '10px', marginTop: '10px' }}>
                                    <button type="submit">{editingId ? 'Update' : 'Save'}</button>
                                    <button type="button" onClick={cancelEdit} style={{ background: '#64748b' }}>Cancel</button>
                                </div>
                            </form>
                        )}

                        <table className="admin-table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Image</th>
                                    <th>Name</th>
                                    <th>Category</th>
                                    <th>Stock</th>
                                    <th>Safe Limit</th>
                                    <th>Price</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {products.map(p => (
                                    <tr key={p.id}>
                                        <td>{p.id}</td>
                                        <td>
                                            {p.image_url && <img src={p.image_url} alt="" style={{ width: 30, height: 30, borderRadius: 4, objectFit: 'cover' }} />}
                                        </td>
                                        <td>{p.name_en} / {p.name_ml}</td>
                                        <td>{p.category}</td>
                                        <td style={{ color: p.stock < 10 ? 'red' : 'inherit', fontWeight: 'bold' }}>
                                            {p.stock}
                                        </td>
                                        <td>{p.safety_stock || 5}</td>
                                        <td>₹{p.price}</td>
                                        <td>
                                            <button style={{ fontSize: '12px', padding: '4px 8px' }} onClick={() => handleEdit(p)}>
                                                ✏️ Edit
                                            </button>
                                            <button
                                                style={{ fontSize: '12px', padding: '4px 8px', marginLeft: '5px', background: '#ef4444' }}
                                                onClick={() => deleteProduct(p.id)}
                                            >
                                                Trash
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}

export default AdminDashboard;
