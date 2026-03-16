import React, { useState, useEffect } from 'react';

const SecurityLogsTable = ({ token }) => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchSecurityLogs = async () => {
            try {
                const response = await fetch('http://localhost:8000/api/admin/security', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (response.ok) {
                    const data = await response.json();
                    setLogs(data);
                }
            } catch (err) {
                console.error("Security logs laden mislukt:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchSecurityLogs();
    }, [token]);

    if (loading) return <p style={{ color: '#666' }}>Beveiligingsgegevens laden...</p>;

    return (
        <div style={secStyles.container}>
            <h3 style={secStyles.title}>🛡️ Security & Integrity Events</h3>
            <table style={secStyles.table}>
                <thead>
                    <tr style={secStyles.thRow}>
                        <th style={secStyles.th}>Tijdstip</th>
                        <th style={secStyles.th}>Type</th>
                        <th style={secStyles.th}>IP-Adres</th>
                        <th style={secStyles.th}>Bericht</th>
                    </tr>
                </thead>
                <tbody>
                    {logs.length === 0 ? (
                        <tr><td colSpan="4" style={secStyles.noData}>Geen verdachte activiteiten gedetecteerd.</td></tr>
                    ) : (
                        logs.map((log) => (
                            <tr key={log.id} style={secStyles.tr}>
                                <td style={secStyles.td}>{new Date(log.created_at).toLocaleString()}</td>
                                <td style={secStyles.td}>
                                    <span style={{
                                        ...secStyles.badge,
                                        backgroundColor: log.event_type === 'PROMPT_INJECTION' ? '#7f1d1d' : '#1e3a8a'
                                    }}>
                                        {log.event_type}
                                    </span>
                                </td>
                                <td style={secStyles.td}>{log.ip_address || 'Onbekend'}</td>
                                <td style={secStyles.td}>{log.message}</td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
};

const secStyles = {
    container: { marginTop: '30px', backgroundColor: '#111', padding: '20px', borderRadius: '10px', border: '1px solid #222' },
    title: { color: '#fff', marginBottom: '20px', fontSize: '18px' },
    table: { width: '100%', borderCollapse: 'collapse', color: '#ccc', fontSize: '14px' },
    thRow: { borderBottom: '2px solid #222', textAlign: 'left' },
    th: { padding: '12px', color: '#888', fontWeight: 'bold' },
    td: { padding: '12px', borderBottom: '1px solid #1a1a1a' },
    noData: { padding: '20px', textAlign: 'center', color: '#555' },
    badge: { padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', color: '#fff' }
};

export default SecurityLogsTable;