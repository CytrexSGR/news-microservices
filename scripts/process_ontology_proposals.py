#!/usr/bin/env python3
"""
Batch-process ontology proposals.

Usage:
    python process_ontology_proposals.py --action reject --pattern "UNKNOWN" --reason "Pipeline issue"
    python process_ontology_proposals.py --action accept --pattern "Article UUIDs"
"""
import requests
import argparse
import sys
from typing import List, Dict
import time

API_BASE = "http://localhost:8109/api/v1/ontology/proposals"

def get_proposals(severity: str = None, pattern: str = None, limit: int = 100) -> List[Dict]:
    """Fetch proposals matching criteria."""
    params = {"limit": limit}
    if severity:
        params["severity"] = severity

    response = requests.get(API_BASE, params=params)
    response.raise_for_status()

    proposals = response.json()["proposals"]

    # Filter by pattern if specified
    if pattern:
        proposals = [p for p in proposals if pattern.lower() in p["title"].lower()]

    return proposals

def update_proposal(proposal_id: int, status: str, reviewed_by: str = "system",
                    rejection_reason: str = None) -> Dict:
    """Update proposal status."""
    params = {
        "status": status,
        "reviewed_by": reviewed_by
    }

    if rejection_reason:
        params["rejection_reason"] = rejection_reason

    response = requests.put(f"{API_BASE}/{proposal_id}", params=params)
    response.raise_for_status()

    return response.json()

def main():
    parser = argparse.ArgumentParser(description="Batch-process ontology proposals")
    parser.add_argument("--action", choices=["accept", "reject", "list"], required=True,
                       help="Action to perform")
    parser.add_argument("--severity", choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                       help="Filter by severity")
    parser.add_argument("--pattern", help="Filter by title pattern")
    parser.add_argument("--reason", help="Rejection reason (for reject action)")
    parser.add_argument("--limit", type=int, default=100, help="Max proposals to process")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without doing it")

    args = parser.parse_args()

    # Fetch proposals
    print(f"Fetching proposals (severity={args.severity}, pattern={args.pattern})...")
    proposals = get_proposals(severity=args.severity, pattern=args.pattern, limit=args.limit)

    # Filter to only PENDING proposals
    pending_proposals = [p for p in proposals if p["status"] == "PENDING"]

    print(f"Found {len(proposals)} total proposals, {len(pending_proposals)} pending")

    if args.action == "list":
        for p in pending_proposals[:20]:  # Show first 20
            print(f"  [{p['severity']}] {p['title']} (occurrences: {p['occurrence_count']})")
        if len(pending_proposals) > 20:
            print(f"  ... and {len(pending_proposals) - 20} more")
        return

    # Process proposals
    if not pending_proposals:
        print("No pending proposals to process")
        return

    if args.action == "reject" and not args.reason:
        print("Error: --reason required for reject action")
        sys.exit(1)

    # Confirm action
    if not args.dry_run:
        response = input(f"\n{args.action.upper()} {len(pending_proposals)} proposals? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted")
            return

    # Process
    processed = 0
    for proposal in pending_proposals:
        try:
            if args.dry_run:
                print(f"[DRY-RUN] Would {args.action} proposal {proposal['id']}: {proposal['title']}")
            else:
                status = "REJECTED" if args.action == "reject" else "ACCEPTED"
                update_proposal(
                    proposal["id"],
                    status=status,
                    rejection_reason=args.reason if args.action == "reject" else None
                )
                print(f"✓ {status} proposal {proposal['id']}: {proposal['title']}")
                processed += 1

                # Rate limiting
                time.sleep(0.1)
        except Exception as e:
            print(f"✗ Error processing proposal {proposal['id']}: {e}")

    print(f"\nProcessed {processed}/{len(pending_proposals)} proposals")

if __name__ == "__main__":
    main()
