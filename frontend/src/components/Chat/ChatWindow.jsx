import Message from "./Message"
import TypingIndicator from "./TypingIndicator"
import { useEffect, useRef } from "react"

export default function ChatWindow({ messages, loading }) {

    const bottomRef = useRef(null)

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" })
    }, [messages, loading])

    return (

        <div className="chat-window">

            {messages.map((msg, index) => (

                <Message
                    key={index}
                    role={msg.role}
                    content={msg.content}
                />

            ))}

            {loading && <TypingIndicator />}

            <div ref={bottomRef}></div>

        </div>
    )
}
