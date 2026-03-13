import { apiRequest } from "./client"

export async function login(username, password) {

    return apiRequest("/login", {
        method: "POST",
        body: JSON.stringify({ username, password })
    })
}