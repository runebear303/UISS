import { useState } from "react"
import { streamChat } from "../api/chatStream"

export function useChat() {

    const [messages, setMessages] = useState([])
    const [loading, setLoading] = useState(false)

    async function sendMessage(question) {

        const userMessage = { role: "user", content: question }

        setMessages(prev => [...prev, userMessage])

        let aiMessage = { role: "ai", content: "" }

        setMessages(prev => [...prev, aiMessage])

        setLoading(true)

        await streamChat(question, token => {

            aiMessage.content += token

            setMessages(prev => {

                const updated = [...prev]
                updated[updated.length - 1] = { ...aiMessage }

                return updated
            })
        })

        setLoading(false)
    }

    return {
        messages,
        sendMessage,
        loading
    }
}