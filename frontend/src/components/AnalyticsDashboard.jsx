import React, { useState, useEffect } from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from 'recharts';
import RecentOrders from './RecentOrders';
import LowStockProducts from './LowStockProducts';
import TopProducts from './TopProducts';
import VoiceLogs from './VoiceLogs';

function AnalyticsDashboard() {
    const [data, setData] = useState({
        orders_today: 0,
        revenue_today: 0,
        total_products: 0,
        low_stock_products: 0,
        most_sold_product: "N/A",
        orders_last_7_days: []
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchAnalytics();
    }, []);

    const fetchAnalytics = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/admin/analytics');
            const json = await res.json();
            if (!json.error) {
                setData(json);
            } else {
                console.error(json.error);
            }
        } catch (err) {
            console.error("Failed to fetch analytics:", err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return <div style={{ padding: '20px' }}>Loading analytics...</div>;
    }

    return (
        <div className="analytics-dashboard">
            <h3>Merchant Analytics Dashboard</h3>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginBottom: '30px' }}>
                <div className="metric-card">
                    <h4>Orders Today</h4>
                    <div className="metric-value">{data.orders_today}</div>
                </div>

                <div className="metric-card">
                    <h4>Revenue Today</h4>
                    <div className="metric-value">₹{data.revenue_today.toFixed(2)}</div>
                </div>

                <div className="metric-card">
                    <h4>Total Products</h4>
                    <div className="metric-value">{data.total_products}</div>
                </div>

                <div className="metric-card" style={data.low_stock_products > 0 ? { background: '#fef2f2', border: '1px solid #fecaca' } : {}}>
                    <h4 style={data.low_stock_products > 0 ? { color: '#ef4444' } : {}}>Low Stock Products</h4>
                    <div className="metric-value" style={data.low_stock_products > 0 ? { color: '#b91c1c' } : {}}>{data.low_stock_products}</div>
                </div>

            </div>

            <div className="chart-container" style={{ background: 'white', padding: '24px', borderRadius: '16px', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-sm)' }}>
                <h4 style={{ margin: '0 0 20px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px', fontSize: '14px' }}>
                    Orders (Last 7 Days)
                </h4>
                <div style={{ width: '100%', height: 300 }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data.orders_last_7_days}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                            <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
                            <YAxis allowDecimals={false} tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
                            <Tooltip
                                contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 14px rgba(0,0,0,0.1)' }}
                                itemStyle={{ color: 'var(--primary-color)', fontWeight: 600 }}
                            />
                            <Line
                                type="monotone"
                                dataKey="orders"
                                stroke="var(--primary-color)"
                                strokeWidth={3}
                                dot={{ r: 4, fill: 'var(--primary-color)', strokeWidth: 2, stroke: 'white' }}
                                activeDot={{ r: 6, fill: 'var(--primary-color)', strokeWidth: 0 }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 1fr)', gap: '24px', marginTop: '24px' }}>
                <RecentOrders />
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    <LowStockProducts />
                    <TopProducts />
                </div>
            </div>

            <div style={{ marginTop: '24px', marginBottom: '40px' }}>
                <VoiceLogs />
            </div>
        </div>
    );
}

export default AnalyticsDashboard;
