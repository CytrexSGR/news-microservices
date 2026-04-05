"""Ontology Proposals API Router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from app.database import get_db
from app.schemas.proposal import ProposalCreate, ProposalResponse
from app.models.proposal import OntologyProposal

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/ontology/proposals",
    tags=["Proposals"]
)


@router.post(
    "",
    response_model=ProposalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new ontology proposal",
    description="Receive and store a new ontology change proposal from OSS"
)
async def create_proposal(
    proposal: ProposalCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new ontology proposal.

    Args:
        proposal: Proposal data
        db: Database session

    Returns:
        ProposalResponse with success status and proposal ID

    Raises:
        HTTPException: If proposal_id already exists or database error
    """
    try:
        # Create database model
        db_proposal = OntologyProposal(**proposal.model_dump())

        # Add to database
        db.add(db_proposal)
        db.commit()
        db.refresh(db_proposal)

        logger.info(f"Created proposal: {proposal.proposal_id}")

        return ProposalResponse(
            success=True,
            proposal_id=proposal.proposal_id,
            message="Proposal created successfully"
        )

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Duplicate proposal_id: {proposal.proposal_id}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Proposal with ID {proposal.proposal_id} already exists"
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating proposal: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create proposal"
        )


@router.get(
    "/statistics",
    summary="Get proposal statistics",
    description="Get aggregate statistics for all proposals"
)
async def get_statistics(db: Session = Depends(get_db)):
    """
    Get proposal statistics including counts by status, severity, and change type.

    Returns:
        Dict with aggregate statistics
    """
    from sqlalchemy import func

    # Total counts
    total_proposals = db.query(func.count(OntologyProposal.id)).scalar()
    pending_count = db.query(func.count(OntologyProposal.id)).filter(
        OntologyProposal.status == "PENDING"
    ).scalar()
    accepted_count = db.query(func.count(OntologyProposal.id)).filter(
        OntologyProposal.status == "ACCEPTED"
    ).scalar()
    rejected_count = db.query(func.count(OntologyProposal.id)).filter(
        OntologyProposal.status == "REJECTED"
    ).scalar()
    implemented_count = db.query(func.count(OntologyProposal.id)).filter(
        OntologyProposal.status == "IMPLEMENTED"
    ).scalar()

    # By severity
    severity_counts = db.query(
        OntologyProposal.severity,
        func.count(OntologyProposal.id)
    ).group_by(OntologyProposal.severity).all()

    by_severity = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0
    }
    for severity, count in severity_counts:
        by_severity[severity] = count

    # By change type
    change_type_counts = db.query(
        OntologyProposal.change_type,
        func.count(OntologyProposal.id)
    ).group_by(OntologyProposal.change_type).all()

    by_change_type = {
        "NEW_ENTITY_TYPE": 0,
        "NEW_RELATIONSHIP_TYPE": 0,
        "MODIFY_ENTITY_TYPE": 0,
        "MODIFY_RELATIONSHIP_TYPE": 0,
        "FLAG_INCONSISTENCY": 0
    }
    for change_type, count in change_type_counts:
        by_change_type[change_type] = count

    # Average confidence
    avg_confidence = db.query(
        func.avg(OntologyProposal.confidence)
    ).scalar() or 0.0

    return {
        "total_proposals": total_proposals,
        "pending_count": pending_count,
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "implemented_count": implemented_count,
        "by_severity": by_severity,
        "by_change_type": by_change_type,
        "avg_confidence": float(avg_confidence)
    }


