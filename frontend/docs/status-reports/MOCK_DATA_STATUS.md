# Mock Data Status - Knowledge Graph Admin

## Overview
This document tracks which components in the Knowledge Graph Admin dashboard use mock data and what backend features are required to replace them with real data.

## Components with Real Data ✅

### Entity Type Trends
- **Status**: ✅ Real API implemented
- **Endpoint**: `GET /api/v1/canonicalization/trends/entity-types`
- **Service**: entity-canonicalization-service (port 8112)
- **Implemented**: 2025-10-24

## Components with Mock Data ⚠️

### 1. Entity Merge History
- **Status**: ⚠️ Mock data (backend feature missing)
- **Component**: `EntityMergeHistory.tsx`
- **Required Feature**: Event logging for entity merges
- **Implementation Needed**:
  - Add event tracking table in `entity-canonicalization-service`
  - Log every merge operation (source, target, method, confidence)
  - Create API endpoint to query merge history
- **Priority**: Medium
- **Estimated Effort**: 4-6 hours

### 2. Disambiguation Quality
- **Status**: ⚠️ Mock data (backend feature missing)
- **Component**: `DisambiguationQuality.tsx`
- **Required Feature**: Disambiguation quality tracking and metrics
- **Implementation Needed**:
  - Track disambiguation attempts (successful, ambiguous, failed)
  - Calculate confidence scores for each disambiguation
  - Store low-confidence cases for review
  - Create API endpoint for quality metrics
- **Priority**: Medium
- **Estimated Effort**: 6-8 hours

### 3. Cross-Article Entity Coverage
- **Status**: ⚠️ Mock data (backend feature missing)
- **Component**: `CrossArticleCoverage.tsx`
- **Required Feature**: Article-Entity relationship tracking in Neo4j
- **Implementation Needed**:
  - Modify `knowledge-graph-service` to store Article nodes
  - Create `EXTRACTED_FROM` relationships between Entity and Article
  - Store article metadata (title, published_at, etc.)
  - Update entity extraction pipeline to create these relationships
  - API endpoint already created: `GET /api/v1/graph/analytics/cross-article-coverage`
- **Priority**: High (API already implemented, only data model missing)
- **Estimated Effort**: 8-10 hours
- **Note**: Backend API endpoint exists but returns empty data because Article nodes don't exist in Neo4j

## Implementation Roadmap

### Phase 1: Critical Data Model Fix
1. **Cross-Article Coverage** - Add Article nodes to Neo4j
   - Modify entity extraction to create Article nodes
   - Update RabbitMQ message handlers
   - Test with existing data

### Phase 2: Audit and Tracking
2. **Entity Merge History** - Add merge event logging
   - Create database table for merge events
   - Update batch reprocessor to log events
   - Create API endpoint

3. **Disambiguation Quality** - Add quality tracking
   - Create metrics tracking system
   - Update canonicalization service
   - Create API endpoint

## Testing Status

| Component | Mock Warning Visible | Backend Endpoint | Data Available |
|-----------|---------------------|------------------|----------------|
| Entity Type Trends | N/A | ✅ | ✅ |
| Entity Merge History | ✅ | ❌ | ❌ |
| Disambiguation Quality | ✅ | ❌ | ❌ |
| Cross-Article Coverage | ✅ | ✅ | ❌ |

## Notes

- All mock components now display clear warning banners explaining:
  - That they show placeholder data
  - Which backend features are missing
  - Where implementation is needed

- Users can see the UI design and understand what data will be displayed once backend features are implemented

- Priority should be given to Cross-Article Coverage as the API endpoint already exists and only the data model needs to be updated

---
Last Updated: 2025-10-24
