import React, { useState, useEffect } from 'react';
import './AdminDashboard.css';

function AdminDashboard() {
    const [orders, setOrders] = useState([]);
    const [products, setProducts] = useState([]);
    const [activeTab, setActiveTab] = useState('orders'); // orders | inventory

    // Auto-refresh orders every 5s
    useEffect(() => {
        fetchOrders();
        const interval = setInterval(fetchOrders, 5000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (activeTab === 'inventory') fetchProducts();
    }, [activeTab]);

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
        name_en: '', name_ml: '', category: 'Vegetables', price: '', stock: '', image_url: ''
    });

    const handleEdit = (product) => {
        setNewProduct(product);
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
        const payload = { ...newProduct, price: parseFloat(newProduct.price), stock: parseInt(newProduct.stock) };

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
            setNewProduct({ name_en: '', name_ml: '', category: 'Vegetables', price: '', stock: '', image_url: '' });
            fetchProducts();
        } catch (err) {
            alert("Failed to save product");
        }
    };

    const cancelEdit = () => {
        setShowForm(false);
        setEditingId(null);
        setNewProduct({ name_en: '', name_ml: '', category: 'Vegetables', price: '', stock: '', image_url: '' });
    };

    return (
        <div className="admin-container">
            <div className="admin-sidebar">
                <h2>CartTalk Admin</h2>
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
                {activeTab === 'orders' ? (
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
                                    <th>Link</th>
                                </tr>
                            </thead>
                            <tbody>
                                {orders.map(order => (
                                    <tr key={order.id}>
                                        <td>#{order.id}</td>
                                        <td>{order.customer_name || 'Unknown'}</td>
                                        <td>{order.customer_address || '-'}</td>
                                        <td>
                                            {/* We rely on 'transcript' or need to join items. For now show status. */}
                                            <span style={{ fontSize: '12px', color: '#666' }}>Check DB</span>
                                        </td>
                                        <td>
                                            <span className={`badge ${order.status}`}>
                                                {order.status}
                                            </span>
                                        </td>
                                        <td>
                                            {order.status !== 'Delivered' && (
                                                <button onClick={() => updateStatus(order.id, 'Delivered')}>
                                                    Mark Delivered
                                                </button>
                                            )}
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
                            <button onClick={() => { setShowForm(true); setEditingId(null); setNewProduct({ name_en: '', name_ml: '', category: 'Vegetables', price: '', stock: '', image_url: '' }); }}>
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
                                <input type="number" placeholder="Stock" required value={newProduct.stock} onChange={e => setNewProduct({ ...newProduct, stock: e.target.value })} />

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
                                        <td>₹{p.price}</td>
                                        <td>
                                            <button style={{ fontSize: '12px', padding: '4px 8px' }} onClick={() => handleEdit(p)}>
                                                ✏️ Edit
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
