import React, { useState, useEffect } from 'react';
import './ProductGrid.css';

function ProductGrid() {
    const [products, setProducts] = useState([]);

    useEffect(() => {
        fetchProducts();
    }, []);

    const fetchProducts = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/products');
            const data = await res.json();
            setProducts(data);
        } catch (e) {
            console.error("Failed to fetch products", e);
        }
    };

    return (
        <div className="product-section">
            <h2 className="section-title">Featured Products</h2>
            <p className="section-subtitle">Items that you can't just miss</p>

            <div className="product-grid">
                {products.map(product => (
                    <div className="product-card" key={product.id}>
                        {product.stock <= 0 && <span className="badge-out">Out of Stock</span>}
                        {product.stock > 0 && product.stock < 20 && <span className="badge-low">Low Stock</span>}

                        <div className="image-container">
                            {product.image_url ? (
                                <img src={product.image_url} alt={product.name_en} loading="lazy" />
                            ) : (
                                <div className="placeholder-image">{product.category?.[0] || '📦'}</div>
                            )}
                        </div>

                        <div className="card-details">
                            <h3 className="product-name">{product.name_en}</h3>
                            <div className="price-row">
                                <span className="price">₹{product.price}</span>
                            </div>

                            <button className="btn-add-cart" onClick={() => alert("Please use Voice to order!")}>
                                Add to cart
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default ProductGrid;
