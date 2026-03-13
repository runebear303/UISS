import { useEffect, useState } from "react"
import { getMetrics } from "../../api/adminApi"
import "./MetricsDashboard.css"

export default function MetricsDashboard({ token }) {

    const [metrics, setMetrics] = useState(null)
    const [lastUpdate, setLastUpdate] = useState(null)

    useEffect(() => {

        if (!token) return

        async function loadMetrics() {

            try {

                const data = await getMetrics(token)

                setMetrics(data)
                setLastUpdate(new Date().toLocaleTimeString())

            } catch (err) {

                console.error("Failed to load metrics", err)

            }

        }

        loadMetrics()

        const interval = setInterval(loadMetrics, 10000)

        return () => clearInterval(interval)

    }, [token])



    if (!metrics) return <div className="metrics-loading">Loading metrics...</div>


    return (

        <div className="metrics-dashboard">

            <div className="metrics-header">

                <h2>AI System Metrics</h2>

                <div className="live-indicator">
                    ● Live
                    <span>Updated {lastUpdate}</span>
                </div>

            </div>


            <div className="metrics-grid">

                <div className="metric-card">
                    <h3>Total Queries</h3>
                    <p>{metrics.queries}</p>
                </div>

                <div className="metric-card">
                    <h3>Errors</h3>
                    <p>{metrics.errors}</p>
                </div>

                <div className="metric-card">
                    <h3>Documents Retrieved</h3>
                    <p>{metrics.documents_retrieved}</p>
                </div>

                <div className="metric-card">
                    <h3>Avg Response Time</h3>
                    <p>{metrics.avg_response_time}s</p>
                </div>

            </div>

        </div>

    )
}