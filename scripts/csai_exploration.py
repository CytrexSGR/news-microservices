#!/usr/bin/env python3
"""
CSAI Topic Discovery - Explorative Tests
=========================================

Testet den CSAI-Ansatz (Cluster Stability Assessment Index) mit Matryoshka-Embeddings.

Dokumentation: docs/research/2026-01-05-csai-topic-discovery.md

Usage:
    python scripts/csai_exploration.py --sample 5000
    python scripts/csai_exploration.py --sample 5000 --step clustering
"""

import argparse
import asyncio
import logging
import numpy as np
from datetime import datetime
from collections import Counter

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Database config
DATABASE_URL = "postgresql://news_user:your_db_password@localhost:5432/news_mcp"


async def load_embeddings(sample_size: int = 5000):
    """
    Step 1: Load embeddings from database.

    Returns dict with article_id, title, embedding, created_at
    """
    import asyncpg

    logger.info(f"Loading {sample_size} embeddings from database...")

    conn = await asyncpg.connect(DATABASE_URL)

    # Get sample with embeddings
    query = """
        SELECT
            aa.article_id,
            fi.title,
            aa.embedding::text as embedding_str,
            aa.created_at
        FROM article_analysis aa
        JOIN feed_items fi ON aa.article_id = fi.id
        WHERE aa.embedding IS NOT NULL
        ORDER BY RANDOM()
        LIMIT $1
    """

    rows = await conn.fetch(query, sample_size)
    await conn.close()

    # Parse embeddings
    articles = []
    for row in rows:
        # Parse "[0.1,0.2,...]" format
        emb_str = row['embedding_str'].strip('[]')
        embedding = [float(x) for x in emb_str.split(',')]

        articles.append({
            'article_id': str(row['article_id']),
            'title': row['title'],
            'embedding': embedding,
            'created_at': row['created_at']
        })

    logger.info(f"Loaded {len(articles)} articles with embeddings")
    logger.info(f"Embedding dimension: {len(articles[0]['embedding'])}")

    return articles


def create_matryoshka_slices(articles: list) -> dict:
    """
    Step 2: Create Matryoshka slices (256D, 512D, 1536D).

    text-embedding-3-small uses MRL - early dimensions contain core semantics.
    """
    logger.info("Creating Matryoshka slices...")

    slices = {
        '1536D': [],  # Full resolution
        '512D': [],   # Medium resolution
        '256D': [],   # Core semantics
    }

    for art in articles:
        emb = art['embedding']
        slices['1536D'].append(emb[:1536])
        slices['512D'].append(emb[:512])
        slices['256D'].append(emb[:256])

    # Convert to numpy
    for key in slices:
        slices[key] = np.array(slices[key])
        logger.info(f"  {key}: shape {slices[key].shape}")

    return slices


