import React, { useState, useEffect } from 'react';

const Message = ({ role, content }) => {
    const [displayedText, setDisplayedText] = useState("");
    const [isDone, setIsDone] = useState(false);
    const isAssistant = role === "ai" || role === "assistant";

    useEffect(() => {
        if (!isAssistant) {
            setDisplayedText(content);
            return;
        }

        // Reset states voor een nieuwe animatie
        setDisplayedText("");
        setIsDone(false);

        let i = 0;
        const speed = 25; // Iets langzamer voor een natuurlijker effect

        const timer = setInterval(() => {
            // We gebruiken 'content.length' om te controleren of we klaar zijn
            if (i < content.length) {
                // Gebruik de substring methode, dit is veiliger voor indexering
                setDisplayedText(content.substring(0, i + 1));
                i++;
            } else {
                setIsDone(true);
                clearInterval(timer);
            }
        }, speed);

        return () => clearInterval(timer);
    }, [content, isAssistant]);

    const messageStyles = {
        userRow: { alignSelf: 'flex-end', maxWidth: '75%', marginBottom: '15px' },
        aiRow: { alignSelf: 'flex-start', maxWidth: '75%', marginBottom: '15px' },
        userBubble: {
            backgroundColor: '#4f46e5',
            padding: '12px 18px',
            borderRadius: '18px 18px 0 18px',
            color: 'white',
            fontSize: '15px'
        },
        aiBubble: {
            backgroundColor: '#1a1a1a',
            padding: '12px 18px',
            borderRadius: '18px 18px 18px 0',
            border: '1px solid #333',
            color: '#e0e0e0',
            fontSize: '15px',
            position: 'relative'
        },
        cursor: {
            display: 'inline-block',
            width: '2px',
            height: '14px',
            backgroundColor: '#4f46e5',
            marginLeft: '4px',
            verticalAlign: 'middle',
        }
    };

    return (
        <div style={isAssistant ? messageStyles.aiRow : messageStyles.userRow}>
            <div style={isAssistant ? messageStyles.aiBubble : messageStyles.userBubble}>
                {displayedText}
                {/* Toon de cursor alleen als de AI nog aan het 'typen' is */}
                {isAssistant && !isDone && (
                    <span style={messageStyles.cursor} className="blink" />
                )}
            </div>
            <style>
                {`
                    .blink { animation: blink-anim 0.8s infinite; }
                    @keyframes blink-anim { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
                `}
            </style>
        </div>
    );
};

export default Message;