"""
Ontology Proposal Auto-Approver

Automatically approves and implements high-confidence ontology proposals
that match predefined criteria, reducing manual review overhead.

Auto-Approval Criteria:
- FLAG_INCONSISTENCY with confidence >= 95%
  - ISO code violations
  - UNKNOWN entity types
  - Article UUID garbage
  - Missing required properties
  - Duplicate entities

- NEW_ENTITY_TYPE with confidence >= 98% AND occurrences >= 100
  - Only for well-established patterns

Runs every 5 minutes via APScheduler.

Created: 2025-12-27
"""

import logging
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

# Configuration
PROPOSALS_SERVICE_URL = "http://news-ontology-proposals-service:8109"
AUTO_APPROVE_INTERVAL = 300  # 5 minutes

# Auto-approval rules
AUTO_APPROVE_RULES = {
    "FLAG_INCONSISTENCY": {
        "min_confidence": 0.95,
        "min_occurrences": 1,
        "title_patterns": [
            "ISO",
            "country code",
            "UNKNOWN",
            "missing required properties",
            "Article UUID",
            "Article UUIDs",
            "Duplicate entity_id",
        ]
    },
    "NEW_ENTITY_TYPE": {
        "min_confidence": 0.98,
        "min_occurrences": 100,
        "title_patterns": None  # Accept any title if criteria met
    }
}


class ProposalAutoApprover:
    """Automatically approves and implements high-confidence proposals."""

    def __init__(self):
        self.stats = {
            "runs": 0,
            "proposals_checked": 0,
            "proposals_approved": 0,
            "proposals_implemented": 0,
            "errors": 0
        }

    async def run(self) -> Dict[str, Any]:
        """
        Main auto-approval cycle.

        Returns:
            Dict with run statistics
        """
        self.stats["runs"] += 1
        run_start = datetime.utcnow()

        result = {
            "run_id": f"auto_approve_{run_start.strftime('%Y%m%d_%H%M%S')}",
            "started_at": run_start.isoformat(),
            "proposals_checked": 0,
            "proposals_approved": 0,
            "proposals_implemented": 0,
            "approved_ids": [],
            "implemented_ids": [],
            "errors": []
        }

        try:
            # Step 1: Fetch pending proposals
            pending = await self._fetch_pending_proposals()
            result["proposals_checked"] = len(pending)
            self.stats["proposals_checked"] += len(pending)

            if not pending:
                logger.debug("No pending proposals to process")
                return result

            logger.info(f"Auto-approver checking {len(pending)} pending proposals")

            # Step 2: Filter by auto-approval rules
            to_approve = []
            for proposal in pending:
                if self._should_auto_approve(proposal):
                    to_approve.append(proposal)

            logger.info(f"Auto-approving {len(to_approve)} proposals")

            # Step 3: Approve and implement each
            for proposal in to_approve:
                try:
                    # Approve
                    approved = await self._approve_proposal(proposal["proposal_id"])
                    if approved:
                        result["proposals_approved"] += 1
                        result["approved_ids"].append(proposal["proposal_id"])
                        self.stats["proposals_approved"] += 1

                        # Implement
                        implemented = await self._implement_proposal(proposal["proposal_id"])
                        if implemented:
                            result["proposals_implemented"] += 1
                            result["implemented_ids"].append(proposal["proposal_id"])
                            self.stats["proposals_implemented"] += 1
                            logger.info(f"Auto-implemented: {proposal['title'][:50]}...")

                except Exception as e:
                    error_msg = f"Failed to process {proposal['proposal_id']}: {e}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
                    self.stats["errors"] += 1

            result["completed_at"] = datetime.utcnow().isoformat()
            logger.info(
                f"Auto-approval complete: {result['proposals_approved']} approved, "
                f"{result['proposals_implemented']} implemented"
            )

        except Exception as e:
            error_msg = f"Auto-approval run failed: {e}"
            logger.error(error_msg, exc_info=True)
            result["errors"].append(error_msg)
            self.stats["errors"] += 1

        return result

    async def _fetch_pending_proposals(self) -> List[Dict[str, Any]]:
        """Fetch pending proposals from ontology-proposals-service."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{PROPOSALS_SERVICE_URL}/api/v1/ontology/proposals",
                params={"status": "PENDING", "limit": 100}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("proposals", [])

    def _should_auto_approve(self, proposal: Dict[str, Any]) -> bool:
        """
        Check if proposal matches auto-approval criteria.

        Args:
            proposal: Proposal dict with title, change_type, confidence, occurrences

        Returns:
            True if proposal should be auto-approved
        """
        change_type = proposal.get("change_type")
        confidence = proposal.get("confidence") or 0
        occurrences = proposal.get("occurrences") or 0
        title = proposal.get("title", "")

        # Get rules for this change_type
        rules = AUTO_APPROVE_RULES.get(change_type)
        if not rules:
            return False

        # Check confidence threshold
        if confidence < rules["min_confidence"]:
            return False

        # Check occurrences threshold (skip if occurrences not tracked)
        min_occ = rules["min_occurrences"]
        if min_occ > 1 and occurrences < min_occ:
            return False

        # Check title patterns (if specified)
        title_patterns = rules.get("title_patterns")
        if title_patterns:
            matches_pattern = any(
                pattern.lower() in title.lower()
                for pattern in title_patterns
            )
            if not matches_pattern:
                return False

        return True

    async def _approve_proposal(self, proposal_id: str) -> bool:
        """
        Approve a proposal.

        Args:
            proposal_id: The proposal ID to approve

        Returns:
            True if successfully approved
        """
        async with httpx.AsyncClient(timeout=30) as client:
            # Use PUT with query params (as per API design)
            response = await client.put(
                f"{PROPOSALS_SERVICE_URL}/api/v1/ontology/proposals/{proposal_id}",
                params={
                    "status": "ACCEPTED",
                    "reviewed_by": "auto-approver"
                }
            )
            response.raise_for_status()
            return True

    async def _implement_proposal(self, proposal_id: str) -> bool:
        """
        Implement an approved proposal.

        Args:
            proposal_id: The proposal ID to implement

        Returns:
            True if successfully implemented
        """
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{PROPOSALS_SERVICE_URL}/api/v1/ontology/proposals/{proposal_id}/implement"
            )
            response.raise_for_status()
            return True

    def get_stats(self) -> Dict[str, Any]:
        """Get auto-approver statistics."""
        return {
            **self.stats,
            "rules": {
                change_type: {
                    "min_confidence": f"{rules['min_confidence']*100:.0f}%",
                    "min_occurrences": rules["min_occurrences"],
                    "patterns": rules.get("title_patterns", "any")
                }
                for change_type, rules in AUTO_APPROVE_RULES.items()
            }
        }


# Global instance
proposal_auto_approver = ProposalAutoApprover()


async def auto_approve_proposals_job():
    """Job function for APScheduler."""
    await proposal_auto_approver.run()
