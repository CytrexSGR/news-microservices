"""
Health Monitoring API
Provides real-time container health and resource metrics via Docker API
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime
import json
import logging
from pathlib import Path

from app.services.docker_monitor import get_docker_monitor

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/containers")
async def get_container_health() -> List[Dict[str, Any]]:
    """
    Get health status and resource metrics for all containers
    Fetches real-time data directly from Docker API

    Returns:
        List of container info with status, health, and resource usage
        Empty list if Docker is unavailable (graceful degradation)
    """
    try:
        monitor = get_docker_monitor()
        containers = await monitor.get_containers()
        return containers

    except Exception as e:
        # Log error but don't expose internal details
        logger.error(f"Error fetching container health: {e}")
        # Graceful degradation: return empty list
        return []


@router.get("/alerts")
async def get_alerts(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get recent alerts from monitoring log

    DEPRECATED: This endpoint reads from external monitoring script logs.
    Will be replaced with Docker event-based alerting in future version.

    Args:
        limit: Maximum number of alerts to return

    Returns:
        List of recent alerts
        Empty list if log file doesn't exist
    """
    logger.warning("DEPRECATED: /alerts endpoint uses legacy monitoring script")
    log_file = Path("/host_tmp/docker-monitor-alerts.log")

    if not log_file.exists():
        return []

    try:
        alerts = []
        with open(log_file, 'r') as f:
            lines = f.readlines()

        # Parse alert lines (format: [timestamp] ALERT [severity] service: message)
        for line in reversed(lines[-limit:]):
            if 'ALERT' in line:
                try:
                    # Parse: [2025-11-05 20:50:57 UTC] ALERT [WARNING] neo4j: HIGH_MEMORY: 9.84% (threshold: 10.0%)
                    parts = line.strip().split('] ')
                    timestamp = parts[0].strip('[')
                    alert_part = parts[1]
                    severity = alert_part.split('[')[1].split(']')[0]
                    service_message = parts[2]
                    service, message = service_message.split(':', 1)

                    alerts.append({
                        "timestamp": timestamp,
                        "severity": severity,
                        "service": service.strip(),
                        "message": message.strip()
                    })
                except Exception:
                    # Skip malformed lines
                    continue

        return alerts

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading alerts: {str(e)}")


@router.get("/summary")
async def get_health_summary(include_containers: bool = False) -> Dict[str, Any]:
    """
    Get overall system health summary

    OPTIMIZATION: Use cached data from docker_monitor (30s cache)
    instead of fetching fresh stats (saves 60+ seconds on 40 containers)

    Args:
        include_containers: Include full container list in response (default: False)

    Returns:
        Summary statistics
    """
    try:
        # Use cached data from monitor (shared with /containers endpoint)
        monitor = get_docker_monitor()
        containers = await monitor.get_containers()

        total = len(containers)

        # Count by health status
        healthy = sum(1 for c in containers if c.get('status') == 'running' and c.get('health') == 'healthy')
        unhealthy = sum(1 for c in containers if c.get('status') == 'running' and c.get('health') == 'unhealthy')
        no_healthcheck = sum(1 for c in containers if c.get('status') == 'running' and c.get('health') is None)

        # Count by status
        running = sum(1 for c in containers if c.get('status') == 'running')
        stopped = sum(1 for c in containers if c.get('status') in ('exited', 'created', 'dead'))

        # Calculate average resource usage (only for running containers)
        running_containers = [c for c in containers if c.get('status') == 'running']
        avg_cpu = sum(c['cpu_percent'] for c in running_containers) / len(running_containers) if running_containers else 0
        avg_memory = sum(c['memory_percent'] for c in running_containers) / len(running_containers) if running_containers else 0
        total_pids = sum(c['pids'] for c in running_containers)

        # Get recent alerts count
        alerts = await get_alerts(limit=100)
        critical_alerts = sum(1 for a in alerts if a['severity'] == 'CRITICAL')
        warning_alerts = sum(1 for a in alerts if a['severity'] == 'WARNING')

        summary = {
            "total_containers": total,
            "healthy": healthy,
            "unhealthy": unhealthy,
            "no_healthcheck": no_healthcheck,
            "running": running,
            "stopped": stopped,
            "avg_cpu_percent": round(avg_cpu, 2),
            "avg_memory_percent": round(avg_memory, 2),
            "total_pids": total_pids,
            "recent_critical_alerts": critical_alerts,
            "recent_warning_alerts": warning_alerts,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Optionally include full container list
        if include_containers:
            summary["containers"] = containers

        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")
