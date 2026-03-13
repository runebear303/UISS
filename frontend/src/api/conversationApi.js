import { apiRequest } from "./client"

export function getConversations() {
    return apiRequest("/conversations")
}

export function createConversation(title) {
    return apiRequest("/conversations", {
        method: "POST",
        body: JSON.stringify({ title })
    })
}

export function getMessages(id) {
    return apiRequest(`/conversations/${id}/messages`)
}