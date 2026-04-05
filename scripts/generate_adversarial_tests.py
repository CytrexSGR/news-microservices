#!/usr/bin/env python3
"""
Adversarial Test-Set Generator

Orchestrates the Red Team Agent to generate challenging test cases
with comprehensive Ground Truth 2.0 solutions.

Usage:
    python generate_adversarial_tests.py --count 10 --challenge-type factual_error
    python generate_adversarial_tests.py --batch-mode --all-types
"""

import argparse
import json
import logging
import sys
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI
from pydantic import ValidationError

from models.adversarial_test_case import (
    AdversarialTestCase,
    ChallengeType,
    RED_TEAM_SYSTEM_PROMPT
)

# ============================================================================
# Configuration
# ============================================================================

OUTPUT_DIR = Path(__file__).parent.parent / "tests" / "adversarial-data"
LOG_DIR = Path(__file__).parent.parent / "logs"

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"adversarial_gen_{datetime.now():%Y%m%d_%H%M%S}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# Red Team Agent
# ============================================================================

class RedTeamAgent:
    """
    Red Team AI Agent for generating adversarial test cases.
    """

    def __init__(self, model: str = "gpt-4-turbo-preview"):
        """
        Initialize Red Team Agent.

        Args:
            model: OpenAI model to use
        """
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Please set it to use the Red Team Agent."
            )

        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.generation_count = 0

    def generate_test_case(
        self,
        challenge_type: Optional[ChallengeType] = None,
        difficulty_level: Optional[int] = None
    ) -> AdversarialTestCase:
        """
        Generate a single adversarial test case.

        Args:
            challenge_type: Specific challenge type to generate (optional)
            difficulty_level: Target difficulty 1-5 (optional)

        Returns:
            AdversarialTestCase with article and ground truth

        Raises:
            ValueError: If generation or validation fails
        """
        # Build user prompt
        user_prompt = "Generate a challenging test case"
        if challenge_type:
            user_prompt += f" with challenge type: {challenge_type.value}"
        if difficulty_level:
            user_prompt += f" at difficulty level {difficulty_level}/5"
        user_prompt += "."

        logger.info(f"Generating test case: {user_prompt}")

        try:
            # Call Red Team Agent (LLM)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": RED_TEAM_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.8,  # Higher creativity for adversarial cases
                max_tokens=4000
            )

            # Parse response
            raw_content = response.choices[0].message.content
            logger.debug(f"Raw LLM response: {raw_content[:200]}...")

            raw_json = json.loads(raw_content)

            # Generate test case ID before validation
            self.generation_count += 1
            if "ground_truth" in raw_json and "challenge_type" in raw_json["ground_truth"]:
                challenge_type_value = raw_json["ground_truth"]["challenge_type"]
                test_case_id = f"{challenge_type_value}_{self.generation_count:03d}"
            else:
                test_case_id = f"unknown_{self.generation_count:03d}"

            # Add test_case_id to JSON
            raw_json["test_case_id"] = test_case_id

            # Validate with Pydantic
            test_case = AdversarialTestCase(**raw_json)

            logger.info(f"✅ Generated: {test_case.test_case_id}")
            return test_case

        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON from Red Team Agent: {e}")
            logger.error(f"Response content: {raw_content}")
            raise ValueError(f"Failed to parse JSON: {e}")
        except ValidationError as e:
            logger.error(f"❌ Validation failed: {e}")
            logger.error(f"Raw JSON keys: {list(raw_json.keys())}")
            raise ValueError(f"Pydantic validation failed: {e}")
        except Exception as e:
            logger.error(f"❌ Generation failed: {e}")
            raise ValueError(f"Unexpected error: {e}")

    def generate_batch(
        self,
        count: int,
        challenge_types: Optional[List[ChallengeType]] = None,
        difficulty_range: tuple[int, int] = (2, 4)
    ) -> List[AdversarialTestCase]:
        """
        Generate multiple test cases in batch.

        Args:
            count: Number of test cases to generate
            challenge_types: List of challenge types to sample from
            difficulty_range: (min, max) difficulty levels

        Returns:
            List of generated test cases
        """
        import random

        if challenge_types is None:
            challenge_types = list(ChallengeType)

        test_cases = []

        for i in range(count):
            # Randomly select challenge type and difficulty
            challenge_type = random.choice(challenge_types)
            difficulty = random.randint(*difficulty_range)

            try:
                test_case = self.generate_test_case(
                    challenge_type=challenge_type,
                    difficulty_level=difficulty
                )
                test_cases.append(test_case)

                logger.info(
                    f"Progress: {len(test_cases)}/{count} "
                    f"({len(test_cases)/count*100:.1f}%)"
                )

            except Exception as e:
                logger.warning(f"Skipping failed generation {i+1}: {e}")
                continue

        return test_cases


