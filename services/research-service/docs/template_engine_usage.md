# Template Engine Usage Guide

## Overview

The Template Engine provides powerful template-based research automation with variable substitution, conditional logic, batch processing, and scheduled execution.

## Features

- **Variable Substitution**: `{{variable}}` syntax for dynamic queries
- **Conditional Logic**: `{{#if variable}}...{{/if}}` and `{{#if variable}}...{{else}}...{{/if}}`
- **Batch Processing**: Execute templates with multiple variable sets
- **Scheduled Execution**: Schedule templates for future execution
- **Result Aggregation**: Combine results from multiple executions
- **Usage Tracking**: Track template usage statistics
- **Pattern Library**: Pre-built templates for common research tasks

## Basic Usage

### 1. Create a Template

```python
from app.services.template_engine import template_engine
from app.core.database import SessionLocal

db = SessionLocal()

# Simple template
template = ResearchTemplate(
    user_id=1,
    name="Technology News Analysis",
    description="Analyze recent technology news",
    query_template="Analyze recent developments in {{topic}} technology. Focus on {{aspect}}.",
    parameters={
        "topic": "Technology area (e.g., AI, blockchain)",
        "aspect": "Specific aspect to analyze"
    },
    default_model="sonar",
    default_depth="standard"
)

db.add(template)
db.commit()
```

### 2. Parse and Validate Template

```python
# Parse template to extract metadata
metadata = template_engine.parse_template(template.query_template)

print(metadata)
# {
#     "variables": ["topic", "aspect"],
#     "required_variables": ["topic", "aspect"],
#     "optional_variables": [],
#     "conditionals": [],
#     "has_conditionals": False
# }

# Validate parameters
variables = {"topic": "AI", "aspect": "ethics"}
is_valid, error = template_engine.validate_parameters(template, variables)

if not is_valid:
    print(f"Validation error: {error}")
```

### 3. Preview Rendered Query

```python
# Preview without executing
preview = template_engine.preview_template(template, variables)

print(preview)
# {
#     "template_id": 1,
#     "template_name": "Technology News Analysis",
#     "is_valid": True,
#     "error": None,
#     "rendered_query": "Analyze recent developments in AI technology. Focus on ethics.",
#     "estimated_tokens": 15,
#     "estimated_cost": 0.001,
#     "model": "sonar",
#     "depth": "standard"
# }
```

### 4. Execute Template

```python
# Execute with variables
task = await template_engine.execute_template(
    db=db,
    user_id=1,
    template=template,
    variables=variables,
    model_name=None,  # Use template default
    depth=None        # Use template default
)

print(f"Task ID: {task.id}, Status: {task.status}")
```

## Conditional Logic

### If Blocks

```python
template = ResearchTemplate(
    user_id=1,
    name="Article Analysis with Optional Timeframe",
    query_template="""
Analyze articles about {{topic}}
{{#if timeframe}}published in the last {{timeframe}}{{/if}}
from {{source}}.
    """,
    parameters={
        "topic": "Main topic",
        "timeframe": "(Optional) Time range",
        "source": "News source"
    }
)

# With timeframe
variables = {"topic": "AI", "timeframe": "week", "source": "TechCrunch"}
# Result: "Analyze articles about AI published in the last week from TechCrunch."

# Without timeframe
variables = {"topic": "AI", "timeframe": "", "source": "TechCrunch"}
# Result: "Analyze articles about AI from TechCrunch."
```

### If/Else Blocks

```python
template = ResearchTemplate(
    user_id=1,
    name="Research with Depth Control",
    query_template="""
{{#if deep_mode}}
Perform comprehensive deep research on {{topic}}, including:
- Historical context
- Expert opinions
- Statistical analysis
- Future predictions
{{else}}
Provide a quick overview of {{topic}} with key points.
{{/if}}
    """,
    parameters={
        "topic": "Research topic",
        "deep_mode": "(Optional) Enable deep research"
    }
)

# Deep mode
variables = {"topic": "Quantum Computing", "deep_mode": "yes"}
# Result: Full deep research prompt

# Quick mode
variables = {"topic": "Quantum Computing", "deep_mode": ""}
# Result: Quick overview prompt
```

## Batch Processing

### Execute Multiple Variable Sets