@router.get(
    "/{proposal_id}",
    summary="Get proposal by ID",
    description="Retrieve a specific proposal by its ID (numeric database ID or string proposal_id)"
)
async def get_proposal(
    proposal_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a proposal by ID.

    Supports both:
    - Numeric database ID (e.g., "5") → queries OntologyProposal.id
    - String proposal_id (e.g., "OSS_20251110_183240_1b86a2d7") → queries OntologyProposal.proposal_id
    """
    # Try to parse as integer for database ID lookup
    try:
        numeric_id = int(proposal_id)
        proposal = db.query(OntologyProposal).filter(
            OntologyProposal.id == numeric_id
        ).first()
    except ValueError:
        # Not a number, treat as string proposal_id
        proposal = db.query(OntologyProposal).filter(
            OntologyProposal.proposal_id == proposal_id
        ).first()

    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal {proposal_id} not found"
        )

    return proposal


@router.put(
    "/{proposal_id}",
    summary="Update proposal",
    description="Update proposal status, reviewer, and notes"
)
async def update_proposal(
    proposal_id: str,
    status: str = None,
    reviewed_by: str = None,
    rejection_reason: str = None,
    implementation_notes: str = None,
    db: Session = Depends(get_db)
):
    """
    Update a proposal (accept, reject, or mark as implemented).

    Supports both:
    - Numeric database ID (e.g., "5") → queries OntologyProposal.id
    - String proposal_id (e.g., "OSS_20251110_183240_1b86a2d7") → queries OntologyProposal.proposal_id
    """
    from datetime import datetime

    # Try to parse as integer for database ID lookup
    try:
        numeric_id = int(proposal_id)
        proposal = db.query(OntologyProposal).filter(
            OntologyProposal.id == numeric_id
        ).first()
    except ValueError:
        # Not a number, treat as string proposal_id
        proposal = db.query(OntologyProposal).filter(
            OntologyProposal.proposal_id == proposal_id
        ).first()

    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal {proposal_id} not found"
        )

    # Update fields if provided
    if status:
        proposal.status = status
    if reviewed_by:
        proposal.reviewed_by = reviewed_by
        proposal.reviewed_at = datetime.utcnow()
    if rejection_reason:
        proposal.rejection_reason = rejection_reason
    if implementation_notes:
        proposal.implementation_notes = implementation_notes

    db.commit()
    db.refresh(proposal)

    logger.info(f"Updated proposal: {proposal.proposal_id} → status={status}")

    return proposal


@router.get(
    "",
    summary="List proposals",
    description="List all proposals with optional filtering"
)
async def list_proposals(
    status: str = None,
    severity: str = None,
    change_type: str = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List proposals with optional filters."""
    query = db.query(OntologyProposal)

    if status:
        query = query.filter(OntologyProposal.status == status)
    if severity:
        query = query.filter(OntologyProposal.severity == severity)
    if change_type:
        query = query.filter(OntologyProposal.change_type == change_type)

    total = query.count()
    proposals = query.order_by(
        OntologyProposal.created_at.desc()
    ).offset(offset).limit(limit).all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "proposals": proposals
    }


@router.post(
    "/{proposal_id}/implement",
    summary="Implement accepted proposal",
    description="Execute Cypher scripts to implement the proposal changes in Neo4j"
)
async def implement_proposal(
    proposal_id: str,
    db: Session = Depends(get_db)
):
    """
    Implement an accepted proposal.

    Executes the necessary Cypher scripts against Neo4j to apply the proposed changes.
    Updates proposal status to IMPLEMENTED on success.

    Args:
        proposal_id: Proposal ID (numeric or string format)
        db: Database session

    Returns:
        Dict with implementation results (nodes affected, errors, etc.)

    Raises:
        HTTPException: If proposal not found, not accepted, or implementation fails
    """
    from datetime import datetime
    from app.services.implementation import implementation_service

    # Find proposal (supports both numeric and string IDs)
    try:
        numeric_id = int(proposal_id)
        proposal = db.query(OntologyProposal).filter(
            OntologyProposal.id == numeric_id
        ).first()
    except ValueError:
        proposal = db.query(OntologyProposal).filter(
            OntologyProposal.proposal_id == proposal_id
        ).first()

    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal {proposal_id} not found"
        )

    # Check if proposal is accepted
    if proposal.status != "ACCEPTED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Proposal must be ACCEPTED to implement (current status: {proposal.status})"
        )

    # Execute implementation
    try:
        logger.info(f"Implementing proposal: {proposal.proposal_id}")
        results = implementation_service.implement_proposal(proposal)

        # Update proposal status
        proposal.status = "IMPLEMENTED"
        proposal.implemented_at = datetime.utcnow()
        proposal.implementation_notes = f"Automated implementation completed. Results: {results}"

        db.commit()
        db.refresh(proposal)

        logger.info(f"Successfully implemented proposal: {proposal.proposal_id}")

        return {
            "success": True,
            "proposal_id": proposal.proposal_id,
            "results": results,
            "message": "Proposal implemented successfully"
        }

    except ValueError as e:
        logger.error(f"Invalid proposal configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to implement proposal: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to implement proposal: {str(e)}"
        )
