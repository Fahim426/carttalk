import React, { useState, useEffect, useMemo } from 'react';
import './ProductGrid.css';

function ProductGrid({ searchQuery = '' }) {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchProducts();
    }, []);

    const fetchProducts = async () => {
        try {
            setLoading(true);
            const res = await fetch('http://localhost:8000/api/products');
            const data = await res.json();
            setProducts(data);
        } catch (e) {
            console.error("Failed to fetch products", e);
        } finally {
            setLoading(false);
        }
    };

    // Live filter with useMemo for performance
    const filteredProducts = useMemo(() => {
        const query = searchQuery.trim().toLowerCase();
        if (!query) return products;
        return products.filter(product =>
            product.name_en?.toLowerCase().includes(query) ||
            product.name_ml?.toLowerCase().includes(query) ||
            product.category?.toLowerCase().includes(query)
        );
    }, [products, searchQuery]);

    // Group products by category
    const groupedProducts = filteredProducts.reduce((acc, product) => {
        const category = product.category || 'Others';
        if (!acc[category]) acc[category] = [];
        acc[category].push(product);
        return acc;
    }, {});

    // Sort categories
    const categoryOrder = ['Fruits', 'Vegetables', 'Dairy', 'Cereals', 'Spices', 'Meat', 'Oils', 'Pantry', 'Beverages', 'Others'];
    const sortedCategories = Object.keys(groupedProducts).sort((a, b) => {
        const indexA = categoryOrder.indexOf(a);
        const indexB = categoryOrder.indexOf(b);
        if (indexA === -1 && indexB === -1) return a.localeCompare(b);
        if (indexA === -1) return 1;
        if (indexB === -1) return -1;
        return indexA - indexB;
    });

    // Component to handle scroll reveals per category row
    const CategoryGroup = ({ category, categoryProducts }) => {
        const [isVisible, setIsVisible] = useState(false);
        const ref = React.useRef(null);

        React.useEffect(() => {
            const observer = new IntersectionObserver(([entry]) => {
                if (entry.isIntersecting) {
                    setIsVisible(true);
                    observer.disconnect(); // Trigger once only
                }
            }, { threshold: 0.15 });

            if (ref.current) observer.observe(ref.current);
            return () => observer.disconnect();
        }, []);

        return (
            <div ref={ref} className={`category-group ${isVisible ? 'is-visible' : ''}`}>
                <h3 className="category-title">{category}</h3>
                <div className="product-grid">
                    {categoryProducts.map((product, index) => (
                        <div className="product-card" key={product.id}>
                            {/* Stable discount badge based on product ID */}
                            <span className="badge-sale">{((product.id * 7 + 3) % 30) + 5}% off</span>

                            {product.stock <= 0 && <span className="badge-out">Out of Stock</span>}

                            <div className="image-container">
                                {product.image_url ? (
                                    <img src={product.image_url} alt={product.name_en} loading="lazy" />
                                ) : (
                                    <div className="placeholder-image">{product.category?.[0] || '📦'}</div>
                                )}
                            </div>

                            <div className="card-details">
                                <h3 className="product-name">{product.name_en}</h3>
                                <p className="product-subtitle">{product.category?.toLowerCase() || 'fresh'} (loose), 1 kg</p>

                                <div className="card-bottom">
                                    <span className="price">₹{product.price}</span>
                                    <button className="btn-add-circle" onClick={() => alert("Please use the 'Start Shopping' Voice Assistant to add items to your cart!")}>
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <line x1="12" y1="5" x2="12" y2="19"></line>
                                            <line x1="5" y1="12" x2="19" y2="12"></line>
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    return (
        <div className="product-section">
            <h2 className="section-title">
                {searchQuery.trim() ? `Results for "${searchQuery.trim()}"` : 'Explore Our Products'}
            </h2>
            <p className="section-subtitle">
                {searchQuery.trim() ? `${filteredProducts.length} item${filteredProducts.length !== 1 ? 's' : ''} found` : 'Freshly stocked for you'}
            </p>

            {loading ? (
                <div className="product-grid" style={{ marginTop: '30px' }}>
                    {[...Array(8)].map((_, i) => (
                        <div className="skeleton-card" key={i}>
                            <div className="skeleton-image skeleton-pulse" />
                            <div className="skeleton-details">
                                <div className="skeleton-line skeleton-pulse" style={{ width: '70%' }} />
                                <div className="skeleton-line skeleton-pulse" style={{ width: '50%', height: '10px' }} />
                                <div className="skeleton-line skeleton-pulse" style={{ width: '40%', marginTop: '12px' }} />
                            </div>
                        </div>
                    ))}
                </div>
            ) : filteredProducts.length === 0 && searchQuery.trim() ? (
                <div style={{ textAlign: 'center', padding: '60px 20px', color: '#94a3b8' }}>
                    <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
                    <h3 style={{ color: '#475569', marginBottom: '8px' }}>No products found</h3>
                    <p>Try searching for "tomato", "chicken", "masala", or a category like "spices"</p>
                </div>
            ) : (
                sortedCategories.map(category => (
                    <CategoryGroup key={category} category={category} categoryProducts={groupedProducts[category]} />
                ))
            )}
        </div>
    );
}

export default ProductGrid;
