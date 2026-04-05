#!/usr/bin/env python3
"""
Backfill pgvector centroids for existing article_clusters.

Converts centroid_vector (JSONB) to centroid_vec (pgvector) for all
active clusters that don't have a pgvector centroid yet. Also calculates
and sets initial CSAI (Cluster Stability Assessment Index) scores.

This script is idempotent - safe to run multiple times.

Usage:
    # From within the container:
    docker exec -it clustering-service python /app/scripts/backfill_pgvector_centroids.py

    # Or with dry-run (no changes):
    docker exec -it clustering-service python /app/scripts/backfill_pgvector_centroids.py --dry-run

    # With custom batch size:
    docker exec -it clustering-service python /app/scripts/backfill_pgvector_centroids.py --batch-size 50

    # Process specific number of clusters (for testing):
    docker exec -it clustering-service python /app/scripts/backfill_pgvector_centroids.py --limit 10

Environment Variables:
    DATABASE_URL: PostgreSQL connection string (default: localhost)
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default database URL (inside container)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/news_mcp"
)

# Batch size for processing
DEFAULT_BATCH_SIZE = 100

# CSAI configuration (from ClusteringService)
CSAI_STABLE_THRESHOLD = 0.35


def calculate_csai(centroid: List[float]) -> float:
    """
    Calculate CSAI using Matryoshka slice correlation.

    Measures semantic consistency across embedding dimensions.
    OpenAI text-embedding-3-small has hierarchical information:
    - First 256D: Core semantics
    - First 512D: More detail
    - Full 1536D: Maximum detail

    A stable cluster should have consistent semantics at all scales.

    Args:
        centroid: 1536D embedding vector

    Returns:
        CSAI score between 0 and 1. >= 0.35 indicates stable cluster.
    """
    if len(centroid) < 512:
        # Can't compute CSAI for small embeddings
        return 1.0

    # Extract Matryoshka slices
    slice_256 = np.array(centroid[:256])
    slice_512 = np.array(centroid[:512])
    full = np.array(centroid)

    # Normalize slices (with epsilon to avoid division by zero)
    norm_256 = np.linalg.norm(slice_256)
    norm_512 = np.linalg.norm(slice_512)
    norm_full = np.linalg.norm(full)

    # Handle zero vectors gracefully
    if norm_256 == 0 or norm_512 == 0 or norm_full == 0:
        return 0.0

    slice_256 = slice_256 / norm_256
    slice_512 = slice_512 / norm_512
    full = full / norm_full

    # Compare 256D slice to first 256D of 512D slice (normalized)
    slice_512_256 = slice_512[:256]
    norm_512_256 = np.linalg.norm(slice_512_256)
    if norm_512_256 > 0:
        slice_512_256 = slice_512_256 / norm_512_256
    sim_256_512 = float(np.dot(slice_256, slice_512_256))

    # Compare 512D slice to first 512D of full embedding (normalized)
    full_512 = full[:512]
    norm_full_512 = np.linalg.norm(full_512)
    if norm_full_512 > 0:
        full_512 = full_512 / norm_full_512
    sim_512_full = float(np.dot(slice_512, full_512))

    # CSAI = average correlation across slices
    return (sim_256_512 + sim_512_full) / 2


def get_csai_status(csai_score: float) -> str:
    """
    Determine CSAI status based on score.

    Args:
        csai_score: CSAI score from calculate_csai()

    Returns:
        'stable' if >= threshold, 'unstable' otherwise
    """
    return 'stable' if csai_score >= CSAI_STABLE_THRESHOLD else 'unstable'


def parse_database_url(url: str) -> Dict[str, Any]:
    """
    Parse DATABASE_URL into asyncpg connection parameters.

    Handles formats like:
    - postgresql://user:pass@host:port/dbname
    - postgres://user:pass@host:port/dbname
    - postgresql+asyncpg://user:pass@host:port/dbname
    - postgresql://user:pass@host:port/dbname?sslmode=require
    """
    # Remove postgresql+asyncpg://, postgresql://, or postgres://
    url = url.replace("postgresql+asyncpg://", "").replace("postgresql://", "").replace("postgres://", "")

    # Split by @ to get auth and host parts
    if "@" in url:
        auth_part, host_part = url.split("@", 1)
    else:
        auth_part = ""
        host_part = url

    # Parse auth
    if ":" in auth_part:
        user, password = auth_part.split(":", 1)
    else:
        user = auth_part
        password = ""

    # Parse host and database
    if "/" in host_part:
        host_port, db_part = host_part.split("/", 1)
    else:
        host_port = host_part
        db_part = "postgres"

    # Parse host and port
    if ":" in host_port:
        host, port_str = host_port.split(":", 1)
        port = int(port_str)
    else:
        host = host_port
        port = 5432

    # Parse database name (remove query params)
    database = db_part.split("?")[0] if "?" in db_part else db_part

    return {
        "user": user,
        "password": password,
        "host": host,
        "port": port,
        "database": database,
    }


async def get_clusters_to_backfill(
    conn: asyncpg.Connection,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get clusters that need backfill.

    Finds clusters where:
    - centroid_vector (JSONB) is NOT NULL
    - centroid_vec (pgvector) IS NULL
    - status is 'active'

    Args:
        conn: Database connection
        limit: Optional limit on number of clusters to return

    Returns:
        List of dicts with cluster id and centroid_vector
    """
    query = """
        SELECT id, centroid_vector, article_count
        FROM article_clusters
        WHERE centroid_vec IS NULL
          AND centroid_vector IS NOT NULL
          AND status = 'active'
        ORDER BY last_updated_at DESC
    """

    if limit:
        query += f" LIMIT {limit}"

    rows = await conn.fetch(query)

    return [
        {
            "id": row["id"],
            "centroid_vector": row["centroid_vector"],
            "article_count": row["article_count"],
        }
        for row in rows
    ]


