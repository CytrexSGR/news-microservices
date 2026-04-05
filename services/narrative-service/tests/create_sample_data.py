"""
Create sample narrative data for testing

Run from narrative-service root:
    docker exec news-narrative-service python tests/create_sample_data.py
"""
import asyncio
import uuid
from datetime import datetime, timedelta
import random

from app.database import AsyncSessionLocal
from app.models.narrative_frame import NarrativeFrame
from app.models.bias_analysis import BiasAnalysis
from app.models.narrative_cluster import NarrativeCluster


FRAME_TYPES = ['victim', 'hero', 'threat', 'solution', 'conflict', 'economic']
SOURCES = ['CNN', 'Fox News', 'BBC', 'Reuters', 'MSNBC', 'NYTimes', 'WSJ']
PERSPECTIVES = ['pro', 'con', 'neutral']
BIAS_LABELS = ['left', 'center-left', 'center', 'center-right', 'right']

SAMPLE_TEXTS = [
    "The government announced new economic policies to address rising inflation",
    "Citizens protest against controversial legislation in the capital",
    "Emergency response teams rescue dozens after natural disaster",
    "Tech giant unveils innovative solution to climate challenges",
    "International tensions escalate over disputed territories",
    "Healthcare workers demand better working conditions and pay",
    "Local community rallies to support struggling small businesses",
    "Scientists warn of potential environmental catastrophe",
]


async def create_sample_frames(session, count=50):
    """Create sample narrative frames"""
    frames = []
    base_time = datetime.utcnow() - timedelta(days=7)

    for i in range(count):
        event_id = str(uuid.uuid4())
        frame_type = random.choice(FRAME_TYPES)
        confidence = random.uniform(0.6, 0.95)
        text_excerpt = random.choice(SAMPLE_TEXTS)

        # Generate entities
        entities = {}
        if random.random() > 0.5:
            entities['PERSON'] = [
                random.choice(['Joe Biden', 'Xi Jinping', 'Vladimir Putin', 'Angela Merkel'])
            ]
        if random.random() > 0.5:
            entities['ORG'] = [
                random.choice(['United Nations', 'World Bank', 'NATO', 'European Union'])
            ]
        if random.random() > 0.5:
            entities['GPE'] = [
                random.choice(['United States', 'China', 'Russia', 'Germany', 'France'])
            ]

        # Create frame
        frame = NarrativeFrame(
            id=uuid.uuid4(),
            event_id=uuid.UUID(event_id),
            frame_type=frame_type,
            confidence=confidence,
            text_excerpt=text_excerpt,
            entities=entities if entities else None,
            frame_metadata={'sample': True, 'batch': 1},
            created_at=base_time + timedelta(hours=i * 3),
        )
        frames.append(frame)

    session.add_all(frames)
    await session.commit()
    print(f"✅ Created {count} narrative frames")
    return frames


async def create_sample_bias_analyses(session, count=30):
    """Create sample bias analyses"""
    analyses = []
    base_time = datetime.utcnow() - timedelta(days=7)

    for i in range(count):
        event_id = str(uuid.uuid4())
        source = random.choice(SOURCES)

        # Assign bias score based on source (simulate real bias)
        if source in ['CNN', 'MSNBC']:
            bias_score = random.uniform(-0.8, -0.2)
            bias_label = random.choice(['left', 'center-left'])
        elif source in ['Fox News', 'WSJ']:
            bias_score = random.uniform(0.2, 0.8)
            bias_label = random.choice(['center-right', 'right'])
        else:  # BBC, Reuters, NYTimes
            bias_score = random.uniform(-0.2, 0.2)
            bias_label = 'center'

        sentiment = random.uniform(-0.7, 0.7)
        perspective = random.choice(PERSPECTIVES)

        # Language indicators
        language_indicators = {
            'emotional_words': random.randint(2, 10),
            'loaded_language': random.randint(0, 5),
            'hyperbole_count': random.randint(0, 3),
        }

        analysis = BiasAnalysis(
            id=uuid.uuid4(),
            event_id=uuid.UUID(event_id),
            source=source,
            bias_score=bias_score,
            bias_label=bias_label,
            sentiment=sentiment,
            language_indicators=language_indicators,
            perspective=perspective,
            created_at=base_time + timedelta(hours=i * 5),
        )
        analyses.append(analysis)

    session.add_all(analyses)
    await session.commit()
    print(f"✅ Created {count} bias analyses")
    return analyses


async def create_sample_clusters(session, frames):
    """Create sample narrative clusters"""
    clusters = []

    # Group frames by type
    frame_groups = {}
    for frame in frames:
        if frame.frame_type not in frame_groups:
            frame_groups[frame.frame_type] = []
        frame_groups[frame.frame_type].append(frame)

    # Create clusters
    for frame_type, group_frames in frame_groups.items():
        if len(group_frames) >= 3:
            cluster = NarrativeCluster(
                id=uuid.uuid4(),
                name=f"{frame_type.capitalize()} Narrative Cluster",
                dominant_frame=frame_type,
                frame_count=len(group_frames),
                bias_score=random.uniform(-0.5, 0.5),
                keywords=[f"keyword_{i}" for i in range(3)],
                entities={'PERSON': ['Sample Person'], 'ORG': ['Sample Org']},
                sentiment=random.uniform(-0.3, 0.3),
                perspectives={'pro': 30, 'con': 20, 'neutral': 50},
                is_active=True,
            )
            clusters.append(cluster)

    session.add_all(clusters)
    await session.commit()
    print(f"✅ Created {len(clusters)} narrative clusters")
    return clusters


async def main():
    """Main test data creation"""
    print("🚀 Creating sample narrative data...")
    print()

    async with AsyncSessionLocal() as session:
        # Create frames
        frames = await create_sample_frames(session, count=50)

        # Create bias analyses
        analyses = await create_sample_bias_analyses(session, count=30)

        # Create clusters
        clusters = await create_sample_clusters(session, frames)

        print()
        print("✅ Sample data created successfully!")
        print(f"   - {len(frames)} narrative frames")
        print(f"   - {len(analyses)} bias analyses")
        print(f"   - {len(clusters)} narrative clusters")
        print()
        print("🔗 Test endpoints:")
        print("   GET  http://localhost:8119/api/v1/narrative/overview?days=7")
        print("   GET  http://localhost:8119/api/v1/narrative/frames?per_page=20")
        print("   GET  http://localhost:8119/api/v1/narrative/clusters")
        print("   GET  http://localhost:8119/api/v1/narrative/bias?days=7")
        print()
        print("🌐 Frontend:")
        print("   http://localhost:3000/narrative")


if __name__ == "__main__":
    asyncio.run(main())
