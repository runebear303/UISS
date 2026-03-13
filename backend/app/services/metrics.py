from app.services.ai_metrics import AIMetrics


# ===============================
# AI METRICS API
# ===============================

def get_ai_metrics():
    """
    Returns AI performance statistics
    used in the admin monitoring dashboard.
    """

    return {
        "ai_metrics": AIMetrics.get_metrics()
    }