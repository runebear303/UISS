const API = import.meta.env.VITE_API_URL || "http://localhost:8000/api"

export async function streamChat(question, onToken) {

    const response = await fetch(`${API}/chat/stream`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ question })
    })

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {

        const { done, value } = await reader.read()

        if (done) break

        const chunk = decoder.decode(value)

        onToken(chunk)
    }
}