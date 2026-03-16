import { useNavigate } from "react-router-dom";

export default function Sidebar({ chats, onSelect, onNew, activeId }) {
    const navigate = useNavigate();

    return (
        <div className="sidebar" style={styles.sidebarContainer}>
            <h2>UISS</h2>
            <p style={{ fontSize: '12px', color: '#666', marginBottom: '20px' }}>
                UNASAT Intelligent Support System
            </p>

            <button onClick={onNew} style={styles.newBtn}>
                + New Chat
            </button>

            {/* De chat-history container krijgt flex: 1 zodat deze de ruimte vult en scrolt indien nodig */}
            <div className="chat-history" style={styles.historyContainer}>
                {chats.map(chat => (
                    <div
                        key={chat.id}
                        className={`chat-history-item ${chat.id === activeId ? 'active' : ''}`}
                        onClick={() => onSelect(chat.id)}
                        style={{
                            ...styles.historyItem,
                            backgroundColor: chat.id === activeId ? '#1a1a1a' : 'transparent',
                            color: chat.id === activeId ? '#4f46e5' : '#ccc',
                            borderLeft: chat.id === activeId ? '3px solid #4f46e5' : '3px solid transparent'
                        }}
                    >
                        {chat.title || `Chat #${chat.id}`}
                    </div>
                ))}
            </div>

            <div className="sidebar-footer" style={styles.footer}>
                <button
                    onClick={() => navigate("/admin")}
                    style={styles.adminBtn}
                >
                    ⚙️ System Admin
                </button>
            </div>
        </div>
    );
}

const styles = {
    sidebarContainer: {
        display: 'flex',
        flexDirection: 'column',
        width: '260px', // Vaste breedte voor een zijbalk
        height: '100%',
        padding: '20px',
        backgroundColor: '#050505',
        borderRight: '1px solid #111'
    },
    newBtn: {
        width: '100%',
        padding: '12px',
        backgroundColor: '#1a1a1a',
        color: 'white',
        border: '1px solid #333',
        borderRadius: '8px',
        cursor: 'pointer',
        transition: 'all 0.2s'
    },
    historyContainer: {
        flex: 1,
        overflowY: 'auto',
        marginTop: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '5px'
    },
    historyItem: {
        padding: '12px',
        cursor: 'pointer',
        fontSize: '14px',
        borderRadius: '5px',
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        transition: '0.2s'
    },
    footer: {
        borderTop: '1px solid #222',
        paddingTop: '15px',
        marginTop: '10px'
    },
    adminBtn: {
        width: '100%',
        padding: '10px',
        background: 'transparent',
        color: '#4f46e5',
        border: '1px solid #4f46e5',
        borderRadius: '5px',
        cursor: 'pointer',
        fontWeight: 'bold'
    }
};