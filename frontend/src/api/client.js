const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api"

export async function apiRequest(path, options = {}) {

    const token = localStorage.getItem("token")

    const headers = {
        "Content-Type": "application/json",
        ...(token && { Authorization: `Bearer ${token}` })
    }

    const response = await fetch(`${API_URL}${path}`, {
        headers,
        ...options
    })

    if (!response.ok) {
        throw new Error("API request failed")
    }

    return response.json()
}