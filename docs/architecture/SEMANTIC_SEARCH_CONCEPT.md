# Semantic Search Concept - Clustering Service

**Date:** 2026-01-06
**Status:** Concept Discussion

## Core Insight

The clustering service should use **mathematical embedding similarity** for topic search, not string matching.

## Current State (Problem)

```
User Query "musk" → LIKE '%musk%' → String Matching → Limited Results
```

- `/topics/search` endpoint uses `search_clusters_by_keyword()`
- This does SQL `LIKE ANY(:patterns)` on article titles
- No semantic understanding - only finds exact string matches

## Target State (Solution)

```
User Query "finance" → OpenAI Embedding → pgvector Similarity → Mathematical Space → Related Clusters
```

- Query gets embedded into same 1536-dimensional space as articles
- pgvector `<=>` operator finds nearest cluster centroids
- System dynamically finds relevant mathematical regions

## Architecture Flow

### Existing (Article Embeddings)

```
content-analysis-v3
    → OpenAI text-embedding-3-small (1536D)
    → article_analysis.embedding
    → batch_clustering_worker loads embeddings
    → UMAP dimensionality reduction
    → HDBSCAN clustering
    → batch_clusters.centroid_vec (cluster centers in 1536D space)
```

### Required (Query Embeddings)

```
User Query
    → OpenAI text-embedding-3-small (1536D)
    → pgvector similarity search on batch_clusters.centroid_vec
    → Return nearest clusters
```

## Key Realizations

1. **Embeddings create mathematical spaces** - Articles with similar meaning are close in 1536D space

2. **Clusters are regions in that space** - UMAP+HDBSCAN groups nearby articles, centroid is the center

3. **Search = finding the right region** - Embed query into same space, find nearest centroids

4. **Categories become obsolete** - FINANCE, CONFLICT, POLITICS are just human labels for mathematical regions the system finds automatically

5. **SITREP service becomes redundant** - If clustering-service does semantic search properly, predefined category searches are unnecessary

## Implementation Requirements

1. **clustering-service needs embedding capability**
   - Either: Add OpenAI client directly
   - Or: Call content-analysis-v3 for embeddings
   - Or: Shared embedding service

2. **New search method in batch_cluster_repository**
   - `search_clusters_semantic(query: str) -> List[Cluster]`
   - Embeds query, uses existing `find_similar_clusters()` with pgvector

3. **Update /topics/search endpoint**
   - Replace string matching with semantic search
   - Or: Add new `/topics/semantic-search` endpoint

## Existing Infrastructure

- `batch_clusters.centroid_vec` - pgvector column (1536D) already exists
- `find_similar_clusters()` - pgvector search method already exists (needs embedding as input)
- `content-analysis-v3/providers/openai/provider.py` - `generate_embedding()` method exists

## Open Questions

- Where should embedding generation live? (clustering-service vs content-analysis-v3 vs shared)
- Caching strategy for query embeddings?
- Fallback to string search if embedding fails?

---

*This document captures the conceptual discussion. Implementation details to follow.*