```python
# Batch execution
variable_sets = [
    {"topic": "AI", "aspect": "ethics"},
    {"topic": "Blockchain", "aspect": "scalability"},
    {"topic": "Quantum", "aspect": "applications"}
]

tasks = await template_engine.batch_execute(
    db=db,
    user_id=1,
    template=template,
    variable_sets=variable_sets,
    model_name="sonar-pro",
    depth="deep"
)

print(f"Created {len(tasks)} research tasks")
for task in tasks:
    print(f"- Task {task.id}: {task.query}")
```

### Aggregate Results

```python
# Get aggregated results
task_ids = [task.id for task in tasks]

aggregated = await template_engine.aggregate_results(
    db=db,
    task_ids=task_ids,
    user_id=1
)

print(f"Total: {aggregated['total']}")
print(f"Completed: {aggregated['completed']}")
print(f"Total Cost: ${aggregated['total_cost']:.4f}")
print(f"Unique Sources: {aggregated['unique_sources']}")
print(f"\nConsolidated Content:\n{aggregated['aggregated_content']}")
```

## Scheduled Execution

### Schedule for Future Time

```python
from datetime import datetime, timedelta

# Schedule for 1 hour from now
schedule_at = datetime.utcnow() + timedelta(hours=1)

scheduled = await template_engine.schedule_execution(
    db=db,
    user_id=1,
    template=template,
    variables={"topic": "AI", "aspect": "regulation"},
    schedule_at=schedule_at,
    model_name="sonar-pro"
)

print(f"Scheduled task: {scheduled['celery_task_id']}")
print(f"Will execute at: {scheduled['scheduled_at']}")
```

### Using Celery Tasks Directly

```python
from app.workers.tasks import process_template_execution, batch_template_execution

# Schedule single execution
task = process_template_execution.apply_async(
    kwargs={
        "user_id": 1,
        "template_id": template.id,
        "variables": {"topic": "AI", "aspect": "ethics"},
        "model_name": "sonar",
        "depth": "standard"
    },
    eta=schedule_at
)

# Batch execution
task = batch_template_execution.delay(
    user_id=1,
    template_id=template.id,
    variable_sets=variable_sets,
    model_name="sonar-pro",
    depth="deep"
)
```

## Pattern Library

### Create from Pre-built Patterns

```python
# Feed Analysis Pattern
template = await template_engine.create_from_pattern(
    db=db,
    user_id=1,
    pattern_name="feed_analysis",
    context={"topic": "Technology", "feed_name": "TechCrunch"}
)

# Execute
task = await template_engine.execute_template(
    db=db,
    user_id=1,
    template=template,
    variables={
        "topic": "AI",
        "feed_name": "TechCrunch",
        "time_range": "last week"
    }
)
```

### Available Patterns

1. **feed_analysis**: Analyze RSS feed articles for themes
   ```python
   context = {"topic": "AI", "feed_name": "TechCrunch"}
   variables = {"topic": "AI", "feed_name": "TechCrunch", "time_range": "week"}
   ```

2. **article_summary**: Deep dive into article topic
   ```python
   context = {"article_title": "Future of AI"}
   variables = {"article_title": "Future of AI", "specific_aspect": "ethics"}
   ```

3. **trend_detection**: Detect emerging trends
   ```python
   context = {"domain": "Technology"}
   variables = {"domain": "Technology", "timeframe": "quarter"}
   ```

4. **fact_check**: Verify claims with sources
   ```python
   context = {"claim": "AI will replace programmers"}
   variables = {"claim": "AI will replace programmers", "claimant": "Tech CEO"}
   ```

## Usage Tracking

### Track Template Usage

```python
# Get usage statistics
stats = await template_engine.track_template_usage(
    db=db,
    template_id=template.id,
    user_id=1,
    days=30
)

print(f"Template: {stats['template_name']}")
print(f"Total Usage: {stats['total_usage']}")
print(f"Last Used: {stats['last_used']}")
```

## API Integration Example

### FastAPI Endpoint

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.template_engine import template_engine

router = APIRouter()

