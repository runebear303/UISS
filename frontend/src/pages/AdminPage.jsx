
import MetricsDashboard from '../components/Admin/MetricsDashboard';
import SecurityLogsTable from '../components/Admin/SecurityLogsTable';

const AdminPage = () => {
    // Voor nu gebruiken we de tijdelijke token. 
    // Zodra de Login-pagina af is, komt deze uit de localStorage of een Context.
    const tempToken = "admin-secret-token";

    return (
        <div style={adminStyles.pageContainer}>
            <header style={adminStyles.header}>
                <div>
                    <h1 style={adminStyles.title}>UISS Control Center</h1>
                    <p style={adminStyles.subtitle}>UNASAT Intelligent Support System • Internal Monitoring</p>
                </div>
                <button
                    onClick={() => window.location.href = "/"}
                    style={adminStyles.backBtn}
                >
                    ← Back to Chat
                </button>
            </header>

            <main style={adminStyles.mainContent}>
                {/* 1. De cijfers: Hoeveel wordt er gevraagd en wat kost het? */}
                <section style={adminStyles.section}>
                    <MetricsDashboard token={tempToken} />
                </section>

                {/* 2. De beveiliging: Wie probeert de AI te foppen? */}
                <section style={adminStyles.section}>
                    <SecurityLogsTable token={tempToken} />
                </section>
            </main>

            <footer style={adminStyles.footer}>
                <p>© 2026 UNASAT - Intelligent Support System Security Panel</p>
            </footer>
        </div>
    );
};

const adminStyles = {
    pageContainer: {
        backgroundColor: '#000',
        minHeight: '100vh',
        padding: '40px',
        color: '#fff',
        fontFamily: 'system-ui, sans-serif'
    },
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '40px',
        borderBottom: '1px solid #222',
        paddingBottom: '20px'
    },
    title: {
        color: '#4f46e5',
        margin: 0,
        fontSize: '28px',
        letterSpacing: '-0.5px'
    },
    subtitle: {
        color: '#666',
        margin: '5px 0 0 0'
    },
    mainContent: {
        maxWidth: '1200px',
        margin: '0 auto'
    },
    section: {
        marginBottom: '30px'
    },
    backBtn: {
        padding: '10px 20px',
        background: '#111',
        color: '#fff',
        border: '1px solid #333',
        cursor: 'pointer',
        borderRadius: '8px',
        fontSize: '14px',
        transition: '0.3s'
    },
    footer: {
        marginTop: '60px',
        textAlign: 'center',
        color: '#333',
        fontSize: '12px',
        borderTop: '1px solid #111',
        paddingTop: '20px'
    }
};

export default AdminPage;