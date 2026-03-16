import React, { useState, useEffect } from 'react';

const MetricsDashboard = ({ token }) => {
    const [stats, setStats] = useState({
        total_conversations: 0,
        total_ai_cost: 0,
        average_tokens_per_request: 0
    });

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const response = await fetch('http://localhost:8000/api/admin/stats', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (response.ok) {
                    const data = await response.json();
                    setStats(data);
                }
            } catch (err) {
                console.error("Dashboard data kon niet worden geladen:", err);
            }
        };
        fetchStats();
    }, [token]);

    return (
        <div style={dashStyles.grid}>
            <div style={dashStyles.card}>
                <h3>Total Chats</h3>
                <p style={dashStyles.value}>{stats.total_conversations}</p>
            </div>
            <div style={dashStyles.card}>
                <h3>Total AI Cost</h3>
                <p style={dashStyles.value}>${stats.total_ai_cost.toFixed(4)}</p>
            </div>
            <div style={dashStyles.card}>
                <h3>Avg Tokens</h3>
                <p style={dashStyles.value}>{Math.round(stats.average_tokens_per_request)}</p>
            </div>
        </div>
    );
};

const dashStyles = {
    grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' },
    card: { backgroundColor: '#111', padding: '20px', borderRadius: '10px', border: '1px solid #222' },
    value: { fontSize: '24px', fontWeight: 'bold', color: '#4f46e5', margin: '10px 0 0 0' }
};

export default MetricsDashboard;