@router.post("/templates/{template_id}/execute")
async def execute_template_endpoint(
    template_id: int,
    variables: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get template
    template = db.query(ResearchTemplate).filter(
        ResearchTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Execute
    task = await template_engine.execute_template(
        db=db,
        user_id=current_user.id,
        template=template,
        variables=variables
    )

    return {
        "task_id": task.id,
        "status": task.status,
        "query": task.query
    }

@router.post("/templates/{template_id}/preview")
async def preview_template_endpoint(
    template_id: int,
    variables: dict,
    db: Session = Depends(get_db)
):
    template = db.query(ResearchTemplate).filter(
        ResearchTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    preview = template_engine.preview_template(template, variables)
    return preview
```

## Best Practices

### 1. Template Design

- **Keep templates focused**: One template per research type
- **Use descriptive variable names**: `{{article_title}}` not `{{x}}`
- **Document parameters**: Clearly describe each variable
- **Set sensible defaults**: Choose appropriate model and depth

### 2. Variable Naming

```python
# Good
variables = {
    "article_title": "The Future of AI",
    "publication_date": "2024-01-15",
    "author_name": "John Doe"
}

# Bad
variables = {
    "x": "The Future of AI",
    "y": "2024-01-15",
    "z": "John Doe"
}
```

### 3. Error Handling

```python
try:
    task = await template_engine.execute_template(
        db=db,
        user_id=user_id,
        template=template,
        variables=variables
    )
except TemplateValidationError as e:
    print(f"Invalid variables: {e}")
except ValueError as e:
    print(f"Budget or constraint error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### 4. Cost Optimization

```python
# Preview cost before execution
preview = template_engine.preview_template(template, variables)

if preview["estimated_cost"] > user_budget:
    print("Cost exceeds budget, using quick mode")
    task = await template_engine.execute_template(
        db=db,
        user_id=user_id,
        template=template,
        variables=variables,
        depth="quick"  # Override to lower tier
    )
```

### 5. Batch Processing

```python
# Process in chunks for large batches
chunk_size = 10
for i in range(0, len(variable_sets), chunk_size):
    chunk = variable_sets[i:i + chunk_size]
    tasks = await template_engine.batch_execute(
        db=db,
        user_id=user_id,
        template=template,
        variable_sets=chunk
    )
    # Wait between chunks to avoid rate limits
    await asyncio.sleep(5)
```

## Troubleshooting

### Missing Required Variables

```
Error: Missing required variables: domain, timeframe
```

**Solution**: Check template metadata and provide all required variables

```python
metadata = template_engine.parse_template(template.query_template)
print(f"Required: {metadata['required_variables']}")
```

### Invalid Template Syntax

```
Error: Template substitution failed
```

**Solution**: Verify template uses correct syntax (`{{variable}}`, not `{variable}`)

### Budget Exceeded

```
Error: Daily cost limit exceeded
```

**Solution**: Use lower-cost tiers or enable caching

```python
task = await template_engine.execute_template(
    db=db,
    user_id=user_id,
    template=template,
    variables=variables,
    depth="quick"  # Use cheaper tier
)
```

## Advanced Examples

### Dynamic Template Generation

```python
def create_research_template(topic: str, aspects: List[str]) -> str:
    """Generate template query for multiple aspects."""
    aspect_prompts = "\n".join([
        f"{{{{#if {aspect}}}}}Analyze {{aspect}}: {{{{{aspect}}}}}{{{{/if}}}}"
        for aspect in aspects
    ])

    return f"""
Research comprehensive analysis of {{{{topic}}}}:

{aspect_prompts}

Provide detailed findings with citations.
    """

template_query = create_research_template(
    topic="AI",
    aspects=["ethics", "applications", "challenges"]
)
```

### Multi-Language Support

```python
template = ResearchTemplate(
    user_id=1,
    name="Multilingual Research",
    query_template="""
{{#if language}}
Research {{topic}} and provide results in {{language}}.
{{else}}
Research {{topic}}.
{{/if}}
    """,
    parameters={
        "topic": "Research topic",
        "language": "(Optional) Target language"
    }
)

# English (default)
variables = {"topic": "Quantum Computing", "language": ""}

# German
variables = {"topic": "Quantum Computing", "language": "German"}
```

## Performance Tips

1. **Use caching**: Results are automatically cached when enabled
2. **Batch related queries**: Use batch processing for efficiency
3. **Schedule off-peak**: Schedule heavy workloads during low-traffic periods
4. **Monitor usage**: Track template usage to optimize frequently-used templates
5. **Optimize prompts**: Shorter, focused prompts reduce token usage and cost

## Support

For issues or questions:
- Check logs: `/var/log/research-service/template_engine.log`
- Review test cases: `tests/services/test_template_engine.py`
- Contact: research-service-team@example.com
