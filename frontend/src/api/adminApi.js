import { apiRequest } from "./client"

export function getMetrics() {
    return apiRequest("/admin/ai-metrics")
}

export function getLogs() {
    return apiRequest("/admin/logs")
}

export function getSystemStats() {
    return apiRequest("/admin/monitor")
}
