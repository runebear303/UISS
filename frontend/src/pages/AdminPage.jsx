import React from 'react';
import MetricsDashboard from '../components/Admin/MetricsDashboard'; // Double check this path!

const AdminPage = () => {
    // For now, we can use a placeholder token. 
    // Later, this will come from your Login screen.
    const tempToken = "admin-secret-token";

    return (
        <div style={{ backgroundColor: '#000', minHeight: '100vh', padding: '40px' }}>
            <header style={{ marginBottom: '30px', borderBottom: '1px solid #222', paddingBottom: '10px' }}>
                <h1 style={{ color: '#4f46e5', margin: 0 }}>UISS Control Center</h1>
                <p style={{ color: '#666' }}>Internal System Monitoring</p>
            </header>

            {/* This is the component you just showed me! */}
            <MetricsDashboard token={tempToken} />

            <div style={{ marginTop: '40px' }}>
                <button
                    onClick={() => window.location.href = "/"}
                    style={{ padding: '10px 20px', background: '#111', color: '#fff', border: '1px solid #333', cursor: 'pointer', borderRadius: '5px' }}
                >
                    Return to Chat
                </button>
            </div>
        </div>
    );
};

export default AdminPage;