async def update_cluster_pgvector(
    conn: asyncpg.Connection,
    cluster_id: str,
    centroid_vec: str,
    csai_score: float,
    csai_status: str,
    dry_run: bool = False,
) -> bool:
    """
    Update a cluster with pgvector centroid and CSAI values.

    Args:
        conn: Database connection
        cluster_id: UUID of the cluster
        centroid_vec: pgvector string format "[0.1,0.2,...]"
        csai_score: Calculated CSAI score
        csai_status: 'stable' or 'unstable'
        dry_run: If True, don't actually update

    Returns:
        True if updated, False otherwise
    """
    if dry_run:
        logger.debug(f"[DRY-RUN] Would update cluster {cluster_id}")
        return True

    try:
        await conn.execute(
            """
            UPDATE article_clusters
            SET centroid_vec = $1::vector,
                csai_score = $2,
                csai_status = $3,
                csai_checked_at = NOW()
            WHERE id = $4
            """,
            centroid_vec,
            csai_score,
            csai_status,
            cluster_id,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to update cluster {cluster_id}: {e}")
        return False


def parse_centroid(centroid_raw: Any) -> Optional[List[float]]:
    """
    Parse centroid from various formats (JSONB can be dict, list, or string).

    Args:
        centroid_raw: Raw centroid data from database

    Returns:
        List of floats, or None if parsing fails
    """
    try:
        if isinstance(centroid_raw, list):
            return [float(x) for x in centroid_raw]
        elif isinstance(centroid_raw, str):
            parsed = json.loads(centroid_raw)
            if isinstance(parsed, list):
                return [float(x) for x in parsed]
        elif isinstance(centroid_raw, dict):
            # Shouldn't happen for proper embeddings, but handle it
            logger.warning("Centroid is a dict, expected list")
            return None
        return None
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.error(f"Failed to parse centroid: {e}")
        return None


async def backfill(
    batch_size: int = DEFAULT_BATCH_SIZE,
    dry_run: bool = False,
    limit: Optional[int] = None,
) -> Dict[str, int]:
    """
    Main backfill function.

    Args:
        batch_size: Number of clusters to process per batch
        dry_run: If True, don't actually update
        limit: Optional limit on total clusters to process

    Returns:
        Dict with statistics: total, processed, skipped, errors
    """
    stats = {
        "total": 0,
        "processed": 0,
        "skipped": 0,
        "errors": 0,
        "stable": 0,
        "unstable": 0,
    }

    # Parse database URL
    db_params = parse_database_url(DATABASE_URL)
    logger.info(f"Connecting to {db_params['host']}:{db_params['port']}/{db_params['database']}")

    try:
        conn = await asyncpg.connect(**db_params)
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return stats

    try:
        # Check if pgvector extension and column exist
        try:
            result = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
            )
            if not result:
                logger.error("pgvector extension not installed. Run migration first.")
                return stats
        except Exception as e:
            logger.error(f"Failed to check pgvector extension: {e}")
            return stats

        # Check if centroid_vec column exists
        try:
            await conn.fetchval(
                "SELECT centroid_vec FROM article_clusters LIMIT 0"
            )
        except Exception as e:
            if "column" in str(e).lower() and "centroid_vec" in str(e).lower():
                logger.error("centroid_vec column not found. Run migration first.")
                return stats
            raise

        # Get clusters needing backfill
        logger.info("Finding clusters to backfill...")
        clusters = await get_clusters_to_backfill(conn, limit)
        stats["total"] = len(clusters)

        if stats["total"] == 0:
            logger.info("No clusters need backfill - all active clusters have pgvector centroids")
            return stats

        logger.info(f"Found {stats['total']} clusters to backfill")
        if dry_run:
            logger.info("[DRY-RUN] No changes will be made")

        # Process in batches
        for i in range(0, len(clusters), batch_size):
            batch = clusters[i:i + batch_size]
            batch_start = datetime.now()

            for cluster in batch:
                cluster_id = cluster["id"]
                centroid_raw = cluster["centroid_vector"]
                article_count = cluster["article_count"]

                # Parse centroid
                centroid = parse_centroid(centroid_raw)
                if centroid is None:
                    logger.warning(f"Skipping cluster {cluster_id}: failed to parse centroid")
                    stats["skipped"] += 1
                    continue

                # Validate centroid dimension
                if len(centroid) != 1536:
                    logger.warning(
                        f"Skipping cluster {cluster_id}: wrong dimension "
                        f"({len(centroid)} instead of 1536)"
                    )
                    stats["skipped"] += 1
                    continue

                # Calculate CSAI
                csai_score = calculate_csai(centroid)
                csai_status = get_csai_status(csai_score)

                # Format as pgvector string
                centroid_vec = "[" + ",".join(str(f) for f in centroid) + "]"

                # Update cluster
                success = await update_cluster_pgvector(
                    conn,
                    cluster_id,
                    centroid_vec,
                    csai_score,
                    csai_status,
                    dry_run=dry_run,
                )

                if success:
                    stats["processed"] += 1
                    if csai_status == "stable":
                        stats["stable"] += 1
                    else:
                        stats["unstable"] += 1
                else:
                    stats["errors"] += 1

            batch_duration = (datetime.now() - batch_start).total_seconds()
            progress = min(i + batch_size, len(clusters))
            logger.info(
                f"Processed {progress}/{stats['total']} clusters "
                f"({batch_duration:.2f}s for batch of {len(batch)})"
            )

        # Final summary
        logger.info("=" * 50)
        logger.info("Backfill complete!")
        logger.info(f"  Total clusters:    {stats['total']}")
        logger.info(f"  Processed:         {stats['processed']}")
        logger.info(f"  Skipped:           {stats['skipped']}")
        logger.info(f"  Errors:            {stats['errors']}")
        logger.info(f"  CSAI stable:       {stats['stable']}")
        logger.info(f"  CSAI unstable:     {stats['unstable']}")
        if dry_run:
            logger.info("[DRY-RUN] No changes were made")

    finally:
        await conn.close()

    return stats


