import { apiRequest } from "./client"

export function sendChatMessage(question) {

    return apiRequest("/chat", {
        method: "POST",
        body: JSON.stringify({ question })
    })
}