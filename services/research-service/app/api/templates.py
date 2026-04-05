"""Template API endpoints."""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, CurrentUser
from app.core.database import get_db
from app.schemas.research import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateApply,
    TemplatePreview,
    ResearchTaskResponse,
)
from app.services.research import template_service, research_service
from app.services.function_registry import list_functions
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/templates", tags=["templates"])


@router.post("/", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new research template."""
    try:
        template = await template_service.create_template(
            db, current_user.user_id, template_data.model_dump()
        )
        return template
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create template"
        )


@router.get("/", response_model=list[TemplateResponse])
async def list_templates(
    include_public: bool = Query(True),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List available templates."""
    templates = await template_service.list_templates(db, current_user.user_id, include_public)
    return templates


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific template."""
    template = await template_service.get_template(db, template_id, current_user.user_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return template


@router.get("/functions")
async def list_research_functions():
    """List available specialised research functions."""
    return {"functions": list_functions()}


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    update_data: TemplateUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a template."""
    template = await template_service.get_template(db, template_id, current_user.user_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    
    # Check ownership
    if template.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this template"
        )
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a template."""
    template = await template_service.get_template(db, template_id, current_user.user_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    
    # Check ownership
    if template.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this template"
        )
    
    template.is_active = False
    db.commit()


@router.post("/{template_id}/preview", response_model=TemplatePreview)
async def preview_template(
    template_id: int,
    apply_data: TemplateApply,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Preview rendered template with variables."""
    template = await template_service.get_template(db, template_id, current_user.user_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    
    rendered_query = await template_service.apply_template(db, template, apply_data.variables)
    
    # Estimate cost
    model_name = apply_data.model_name or template.default_model
    model_config = settings.get_model_config(model_name)
    estimated_tokens = len(rendered_query.split()) * 1.3  # Rough estimate
    estimated_cost = settings.calculate_cost(int(estimated_tokens), model_name)
    
    return TemplatePreview(
        template_id=template_id,
        variables=apply_data.variables,
        rendered_query=rendered_query,
        estimated_cost=estimated_cost
    )


@router.post("/{template_id}/apply", response_model=ResearchTaskResponse)
async def apply_template(
    template_id: int,
    apply_data: TemplateApply,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Apply template and create research task."""
    template = await template_service.get_template(db, template_id, current_user.user_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    
    try:
        if template.research_function:
            template.usage_count += 1
            template.last_used_at = datetime.utcnow()
            db.commit()
            combined_parameters: Dict[str, Any] = dict(template.function_parameters or {})
            combined_parameters.update(apply_data.variables or {})
            task = await research_service.execute_function(
                db=db,
                user_id=current_user.user_id,
                function_name=template.research_function,
                parameters=combined_parameters,
            )
        else:
            # Render query for classic templates
            rendered_query = await template_service.apply_template(
                db, template, apply_data.variables
            )
            task = await research_service.create_research_task(
                db=db,
                user_id=current_user.user_id,
                query=rendered_query,
                model_name=apply_data.model_name or template.default_model,
                depth=apply_data.depth or template.default_depth,
                feed_id=apply_data.feed_id,
                legacy_feed_id=apply_data.legacy_feed_id,
                article_id=apply_data.article_id,
                legacy_article_id=apply_data.legacy_article_id,
            )
        return task
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Failed to apply template: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply template",
        ) from exc