async def verify_backfill(conn: asyncpg.Connection) -> Dict[str, int]:
    """
    Verify backfill results.

    Returns:
        Dict with verification statistics
    """
    result = await conn.fetchrow("""
        SELECT
            COUNT(*) FILTER (WHERE centroid_vec IS NOT NULL) as with_pgvector,
            COUNT(*) FILTER (WHERE centroid_vec IS NULL AND centroid_vector IS NOT NULL) as without_pgvector,
            COUNT(*) FILTER (WHERE csai_status = 'stable') as stable,
            COUNT(*) FILTER (WHERE csai_status = 'unstable') as unstable,
            COUNT(*) FILTER (WHERE csai_status = 'pending' OR csai_status IS NULL) as pending,
            COUNT(*) as total
        FROM article_clusters
        WHERE status = 'active'
    """)

    return dict(result)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Backfill pgvector centroids for article_clusters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually update, just show what would be done",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Number of clusters per batch (default: {DEFAULT_BATCH_SIZE})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit total clusters to process (for testing)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify current state, don't backfill",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.verify_only:
        # Just run verification
        async def verify():
            db_params = parse_database_url(DATABASE_URL)
            conn = await asyncpg.connect(**db_params)
            try:
                stats = await verify_backfill(conn)
                logger.info("Current backfill status:")
                logger.info(f"  With pgvector:      {stats['with_pgvector']}")
                logger.info(f"  Without pgvector:   {stats['without_pgvector']}")
                logger.info(f"  CSAI stable:        {stats['stable']}")
                logger.info(f"  CSAI unstable:      {stats['unstable']}")
                logger.info(f"  CSAI pending:       {stats['pending']}")
                logger.info(f"  Total active:       {stats['total']}")

                if stats['without_pgvector'] == 0:
                    logger.info("All active clusters have pgvector centroids!")
                    return 0
                else:
                    logger.warning(
                        f"{stats['without_pgvector']} clusters still need backfill"
                    )
                    return 1
            finally:
                await conn.close()

        sys.exit(asyncio.run(verify()))

    # Run backfill
    stats = asyncio.run(backfill(
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        limit=args.limit,
    ))

    # Exit with error if there were errors
    if stats["errors"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
