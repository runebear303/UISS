import { useState } from "react"

export default function ChatInput({ onSend, loading }) {

    const [question, setQuestion] = useState("")

    function handleSubmit(e) {

        e.preventDefault()

        if (!question.trim()) return

        onSend(question)

        setQuestion("")
    }

    return (

        <form className="chat-input" onSubmit={handleSubmit}>

            <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a question..."
            />

            <button disabled={loading}>

                Send

            </button>

        </form>
    )
}