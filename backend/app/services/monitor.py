import psutil
import os
from datetime import datetime, UTC
from app.services.logger import log_system_alert


# =========================
# HEALTH THRESHOLDS
# =========================

CPU_THRESHOLD = 90
RAM_THRESHOLD = 90
DISK_THRESHOLD = 90


# =========================
# SYSTEM STATS
# =========================

def system_stats():
    try:
        root_path = os.path.abspath(os.sep)

        cpu = psutil.cpu_percent(interval=0.5)
        vm = psutil.virtual_memory()
        disk = psutil.disk_usage(root_path)

        uptime = int(datetime.now().timestamp() - psutil.boot_time())

        alerts = []

        # CPU ALERT
        if cpu > CPU_THRESHOLD:
            alerts.append("CPU usage critical")
            log_system_alert("cpu_percent", cpu)

        # RAM ALERT
        if vm.percent > RAM_THRESHOLD:
            alerts.append("RAM usage critical")
            log_system_alert("ram_percent", vm.percent)

        # DISK ALERT
        if disk.percent > DISK_THRESHOLD:
            alerts.append("Disk usage critical")
            log_system_alert("disk_percent", disk.percent)

        return {
            "system": {
                "cpu_percent": cpu,
                "ram_percent": vm.percent,
                "ram_used_mb": round(vm.used / (1024 ** 2), 2),
                "ram_total_mb": round(vm.total / (1024 ** 2), 2),
                "disk_percent": disk.percent,
                "uptime_seconds": uptime,
                "timestamp": datetime.now(UTC).isoformat()
            },
            "health": {
                "status": "critical" if alerts else "healthy",
                "alerts": alerts
            }
        }

    except Exception as e:
        return {
            "system": None,
            "health": {
                "status": "error",
                "alerts": [str(e)]
            }
        }