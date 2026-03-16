import { useState } from 'react';
import Message from "../components/Chat/Message";
import Sidebar from "../components/Layout/Sidebar";

const ChatPage = () => {
    const [messages, setMessages] = useState([
        { role: 'ai', content: 'Hallo! Ik ben het UNASAT Intelligent Support System. Hoe kan ik u vandaag helpen?' }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [activeConversationId, setActiveConversationId] = useState(null);
    const [chats] = useState([]);

    const handleSend = async () => {
        // Voorkom lege berichten of dubbel verzenden
        if (!input.trim() || isLoading) return;

        const userMessage = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);

        const currentQuery = input;
        setInput('');
        setIsLoading(true);

        try {
            const response = await fetch('http://localhost:8000/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: currentQuery,
                    conversation_id: activeConversationId
                }),
            });

            if (!response.ok) throw new Error(`Server status: ${response.status}`);

            const data = await response.json();

            // Werk de ID bij voor de volgende vraag in dit gesprek
            if (data.conversation_id && data.conversation_id !== activeConversationId) {
                setActiveConversationId(data.conversation_id);
            }

            setMessages(prev => [...prev, {
                role: 'ai',
                content: data.answer || "Ik heb geen antwoord kunnen vinden in de documenten."
            }]);

        } catch (error) {
            console.error("Connection Error:", error);
            setMessages(prev => [...prev, {
                role: 'ai',
                content: "Error: De server is onbereikbaar. Controleer of de backend draait."
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const startNewChat = () => {
        setMessages([{ role: 'ai', content: 'Nieuwe sessie gestart. Hoe kan ik helpen?' }]);
        setActiveConversationId(null);
    };

    return (
        <div style={styles.container}>
            <Sidebar
                chats={chats}
                onNew={startNewChat}
                onSelect={(id) => setActiveConversationId(id)}
            />

            <main style={styles.main}>
                <header style={styles.header}>
                    <h1 style={styles.title}>UNASAT Intelligent Support System</h1>
                </header>

                <div style={styles.chatWindow}>
                    {messages.map((msg, index) => (
                        <Message
                            key={index}
                            role={msg.role}
                            content={msg.content}
                        />
                    ))}

                    {isLoading && (
                        <div style={styles.aiRow}>
                            <div style={styles.aiBubble}>
                                <div style={styles.loadingDots}>Thinking...</div>
                            </div>
                        </div>
                    )}
                </div>

                <div style={styles.inputContainer}>
                    <div style={styles.inputArea}>
                        <input
                            style={styles.input}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            // Gebruik onKeyDown in plaats van onKeyPress
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                    handleSend();
                                }
                            }}
                            placeholder="Stel een vraag over de reglementen..."
                            disabled={isLoading}
                        />
                        <button
                            onClick={handleSend}
                            style={isLoading ? { ...styles.sendBtn, opacity: 0.5 } : styles.sendBtn}
                            disabled={isLoading}
                        >
                            {isLoading ? '...' : 'Send'}
                        </button>
                    </div>
                </div>
            </main>
        </div>
    );
};

const styles = {
    container: { display: 'flex', height: '100vh', width: '100vw', backgroundColor: '#000', color: 'white', overflow: 'hidden' },
    main: { flex: 1, display: 'flex', flexDirection: 'column', backgroundColor: '#000' },
    header: { padding: '20px', borderBottom: '1px solid #111', textAlign: 'center' },
    title: { fontSize: '18px', margin: 0, color: '#fff', fontWeight: '400', letterSpacing: '1px' },
    chatWindow: { flex: 1, padding: '20px 40px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px' },
    aiRow: { alignSelf: 'flex-start', maxWidth: '75%' },
    aiBubble: { backgroundColor: '#1a1a1a', padding: '12px 18px', borderRadius: '18px 18px 18px 0', border: '1px solid #333', color: '#e0e0e0', fontSize: '15px' },
    inputContainer: { borderTop: '1px solid #111', paddingBottom: '20px' },
    inputArea: { padding: '20px', display: 'flex', gap: '12px', maxWidth: '900px', margin: '0 auto', width: '100%' },
    input: { flex: 1, padding: '14px 20px', borderRadius: '12px', border: '1px solid #333', backgroundColor: '#0f0f0f', color: 'white', outline: 'none', fontSize: '15px' },
    sendBtn: { padding: '0 30px', backgroundColor: '#4f46e5', color: 'white', border: 'none', borderRadius: '12px', fontWeight: 'bold', cursor: 'pointer' },
    loadingDots: { fontStyle: 'italic', color: '#888' }
};

export default ChatPage;