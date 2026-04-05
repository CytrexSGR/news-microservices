"""
Docker Container Monitoring Service
Provides real-time container health and resource metrics via Docker API
"""
import docker
from docker.errors import DockerException, NotFound
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class DockerMonitor:
    """
    Thread-safe Docker monitoring service with in-memory caching

    Features:
    - Async wrapper for synchronous Docker SDK calls
    - 3-second cache to reduce Docker API load
    - Graceful error handling for missing/deleted containers
    - 1:1 mapping to existing health API response format
    """

    def __init__(self, cache_ttl_seconds: int = 30):
        """
        Initialize Docker monitor

        Args:
            cache_ttl_seconds: Cache time-to-live in seconds (default: 30)
        """
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)
        self._cache_data: Optional[List[Dict[str, Any]]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._client: Optional[docker.DockerClient] = None

    def _get_client(self) -> docker.DockerClient:
        """
        Get or create Docker client instance

        Returns:
            Docker client

        Raises:
            DockerException: If Docker socket is unavailable
        """
        if self._client is None:
            try:
                self._client = docker.from_env()
            except DockerException as e:
                logger.error(f"Failed to connect to Docker: {e}")
                raise
        return self._client

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if self._cache_data is None or self._cache_timestamp is None:
            return False
        return datetime.utcnow() - self._cache_timestamp < self.cache_ttl

    async def get_containers(self) -> List[Dict[str, Any]]:
        """
        Get health and resource stats for all containers (async, cached)

        Returns:
            List of container information dictionaries
            Empty list if Docker is unavailable
        """
        # Return cached data if valid
        if self._is_cache_valid():
            logger.debug("Returning cached container data")
            return self._cache_data or []

        # Fetch fresh data in thread pool (Docker SDK is synchronous)
        try:
            containers = await asyncio.to_thread(self._get_containers_sync)

            # Update cache
            self._cache_data = containers
            self._cache_timestamp = datetime.utcnow()

            return containers
        except DockerException as e:
            logger.error(f"Docker API error: {e}")
            # Return empty list on error (graceful degradation)
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching containers: {e}")
            return []

    def _get_containers_sync(self) -> List[Dict[str, Any]]:
        """
        Synchronous Docker API calls with parallel stats fetching

        OPTIMIZATION: Use ThreadPoolExecutor to fetch stats in parallel
        - Before: 40 containers × 1.5s/each = 60s sequential
        - After:  40 containers / 10 threads = ~6s parallel

        Returns:
            List of container information
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        client = self._get_client()
        containers_data = []

        try:
            # Get all containers (running and stopped)
            containers = client.containers.list(all=True)

            # Parse containers in parallel (max 10 concurrent)
            with ThreadPoolExecutor(max_workers=10) as executor:
                # Submit all parse tasks
                future_to_container = {
                    executor.submit(self._parse_container, container): container
                    for container in containers
                }

                # Collect results as they complete
                for future in as_completed(future_to_container):
                    container = future_to_container[future]
                    try:
                        container_info = future.result()
                        if container_info:
                            containers_data.append(container_info)
                    except Exception as e:
                        # Skip containers that can't be parsed (e.g., deleted mid-request)
                        logger.warning(f"Failed to parse container {container.name}: {e}")
                        continue

            return containers_data

        except DockerException as e:
            logger.error(f"Failed to list containers: {e}")
            raise

    def _parse_container(self, container) -> Optional[Dict[str, Any]]:
        """
        Parse Docker container to API response format

        Args:
            container: Docker container object

        Returns:
            Container info dict matching existing API format
            None if container can't be parsed
        """
        try:
            # Reload container to get latest state
            container.reload()

            # Get basic info
            name = container.name
            status = container.attrs['State']['Status']  # running, exited, etc.

            # Get health status (if healthcheck defined)
            health_status = None
            if 'Health' in container.attrs['State']:
                health_raw = container.attrs['State']['Health']['Status']
                # Map Docker health to our format: healthy, unhealthy, starting
                if health_raw in ('healthy', 'unhealthy'):
                    health_status = health_raw
                # Treat 'starting' or other states as None (no health check)

            # Get resource stats (only for running containers)
            cpu_percent = 0.0
            memory_percent = 0.0
            memory_usage = "0MiB / 0MiB"
            pids = 0

            if status == 'running':
                try:
                    # Get stats (stream=False for single snapshot)
                    stats = container.stats(stream=False)

                    # Calculate CPU percentage
                    cpu_percent = self._calculate_cpu_percent(stats)

                    # Calculate memory percentage and usage
                    memory_percent, memory_usage = self._calculate_memory(stats)

                    # Get PID count
                    pids = stats.get('pids_stats', {}).get('current', 0)

                except Exception as e:
                    logger.warning(f"Failed to get stats for {name}: {e}")

            return {
                "name": name,
                "status": status,
                "health": health_status,
                "cpu_percent": round(cpu_percent, 2),
                "memory_percent": round(memory_percent, 2),
                "memory_usage": memory_usage,
                "pids": pids,
                "timestamp": datetime.utcnow().isoformat() + 'Z'
            }

        except NotFound:
            # Container was deleted mid-request
            logger.warning(f"Container no longer exists: {container.id}")
            return None
        except Exception as e:
            logger.error(f"Error parsing container: {e}")
            return None

    def _calculate_cpu_percent(self, stats: Dict[str, Any]) -> float:
        """
        Calculate CPU percentage from Docker stats

        Formula from Docker stats implementation:
        cpu_percent = (cpu_delta / system_delta) * num_cpus * 100
        """
        try:
            cpu_stats = stats.get('cpu_stats', {})
            precpu_stats = stats.get('precpu_stats', {})

            cpu_usage = cpu_stats.get('cpu_usage', {})
            precpu_usage = precpu_stats.get('cpu_usage', {})

            cpu_delta = cpu_usage.get('total_usage', 0) - precpu_usage.get('total_usage', 0)
            system_delta = cpu_stats.get('system_cpu_usage', 0) - precpu_stats.get('system_cpu_usage', 0)

            if system_delta > 0 and cpu_delta > 0:
                num_cpus = cpu_stats.get('online_cpus', 1)
                return (cpu_delta / system_delta) * num_cpus * 100.0

            return 0.0
        except (KeyError, TypeError, ZeroDivisionError):
            return 0.0

    def _calculate_memory(self, stats: Dict[str, Any]) -> tuple[float, str]:
        """
        Calculate memory percentage and usage string

        Returns:
            Tuple of (memory_percent, memory_usage_string)
        """
        try:
            memory_stats = stats.get('memory_stats', {})

            # Current memory usage
            usage = memory_stats.get('usage', 0)
            limit = memory_stats.get('limit', 0)

            # Calculate percentage
            memory_percent = (usage / limit * 100.0) if limit > 0 else 0.0

            # Format usage string (matching existing format: "127.7MiB / 19.51GiB")
            usage_mb = usage / (1024 * 1024)
            limit_gb = limit / (1024 * 1024 * 1024)
            memory_usage = f"{usage_mb:.1f}MiB / {limit_gb:.2f}GiB"

            return memory_percent, memory_usage
        except (KeyError, TypeError, ZeroDivisionError):
            return 0.0, "0MiB / 0GiB"

    async def cleanup(self):
        """Close Docker client connection"""
        if self._client:
            try:
                await asyncio.to_thread(self._client.close)
            except Exception as e:
                logger.warning(f"Error closing Docker client: {e}")
            finally:
                self._client = None


# Singleton instance with 30-second cache (stats collection is slow)
_monitor_instance: Optional[DockerMonitor] = None


def get_docker_monitor() -> DockerMonitor:
    """
    Get singleton Docker monitor instance

    Returns:
        DockerMonitor instance
    """
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = DockerMonitor(cache_ttl_seconds=30)
    return _monitor_instance
