import { useNavigate } from "react-router-dom";

export default function Sidebar({ chats, onSelect, onNew }) {
    const navigate = useNavigate();

    return (
        <div className="sidebar" style={{
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
            padding: '20px',
            backgroundColor: '#050505'
        }}>
            <h2>UISS</h2>
            <p style={{ fontSize: '12px', color: '#666' }}>UNASAT Intelligent Support System</p>

            <button onClick={onNew} style={styles.newBtn}>
                + New Chat
            </button>

            <div className="chat-history" style={{ flex: 1, overflowY: 'auto', marginTop: '20px' }}>
                {chats.map(chat => (
                    <div
                        key={chat.id}
                        className="chat-history-item"
                        onClick={() => onSelect(chat.id)}
                        style={styles.historyItem}
                    >
                        {chat.title}
                    </div>
                ))}
            </div>

            {/* THE SPACER - This pushes everything below it to the bottom */}
            <div style={{ flex: 1 }}></div>

            <div className="sidebar-footer" style={{ borderTop: '1px solid #222', paddingTop: '15px' }}>
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
    newBtn: { width: '100%', padding: '10px', backgroundColor: '#1a1a1a', color: 'white', border: '1px solid #333', borderRadius: '5px', cursor: 'pointer' },
    historyItem: { padding: '10px', cursor: 'pointer', color: '#ccc', fontSize: '14px' },
    adminBtn: {
        width: '100%',
        padding: '10px',
        background: 'transparent',
        color: '#4f46e5', // Purple color to make it stand out
        border: '1px solid #4f46e5',
        borderRadius: '5px',
        cursor: 'pointer',
        fontWeight: 'bold'
    }
};