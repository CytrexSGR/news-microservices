# LLM Orchestrator Prompt Library

Reusable, optimized prompt templates categorized by use case.

## Directory Structure

```
prompts/
├── README.md                    # This file
├── analysis/                    # Content analysis prompts
│   ├── root_cause_analysis.md
│   ├── sentiment_analysis.md
│   └── topic_classification.md
├── verification/                # Fact-checking prompts
│   ├── fact_verification.md
│   ├── claim_validation.md
│   └── source_reliability.md
├── extraction/                  # Entity/data extraction
│   ├── entity_extraction.md
│   ├── numerical_data.md
│   └── key_points.md
├── summarization/              # Summarization prompts
│   ├── brief_summary.md
│   ├── detailed_summary.md
│   └── executive_summary.md
└── research/                   # Research/investigation
    ├── deep_research.md
    ├── comparative_analysis.md
    └── trend_analysis.md
```

## Template Format

Each template follows this structure:

```markdown
# [Template Name]

## Use Case
Brief description of when to use this template.

## Model Recommendations
- **Primary**: gpt-4o-mini (fast, cost-effective)
- **Alternative**: gpt-4o (higher accuracy)
- **Fallback**: gpt-3.5-turbo (budget)

## Token Budget
- **Input**: ~1,500 tokens
- **Output**: ~500 tokens
- **Total Cost**: $0.0003 (gpt-4o-mini)

## System Prompt
[system prompt with best practices]

## User Prompt Template
[user prompt with {variables} for interpolation]

## Variables
- `{variable_name}`: Description

## Examples
### Example 1
Input: [sample input]
Output: [expected output]

## Best Practices
- Specific guidelines for this template
- Token optimization tips
- Common pitfalls to avoid
```

## Template Selection Guidelines

### By Task Complexity

**Low Complexity** (gpt-3.5-turbo/gpt-4o-mini)
- Simple classification
- Basic entity extraction
- Short summaries

**Medium Complexity** (gpt-4o-mini)
- Root cause analysis (current Stage 1)
- Verification planning (current Stage 2)
- Detailed extraction

**High Complexity** (gpt-4o)
- Multi-document synthesis
- Complex reasoning chains
- Critical fact-checking

### By Response Time

**Real-time** (< 2s)
- gpt-3.5-turbo
- gpt-4o-mini with max_tokens=500

**Near real-time** (< 5s)
- gpt-4o-mini (default)

**Batch processing** (> 5s acceptable)
- gpt-4o for highest quality

### By Cost

**Budget** ($0.0001/request)
- gpt-3.5-turbo
- Short prompts + low max_tokens

**Balanced** ($0.0003/request)
- gpt-4o-mini (recommended default)

**Premium** ($0.003/request)
- gpt-4o for critical operations

## Token Optimization Strategies

### 1. Prompt Compression
```python
# ❌ Verbose (500 tokens)
"Please analyze the following article carefully and provide a detailed analysis..."

# ✅ Concise (50 tokens)
"Analyze article. Extract: sentiment, entities, key claims."
```

### 2. Output Constraint
```python
# ❌ Unlimited output
response_format={"type": "json_object"}

# ✅ Limited output
response_format={"type": "json_object"}, max_tokens=500
```

### 3. Context Truncation
```python
# ❌ Full article (5000 tokens)
content = article.full_text

# ✅ Smart truncation (2000 tokens)
content = article.title + "\n" + article.summary + "\n" + article.full_text[:1500]
```

### 4. Response Caching
```python
# Cache identical requests for 1 hour
cache_key = f"llm:{prompt_hash}:{model}"
cached = await redis.get(cache_key)
if cached:
    return cached
```

## Cost Tracking

Track costs per template:

```python
from app.utils.cost_tracker import track_llm_cost

@track_llm_cost(template="root_cause_analysis")
async def analyze(content: str):
    response = await client.chat.completions.create(...)
    return response
```

## Version Control

Templates are versioned with metadata:

```json
{
  "template_name": "root_cause_analysis",
  "version": "1.2.0",
  "created": "2024-10-24",
  "last_updated": "2024-11-24",
  "author": "LLM Orchestrator Team",
  "changelog": [
    "v1.2.0: Reduced token usage by 30%",
    "v1.1.0: Improved accuracy for financial claims",
    "v1.0.0: Initial version"
  ]
}
```

## Testing Templates

Each template includes test cases:

```bash
# Test single template
pytest tests/prompts/test_root_cause_analysis.py

# Test all templates
pytest tests/prompts/

# Benchmark performance
python scripts/benchmark_prompts.py --template root_cause_analysis
```

## Contributing New Templates

1. Copy template skeleton: `prompts/_template_skeleton.md`
2. Fill in all sections
3. Add test cases: `tests/prompts/test_[template_name].py`
4. Run benchmarks: `python scripts/benchmark_prompts.py`
5. Update this README with new template

## References

- [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
- [Anthropic Prompt Library](https://docs.anthropic.com/claude/prompt-library)
- [ADR-018: DIA Planner & Verifier](../../docs/decisions/ADR-018-dia-planner-verifier.md)
