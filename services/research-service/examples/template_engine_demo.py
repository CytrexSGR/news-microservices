"""
Template Engine Demo Script

This script demonstrates the key features of the template engine.
Run with: python examples/template_engine_demo.py
"""

import asyncio
from datetime import datetime, timedelta

# Mock database and models for demo
class MockDB:
    def add(self, obj): pass
    def commit(self): pass
    def refresh(self, obj): pass
    def query(self, model): return MockQuery()

class MockQuery:
    def filter(self, *args): return self
    def first(self): return None
    def all(self): return []
    def count(self): return 0

class MockTemplate:
    def __init__(self, query_template, **kwargs):
        self.id = 1
        self.name = kwargs.get("name", "Test Template")
        self.query_template = query_template
        self.parameters = kwargs.get("parameters", {})
        self.default_model = kwargs.get("default_model", "sonar")
        self.default_depth = kwargs.get("default_depth", "standard")
        self.usage_count = 0
        self.last_used_at = None


def demo_parse_template():
    """Demo 1: Template Parsing"""
    from app.services.template_engine import TemplateEngine

    print("=" * 80)
    print("Demo 1: Template Parsing")
    print("=" * 80)

    engine = TemplateEngine()

    # Simple template
    template1 = "Research {{topic}} in {{domain}}"
    metadata1 = engine.parse_template(template1)

    print(f"\nTemplate: {template1}")
    print(f"Variables: {metadata1['variables']}")
    print(f"Required: {metadata1['required_variables']}")
    print(f"Optional: {metadata1['optional_variables']}")

    # Template with conditionals
    template2 = """Research {{topic}} in {{domain}}
{{#if timeframe}}from {{timeframe}}{{/if}}
{{#if deep_mode}}with deep analysis{{else}}with quick overview{{/if}}"""

    metadata2 = engine.parse_template(template2)

    print(f"\nTemplate: {template2}")
    print(f"Variables: {metadata2['variables']}")
    print(f"Required: {metadata2['required_variables']}")
    print(f"Optional: {metadata2['optional_variables']}")
    print(f"Has conditionals: {metadata2['has_conditionals']}")


def demo_variable_substitution():
    """Demo 2: Variable Substitution"""
    from app.services.template_engine import TemplateEngine

    print("\n" + "=" * 80)
    print("Demo 2: Variable Substitution")
    print("=" * 80)

    engine = TemplateEngine()

    # Simple substitution
    template = "Research {{topic}} in {{domain}}"
    variables = {"topic": "Artificial Intelligence", "domain": "healthcare"}
    result = engine.substitute_variables(template, variables)

    print(f"\nTemplate: {template}")
    print(f"Variables: {variables}")
    print(f"Result: {result}")

    # With conditionals
    template2 = """Research {{topic}}{{#if timeframe}} from {{timeframe}}{{/if}}"""

    # With timeframe
    variables2a = {"topic": "AI", "timeframe": "2024"}
    result2a = engine.substitute_variables(template2, variables2a)

    print(f"\nTemplate: {template2}")
    print(f"Variables (with timeframe): {variables2a}")
    print(f"Result: {result2a}")

    # Without timeframe
    variables2b = {"topic": "AI", "timeframe": ""}
    result2b = engine.substitute_variables(template2, variables2b)

    print(f"Variables (without timeframe): {variables2b}")
    print(f"Result: {result2b}")

    # If/else
    template3 = "{{#if premium}}Deep analysis{{else}}Quick overview{{/if}} of {{topic}}"

    variables3a = {"premium": "yes", "topic": "Blockchain"}
    result3a = engine.substitute_variables(template3, variables3a)

    print(f"\nTemplate: {template3}")
    print(f"Variables (premium): {variables3a}")
    print(f"Result: {result3a}")

    variables3b = {"premium": "", "topic": "Blockchain"}
    result3b = engine.substitute_variables(template3, variables3b)

    print(f"Variables (not premium): {variables3b}")
    print(f"Result: {result3b}")


def demo_validation():
    """Demo 3: Parameter Validation"""
    from app.services.template_engine import TemplateEngine

    print("\n" + "=" * 80)
    print("Demo 3: Parameter Validation")
    print("=" * 80)

    engine = TemplateEngine()

    template = MockTemplate(
        query_template="Research {{topic}} in {{domain}}{{#if year}} in {{year}}{{/if}}",
        name="Tech Research"
    )

    # Valid parameters
    variables1 = {"topic": "AI", "domain": "healthcare", "year": "2024"}
    is_valid1, error1 = engine.validate_parameters(template, variables1)

    print(f"\nVariables: {variables1}")
    print(f"Valid: {is_valid1}, Error: {error1}")

    # Valid (without optional)
    variables2 = {"topic": "AI", "domain": "healthcare"}
    is_valid2, error2 = engine.validate_parameters(template, variables2)

    print(f"\nVariables: {variables2}")
    print(f"Valid: {is_valid2}, Error: {error2}")

    # Invalid (missing required)
    variables3 = {"topic": "AI"}
    is_valid3, error3 = engine.validate_parameters(template, variables3)

    print(f"\nVariables: {variables3}")
    print(f"Valid: {is_valid3}, Error: {error3}")


