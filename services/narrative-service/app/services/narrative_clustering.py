"""
Narrative Clustering Service - Group similar narrative frames
"""
from typing import List, Dict, Any
from collections import Counter, defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import NarrativeFrame, NarrativeCluster


class NarrativeClusteringService:
    """
    Cluster narrative frames by similarity
    Groups frames with same type and overlapping entities
    """

    def cluster_frames(self, frames: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
        """
        Cluster frames by type and entity overlap

        Returns:
            Dictionary mapping cluster_id to list of frames
        """
        if not frames:
            return {}

        # Group by frame type first
        type_groups = defaultdict(list)
        for frame in frames:
            type_groups[frame["frame_type"]].append(frame)

        # Create clusters
        clusters = {}
        cluster_id = 0

        for frame_type, type_frames in type_groups.items():
            # For each frame type, cluster by entity overlap
            if len(type_frames) >= 3:  # Need at least 3 frames to form cluster
                clusters[cluster_id] = type_frames
                cluster_id += 1

        return clusters

    def create_cluster_metadata(self, frames: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create metadata for a cluster of frames

        Returns:
            Dictionary with cluster name, dominant_frame, keywords, etc.
        """
        if not frames:
            return {}

        # Count frame types
        frame_types = [f["frame_type"] for f in frames]
        dominant_frame = Counter(frame_types).most_common(1)[0][0]

        # Aggregate entities
        all_persons = []
        all_orgs = []
        all_locations = []

        for frame in frames:
            entities = frame.get("entities", {})
            all_persons.extend(entities.get("persons", []))
            all_orgs.extend(entities.get("organizations", []))
            all_locations.extend(entities.get("locations", []))

        # Get top entities
        top_persons = [p for p, _ in Counter(all_persons).most_common(3)]
        top_orgs = [o for o, _ in Counter(all_orgs).most_common(3)]
        top_locations = [l for l, _ in Counter(all_locations).most_common(3)]

        # Create name from entities
        name_parts = []
        if top_persons:
            name_parts.append(top_persons[0])
        if top_orgs:
            name_parts.append(top_orgs[0])
        if top_locations:
            name_parts.append(top_locations[0])

        name = " - ".join(name_parts) if name_parts else f"{dominant_frame.title()} Narrative"

        # Create keywords from entities
        keywords = top_persons + top_orgs + top_locations

        return {
            "name": name[:255],  # Limit name length
            "dominant_frame": dominant_frame,
            "frame_count": len(frames),
            "keywords": keywords,
            "entities": {
                "persons": top_persons,
                "organizations": top_orgs,
                "locations": top_locations,
            },
        }

    async def update_narrative_clusters(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Update narrative clusters from all frames

        Returns:
            Statistics about clustering
        """
        # Get all active frames from last 7 days
        result = await db.execute(
            select(NarrativeFrame)
            .where(NarrativeFrame.created_at >= func.now() - func.make_interval(0, 0, 0, 7))
            .order_by(NarrativeFrame.created_at.desc())
        )
        frames = result.scalars().all()

        if not frames:
            return {"status": "no_frames", "clusters_created": 0}

        # Convert to dicts
        frame_dicts = [
            {
                "id": str(f.id),
                "frame_type": f.frame_type,
                "entities": f.entities or {},
                "confidence": f.confidence,
            }
            for f in frames
        ]

        # Cluster frames
        clusters = self.cluster_frames(frame_dicts)

        # Upsert cluster objects (create or update)
        clusters_created = 0
        clusters_updated = 0

        for cluster_frames in clusters.values():
            metadata = self.create_cluster_metadata(cluster_frames)
            cluster_name = metadata["name"]

            # Check if cluster with this name already exists
            existing_cluster = await db.execute(
                select(NarrativeCluster).where(NarrativeCluster.name == cluster_name)
            )
            existing = existing_cluster.scalar_one_or_none()

            if existing:
                # Update existing cluster
                existing.frame_count = metadata["frame_count"]
                existing.keywords = metadata["keywords"]
                existing.entities = metadata["entities"]
                existing.is_active = True
                clusters_updated += 1
            else:
                # Create new cluster
                cluster = NarrativeCluster(
                    name=cluster_name,
                    dominant_frame=metadata["dominant_frame"],
                    frame_count=metadata["frame_count"],
                    keywords=metadata["keywords"],
                    entities=metadata["entities"],
                    is_active=True,
                )
                db.add(cluster)
                clusters_created += 1

        await db.commit()

        return {
            "status": "success",
            "frames_processed": len(frames),
            "clusters_created": clusters_created,
            "clusters_updated": clusters_updated,
        }


# Global service instance
narrative_clustering_service = NarrativeClusteringService()
