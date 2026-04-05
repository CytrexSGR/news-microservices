#!/usr/bin/env python3
"""
Fix n8n Workflow with JWT Authentication
=========================================

Updated version using stable JWT auth instead of API keys.

This script fixes the Entity-to-Knowledge-Graph-v1 workflow:
- Transform node: Gets IDs from Extract Entity Data node
- Mark as Processed: References Transform node directly via $node[...]

Usage:
    python3 scripts/fix_workflow_jwt.py [workflow_id]

Example:
    python3 scripts/fix_workflow_jwt.py 5o3ZjyhLELti9its
"""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.n8n_jwt_auth import N8nAuth


def fix_workflow(workflow_id: str = "5o3ZjyhLELti9its"):
    """
    Fix workflow using JWT authentication

    Args:
        workflow_id: Workflow ID to fix (default: Entity-to-Knowledge-Graph-v1)
    """
    print(f"🔧 Fixing workflow {workflow_id} using JWT auth\n")

    # Authenticate
    auth = N8nAuth()
    auth.login()

    # Fetch workflow
    print(f"📥 Fetching workflow...")
    resp = auth.get(f"api/v1/workflows/{workflow_id}")

    if resp.status_code != 200:
        print(f"❌ Failed to fetch workflow: HTTP {resp.status_code}")
        print(resp.text)
        return False

    workflow = resp.json()
    print(f"✅ Got workflow: {workflow['name']}")
    print(f"   Nodes: {len(workflow['nodes'])}")

    # Fix Transform node
    transform_updated = False
    mark_updated = False

    for node in workflow['nodes']:
        if node['name'] == 'Transform for Knowledge Graph':
            # New code that gets IDs from Extract Entity Data node
            new_code = '''// Transform canonicalized entities into RelationshipsExtractedEvent format
const canonicalizedResults = $input.item.json.results || [];

// Get article_id and agent_result_id from Extract Entity Data node (NOT from current input!)
const extractData = $node["Extract Entity Data"].json;
const articleId = extractData.article_id;
const agentResultId = extractData.agent_result_id;

const triplets = canonicalizedResults.map((entity) => ({
  subject: {
    text: entity.canonical_name,
    type: entity.entity_type,
    wikidata_id: entity.canonical_id
  },
  relationship: {
    type: 'MENTIONED_IN',
    confidence: entity.confidence,
    evidence: `Extracted from article ${articleId}`
  },
  object: {
    text: `Article ${articleId}`,
    type: 'ARTICLE',
    wikidata_id: null
  }
}));

return {
  json: {
    event_type: 'relationships.extracted',
    timestamp: new Date().toISOString(),
    payload: {
      article_id: articleId,
      source_url: null,
      triplets: triplets,
      extraction_timestamp: new Date().toISOString(),
      total_relationships: triplets.length
    },
    agent_result_id: agentResultId  // For Mark as Processed node
  }
};'''

            node['parameters']['jsCode'] = new_code
            transform_updated = True
            print(f"\n✅ Updated 'Transform for Knowledge Graph' node")

        elif node['name'] == 'Mark as Processed':
            # Update SQL query to reference Transform node directly
            new_query = '''UPDATE content_analysis_v2.agent_results
SET processed_by_kg = true
WHERE id = '{{ $node["Transform for Knowledge Graph"].json.agent_result_id }}' '''

            node['parameters']['query'] = new_query
            mark_updated = True
            print(f"✅ Updated 'Mark as Processed' node")

    if not transform_updated or not mark_updated:
        print(f"\n❌ ERROR: Could not find required nodes!")
        return False

    # Update workflow via API
    print(f"\n📤 Updating workflow via JWT-authenticated API...")

    update_payload = {
        "name": workflow['name'],
        "nodes": workflow['nodes'],
        "connections": workflow['connections'],
        "settings": workflow.get('settings', {}),
        "staticData": workflow.get('staticData')
    }

    resp = auth.put(f"api/v1/workflows/{workflow_id}", json=update_payload)

    if resp.status_code == 200:
        result = resp.json()
        print(f"\n🎉 SUCCESS! Workflow updated!")
        print(f"   Updated at: {result['updatedAt']}")

        # Reload workflow if active
        if workflow.get('active'):
            print(f"\n🔄 Reloading workflow...")
            auth.post(f"api/v1/workflows/{workflow_id}/deactivate")
            auth.post(f"api/v1/workflows/{workflow_id}/activate")
            print(f"✅ Workflow reactivated!")

        print(f"\n⏰ Next execution should run in ~30 seconds")
        print(f"   Monitor with: docker logs news-n8n -f")
        return True
    else:
        print(f"\n❌ Update failed: HTTP {resp.status_code}")
        print(resp.text)
        return False


def main():
    """Main entry point"""
    workflow_id = sys.argv[1] if len(sys.argv) > 1 else "5o3ZjyhLELti9its"

    print("=" * 70)
    print("n8n Workflow Fix - JWT Authentication")
    print("=" * 70)
    print()

    success = fix_workflow(workflow_id)

    print()
    print("=" * 70)

    if success:
        print("✅ Workflow fix completed successfully!")
        print()
        print("Next steps:")
        print("1. Monitor workflow execution: docker logs news-n8n -f")
        print("2. Check for errors in next 30 seconds")
        print("3. Verify 'processed_by_kg' flag in database")
        sys.exit(0)
    else:
        print("❌ Workflow fix failed!")
        print()
        print("Troubleshooting:")
        print("1. Check n8n container is running: docker ps | grep n8n")
        print("2. Verify JWT auth is enabled: docker logs news-n8n | grep JWT")
        print("3. Check credentials in scripts/n8n_jwt_auth.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