# ============================================================================
# Storage Manager
# ============================================================================

class TestCaseStorage:
    """Manages storage and retrieval of adversarial test cases."""

    def __init__(self, base_dir: Path = OUTPUT_DIR):
        self.base_dir = base_dir
        self.metadata_file = base_dir / "metadata.json"

    def save_test_case(self, test_case: AdversarialTestCase) -> Path:
        """Save test case to disk."""
        output_path = test_case.save_to_file(str(self.base_dir))
        logger.info(f"💾 Saved: {output_path}")

        # Update metadata index
        self._update_metadata(test_case)

        return output_path

    def _update_metadata(self, test_case: AdversarialTestCase):
        """Update metadata index."""
        # Load existing metadata
        if self.metadata_file.exists():
            with open(self.metadata_file) as f:
                metadata = json.load(f)
        else:
            metadata = {"test_cases": [], "statistics": {}}

        # Add new test case entry
        metadata["test_cases"].append({
            "test_case_id": test_case.test_case_id,
            "challenge_type": test_case.ground_truth.challenge_type.value,
            "difficulty_level": test_case.ground_truth.difficulty_level,
            "generated_at": test_case.generated_at.isoformat(),
            "file_path": f"{test_case.test_case_id}.json"
        })

        # Update statistics
        stats = metadata["statistics"]
        challenge_type = test_case.ground_truth.challenge_type.value
        stats[challenge_type] = stats.get(challenge_type, 0) + 1
        stats["total_count"] = len(metadata["test_cases"])

        # Save metadata
        with open(self.metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

    def list_test_cases(self) -> List[dict]:
        """List all test cases."""
        if not self.metadata_file.exists():
            return []

        with open(self.metadata_file) as f:
            metadata = json.load(f)

        return metadata["test_cases"]

    def get_statistics(self) -> dict:
        """Get test case statistics."""
        if not self.metadata_file.exists():
            return {}

        with open(self.metadata_file) as f:
            metadata = json.load(f)

        return metadata.get("statistics", {})


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate adversarial test cases for DIA validation"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of test cases to generate"
    )
    parser.add_argument(
        "--challenge-type",
        type=str,
        choices=[ct.value for ct in ChallengeType],
        help="Specific challenge type to generate"
    )
    parser.add_argument(
        "--difficulty",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Target difficulty level (1=Easy, 5=Hard)"
    )
    parser.add_argument(
        "--batch-mode",
        action="store_true",
        help="Generate diverse batch across all types"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4-turbo-preview",
        help="LLM model to use for Red Team Agent"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List existing test cases and exit"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics and exit"
    )

    args = parser.parse_args()

    storage = TestCaseStorage()

    # Handle list/stats commands
    if args.list:
        test_cases = storage.list_test_cases()
        print(f"\n📋 Found {len(test_cases)} test cases:\n")
        for tc in test_cases:
            print(
                f"  • {tc['test_case_id']} "
                f"({tc['challenge_type']}, difficulty {tc['difficulty_level']})"
            )
        return

    if args.stats:
        stats = storage.get_statistics()
        print("\n📊 Test Case Statistics:\n")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        return

    # Generate test cases
    try:
        agent = RedTeamAgent(model=args.model)
    except ValueError as e:
        logger.error(f"Failed to initialize Red Team Agent: {e}")
        print(f"\n❌ Error: {e}\n")
        return 1

    print(f"\n🤖 Red Team Agent initialized (model: {args.model})")
    print(f"📁 Output directory: {OUTPUT_DIR}\n")

    if args.batch_mode:
        print(f"🎯 Batch mode: Generating {args.count} diverse test cases...\n")
        test_cases = agent.generate_batch(count=args.count)
    else:
        print(f"🎯 Generating {args.count} test case(s)...\n")
        challenge_type = ChallengeType(args.challenge_type) if args.challenge_type else None
        test_cases = []

        for i in range(args.count):
            try:
                test_case = agent.generate_test_case(
                    challenge_type=challenge_type,
                    difficulty_level=args.difficulty
                )
                test_cases.append(test_case)
            except Exception as e:
                logger.error(f"Failed to generate test case {i+1}: {e}")
                print(f"❌ Generation {i+1} failed: {e}")

    # Save all test cases
    print("\n💾 Saving test cases...\n")
    for test_case in test_cases:
        try:
            storage.save_test_case(test_case)
        except Exception as e:
            logger.error(f"Failed to save {test_case.test_case_id}: {e}")
            print(f"❌ Save failed for {test_case.test_case_id}: {e}")

    # Final summary
    print(f"\n✅ Successfully generated {len(test_cases)} test cases")
    print(f"📊 Statistics: {storage.get_statistics()}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