def demo_preview():
    """Demo 4: Template Preview"""
    from app.services.template_engine import TemplateEngine

    print("\n" + "=" * 80)
    print("Demo 4: Template Preview")
    print("=" * 80)

    engine = TemplateEngine()

    template = MockTemplate(
        query_template="Analyze {{topic}} trends in {{industry}}{{#if region}} in {{region}}{{/if}}",
        name="Trend Analysis",
        default_model="sonar-pro",
        default_depth="deep"
    )

    # Valid preview
    variables1 = {"topic": "AI", "industry": "technology", "region": "Europe"}

    # Mock settings for cost calculation
    import app.services.template_engine as te_module

    class MockSettings:
        @staticmethod
        def calculate_cost(tokens, model):
            return tokens * 0.001

    original_settings = te_module.settings
    te_module.settings = MockSettings()

    try:
        preview1 = engine.preview_template(template, variables1)

        print(f"\nTemplate: {template.name}")
        print(f"Variables: {variables1}")
        print(f"Valid: {preview1['is_valid']}")
        print(f"Rendered: {preview1['rendered_query']}")
        print(f"Estimated tokens: {preview1['estimated_tokens']}")
        print(f"Estimated cost: ${preview1['estimated_cost']:.4f}")
        print(f"Model: {preview1['model']}")
        print(f"Depth: {preview1['depth']}")

        # Invalid preview
        variables2 = {"topic": "AI"}  # Missing 'industry'
        preview2 = engine.preview_template(template, variables2)

        print(f"\nVariables: {variables2}")
        print(f"Valid: {preview2['is_valid']}")
        print(f"Error: {preview2['error']}")

    finally:
        te_module.settings = original_settings


def demo_patterns():
    """Demo 5: Pre-built Patterns"""
    from app.services.template_engine import TemplateEngine

    print("\n" + "=" * 80)
    print("Demo 5: Pre-built Patterns")
    print("=" * 80)

    engine = TemplateEngine()

    patterns = [
        ("feed_analysis", {"topic": "Technology", "feed_name": "TechCrunch"}),
        ("article_summary", {"article_title": "The Future of AI"}),
        ("trend_detection", {"domain": "Artificial Intelligence"}),
        ("fact_check", {"claim": "AI will replace all jobs by 2030"})
    ]

    for pattern_name, context in patterns:
        print(f"\nPattern: {pattern_name}")
        print(f"Context: {context}")

        # Would create template in real usage
        print(f"  → Creates template with appropriate query structure")
        print(f"  → Example usage: Execute with context variables")


def demo_batch_processing():
    """Demo 6: Batch Processing Concept"""
    print("\n" + "=" * 80)
    print("Demo 6: Batch Processing Concept")
    print("=" * 80)

    print("\nBatch processing allows executing a template with multiple variable sets:")

    template_name = "Multi-topic Analysis"
    variable_sets = [
        {"topic": "AI", "domain": "healthcare"},
        {"topic": "Blockchain", "domain": "finance"},
        {"topic": "Quantum Computing", "domain": "cryptography"},
        {"topic": "IoT", "domain": "manufacturing"},
        {"topic": "5G", "domain": "telecommunications"}
    ]

    print(f"\nTemplate: {template_name}")
    print(f"Variable sets: {len(variable_sets)}")

    for i, variables in enumerate(variable_sets, 1):
        print(f"  {i}. {variables}")

    print("\n→ Would create 5 research tasks in parallel")
    print("→ Each task uses the same template with different variables")
    print("→ Results can be aggregated for comprehensive analysis")


def demo_scheduled_execution():
    """Demo 7: Scheduled Execution Concept"""
    print("\n" + "=" * 80)
    print("Demo 7: Scheduled Execution Concept")
    print("=" * 80)

    now = datetime.utcnow()
    schedules = [
        (now + timedelta(hours=1), "1 hour from now"),
        (now + timedelta(days=1), "tomorrow"),
        (now + timedelta(weeks=1), "next week")
    ]

    print("\nTemplates can be scheduled for future execution:")

    for schedule_time, label in schedules:
        print(f"\n  Schedule at {schedule_time.strftime('%Y-%m-%d %H:%M:%S')} ({label})")
        print(f"  → Celery task created with ETA")
        print(f"  → Executes automatically at scheduled time")
        print(f"  → Results stored in database")


def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print("TEMPLATE ENGINE DEMONSTRATION")
    print("=" * 80)

    try:
        demo_parse_template()
        demo_variable_substitution()
        demo_validation()
        demo_preview()
        demo_patterns()
        demo_batch_processing()
        demo_scheduled_execution()

        print("\n" + "=" * 80)
        print("All demos completed successfully!")
        print("=" * 80)
        print("\nFor full documentation, see:")
        print("  - docs/template_engine_usage.md")
        print("  - docs/TEMPLATE_ENGINE_IMPLEMENTATION.md")
        print("\nFor tests, run:")
        print("  pytest tests/services/test_template_engine.py -v")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\nError running demos: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