def create_tfidf_vectors(articles: list, max_features: int = 1000) -> np.ndarray:
    """
    Step 3: Create TF-IDF vectors from titles as "anchor in reality".
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    logger.info(f"Creating TF-IDF vectors (max_features={max_features})...")

    titles = [art['title'] or '' for art in articles]

    vectorizer = TfidfVectorizer(
        max_features=max_features,
        stop_words='english',
        ngram_range=(1, 2)
    )

    tfidf_matrix = vectorizer.fit_transform(titles)

    logger.info(f"  TF-IDF shape: {tfidf_matrix.shape}")

    return tfidf_matrix.toarray()


def reduce_dimensions(embeddings: np.ndarray, name: str, n_components: int = 10) -> np.ndarray:
    """
    Step 3.5: Reduce dimensions with UMAP before clustering.

    High-dimensional spaces suffer from "curse of dimensionality" -
    distances become less meaningful.
    """
    import umap

    logger.info(f"  Reducing {name} to {n_components}D with UMAP...")

    reducer = umap.UMAP(
        n_components=n_components,
        n_neighbors=15,
        min_dist=0.1,
        metric='cosine',
        random_state=42
    )

    reduced = reducer.fit_transform(embeddings)
    logger.info(f"    {name}: {embeddings.shape} → {reduced.shape}")

    return reduced


def cluster_embeddings(embeddings: np.ndarray, name: str, min_cluster_size: int = 15) -> np.ndarray:
    """
    Step 4: Cluster using HDBSCAN.

    Returns cluster labels (-1 = noise).
    """
    import hdbscan

    logger.info(f"Clustering {name}...")

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=5,
        metric='euclidean',
        cluster_selection_method='eom'
    )

    labels = clusterer.fit_predict(embeddings)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)

    logger.info(f"  {name}: {n_clusters} clusters, {n_noise} noise points ({n_noise/len(labels)*100:.1f}%)")

    return labels


def calculate_jaccard(labels_a: np.ndarray, labels_b: np.ndarray) -> float:
    """
    Calculate Jaccard similarity between two clusterings.

    Measures: How many document pairs are in the same cluster in both?
    """
    from sklearn.metrics import adjusted_rand_score

    # Use Adjusted Rand Index as proxy for cluster agreement
    # (Jaccard on cluster pairs is expensive for large N)
    ari = adjusted_rand_score(labels_a, labels_b)

    return ari


def calculate_csai(labels_dict: dict) -> dict:
    """
    Step 5: Calculate CSAI scores.

    Compares 1536D clustering against other representations.
    """
    logger.info("Calculating CSAI (cluster stability)...")

    base = labels_dict['1536D']

    scores = {}
    for name, labels in labels_dict.items():
        if name != '1536D':
            score = calculate_jaccard(base, labels)
            scores[name] = score
            logger.info(f"  J(1536D, {name}) = {score:.3f}")

    # Geometric mean for overall CSAI (all representations)
    values = list(scores.values())
    if all(v > 0 for v in values):
        csai_all = np.prod(values) ** (1/len(values))
    else:
        csai_all = 0.0
    logger.info(f"  CSAI (all, geo. mean) = {csai_all:.3f}")

    # CSAI for Matryoshka slices only (without TF-IDF)
    mrl_values = [scores.get('512D', 0), scores.get('256D', 0)]
    if all(v > 0 for v in mrl_values):
        csai_mrl = np.prod(mrl_values) ** (1/len(mrl_values))
    else:
        csai_mrl = 0.0
    logger.info(f"  CSAI (Matryoshka only) = {csai_mrl:.3f}")

    scores['CSAI'] = csai_all
    scores['CSAI_MRL'] = csai_mrl
    return scores


def analyze_clusters(articles: list, labels: np.ndarray, top_n: int = 5):
    """
    Step 6: Analyze top clusters - show representative titles.
    """
    logger.info(f"\nTop {top_n} clusters by size:")
    logger.info("=" * 60)

    # Count cluster sizes (exclude noise)
    cluster_counts = Counter(l for l in labels if l != -1)

    for cluster_id, count in cluster_counts.most_common(top_n):
        # Get articles in this cluster
        cluster_articles = [
            articles[i] for i, l in enumerate(labels) if l == cluster_id
        ]

        logger.info(f"\nCluster {cluster_id} ({count} articles):")
        logger.info("-" * 40)

        # Show sample titles
        for art in cluster_articles[:5]:
            title = art['title'][:80] if art['title'] else "[No title]"
            logger.info(f"  • {title}")


def visualize_clusters(embeddings: np.ndarray, labels: np.ndarray, output_path: str = "cluster_plot.png"):
    """
    Step 7: Create 2D UMAP visualization of clusters.
    """
    import matplotlib.pyplot as plt
    import umap

    logger.info(f"\nCreating 2D visualization...")

    # Reduce to 2D for visualization
    reducer = umap.UMAP(
        n_components=2,
        n_neighbors=15,
        min_dist=0.1,
        metric='cosine',
        random_state=42
    )
    coords_2d = reducer.fit_transform(embeddings)

    # Plot
    fig, ax = plt.subplots(figsize=(14, 10))

    # Unique labels
    unique_labels = sorted(set(labels))
    n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)

    # Color map (skip grey for noise)
    colors = plt.cm.tab20(np.linspace(0, 1, min(20, n_clusters)))

    for idx, label in enumerate(unique_labels):
        mask = labels == label
        if label == -1:
            # Noise in grey
            ax.scatter(coords_2d[mask, 0], coords_2d[mask, 1],
                      c='lightgrey', s=3, alpha=0.3, label='Noise')
        else:
            color_idx = idx % len(colors)
            ax.scatter(coords_2d[mask, 0], coords_2d[mask, 1],
                      c=[colors[color_idx]], s=8, alpha=0.7)

    ax.set_title(f"UMAP Cluster Visualization ({n_clusters} clusters)")
    ax.set_xlabel("UMAP 1")
    ax.set_ylabel("UMAP 2")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    logger.info(f"  Saved to: {output_path}")
    plt.close()

    return coords_2d


async def run_full_pipeline(sample_size: int = 5000):
    """Run the complete CSAI exploration pipeline."""

    logger.info("=" * 60)
    logger.info("CSAI Topic Discovery - Exploration")
    logger.info("=" * 60)

    # Step 1: Load data
    articles = await load_embeddings(sample_size)

    # Step 2: Matryoshka slices
    slices = create_matryoshka_slices(articles)

    # Step 3: TF-IDF
    tfidf = create_tfidf_vectors(articles)

    # Step 3.5: UMAP reduction BEFORE clustering (curse of dimensionality!)
    logger.info("\nReducing dimensions with UMAP...")
    reduced = {}
    reduced['1536D'] = reduce_dimensions(slices['1536D'], '1536D', n_components=10)
    reduced['512D'] = reduce_dimensions(slices['512D'], '512D', n_components=10)
    reduced['256D'] = reduce_dimensions(slices['256D'], '256D', n_components=10)
    reduced['TF-IDF'] = reduce_dimensions(tfidf, 'TF-IDF', n_components=10)

    # Step 4: Cluster each REDUCED representation
    logger.info("\nClustering reduced representations...")
    labels = {}
    labels['1536D'] = cluster_embeddings(reduced['1536D'], '1536D→10D')
    labels['512D'] = cluster_embeddings(reduced['512D'], '512D→10D')
    labels['256D'] = cluster_embeddings(reduced['256D'], '256D→10D')
    labels['TF-IDF'] = cluster_embeddings(reduced['TF-IDF'], 'TF-IDF→10D')

    # Step 5: CSAI
    csai_scores = calculate_csai(labels)

    # Step 6: Analyze clusters
    analyze_clusters(articles, labels['1536D'])

    # Step 7: Visualization
    output_dir = "/home/cytrex/news-microservices/docs/research"
    plot_path = f"{output_dir}/csai_clusters_{sample_size}.png"
    visualize_clusters(slices['1536D'], labels['1536D'], plot_path)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Sample size: {len(articles)}")
    logger.info(f"Clusters found: {len(set(labels['1536D'])) - (1 if -1 in labels['1536D'] else 0)}")
    logger.info(f"CSAI Score (all): {csai_scores['CSAI']:.3f}")
    logger.info(f"CSAI Score (Matryoshka): {csai_scores['CSAI_MRL']:.3f}")
    logger.info(f"\nInterpretation (Matryoshka CSAI):")
    if csai_scores['CSAI_MRL'] > 0.5:
        logger.info("  ✅ High stability - clusters exist across MRL resolutions")
    elif csai_scores['CSAI_MRL'] > 0.35:
        logger.info("  ⚠️ Medium stability - clusters mostly consistent")
    else:
        logger.info("  ❌ Low stability - clusters may be artifacts")

    logger.info(f"\nTF-IDF correlation: {csai_scores.get('TF-IDF', 0):.3f}")
    if csai_scores.get('TF-IDF', 0) < 0.15:
        logger.info("  → TF-IDF shows low correlation (expected - semantic vs lexical)")

    return {
        'articles': articles,
        'slices': slices,
        'labels': labels,
        'csai_scores': csai_scores
    }


async def main():
    parser = argparse.ArgumentParser(description="CSAI Topic Discovery Exploration")
    parser.add_argument("--sample", type=int, default=5000, help="Sample size")
    args = parser.parse_args()

    results = await run_full_pipeline(args.sample)

    return results


if __name__ == "__main__":
    asyncio.run(main())
