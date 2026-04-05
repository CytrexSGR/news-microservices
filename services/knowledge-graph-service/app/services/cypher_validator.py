"""
Cypher Syntax Validator

Validates Cypher query syntax BEFORE execution to prevent runtime errors.
This is different from query_validator.py which validates security (read-only).

Key validations:
- MERGE + ON CREATE SET pattern correctness
- ON MATCH SET ordering
- Common syntax errors that cause retry storms

Post-Incident #18 implementation: Prevents Cypher syntax errors from
causing infinite retry loops in RabbitMQ consumers.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class CypherSyntaxError(Exception):
    """
    Raised when Cypher query fails syntax validation.

    This is a non-retriable error - retrying the same query will fail again.
    Messages should be moved to DLQ, not requeued.
    """

    def __init__(self, message: str, errors: List[str], query_preview: str = ""):
        self.errors = errors
        self.query_preview = query_preview
        super().__init__(message)


@dataclass
class ValidationResult:
    """Result of Cypher syntax validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    query_type: str  # 'read', 'write', 'mixed'


class CypherSyntaxValidator:
    """
    Validates Cypher query syntax for correctness.

    Focuses on patterns that cause runtime errors, particularly:
    - MERGE + ON CREATE/MATCH SET ordering (Incident #18 root cause)
    - Balanced parentheses and brackets
    - Required clause structure
    """

    # Pattern for MERGE statements
    MERGE_PATTERN = re.compile(r'\bMERGE\s*\(', re.IGNORECASE)

    # Pattern for ON CREATE SET (must come after MERGE, before standalone SET)
    ON_CREATE_SET_PATTERN = re.compile(r'\bON\s+CREATE\s+SET\b', re.IGNORECASE)

    # Pattern for ON MATCH SET
    ON_MATCH_SET_PATTERN = re.compile(r'\bON\s+MATCH\s+SET\b', re.IGNORECASE)

    # Pattern for standalone SET - we'll filter out ON CREATE/MATCH SET matches later
    # Note: Python lookbehind requires fixed-width patterns, so we use a simpler approach
    SET_PATTERN = re.compile(r'\bSET\b', re.IGNORECASE)

    # Write operation keywords
    WRITE_KEYWORDS = ['CREATE', 'MERGE', 'DELETE', 'SET', 'REMOVE', 'DETACH']

    def __init__(self):
        """Initialize validator."""
        self._validation_count = 0
        self._error_count = 0

    def validate(self, query: str) -> ValidationResult:
        """
        Validate Cypher query syntax.

        Args:
            query: Cypher query string

        Returns:
            ValidationResult with errors and warnings
        """
        self._validation_count += 1
        errors = []
        warnings = []

        # Determine query type
        query_type = self._detect_query_type(query)

        # 1. Check balanced brackets
        bracket_errors = self._check_balanced_brackets(query)
        errors.extend(bracket_errors)

        # 2. Check MERGE + ON CREATE/MATCH SET pattern (critical - Incident #18)
        merge_errors = self._validate_merge_pattern(query)
        errors.extend(merge_errors)

        # 3. Check for common mistakes
        common_warnings = self._check_common_mistakes(query)
        warnings.extend(common_warnings)

        # 4. Check for empty query
        if not query.strip():
            errors.append("Query is empty")

        is_valid = len(errors) == 0

        if not is_valid:
            self._error_count += 1
            logger.warning(
                f"Cypher validation failed: {len(errors)} errors",
                extra={
                    "errors": errors,
                    "query_preview": query[:200] if len(query) > 200 else query
                }
            )

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            query_type=query_type
        )

    def _detect_query_type(self, query: str) -> str:
        """Detect if query is read, write, or mixed."""
        has_write = any(
            re.search(rf'\b{kw}\b', query, re.IGNORECASE)
            for kw in self.WRITE_KEYWORDS
        )
        has_read = re.search(r'\bMATCH\b', query, re.IGNORECASE) is not None

        if has_write and has_read:
            return 'mixed'
        elif has_write:
            return 'write'
        else:
            return 'read'

    def _check_balanced_brackets(self, query: str) -> List[str]:
        """Check for balanced parentheses, brackets, and braces."""
        errors = []

        # Count brackets
        brackets = {
            '(': ')',
            '[': ']',
            '{': '}'
        }

        for open_b, close_b in brackets.items():
            open_count = query.count(open_b)
            close_count = query.count(close_b)

            if open_count != close_count:
                errors.append(
                    f"Unbalanced {open_b}{close_b}: "
                    f"{open_count} opening, {close_count} closing"
                )

        return errors

    def _validate_merge_pattern(self, query: str) -> List[str]:
        """
        Validate MERGE + ON CREATE/MATCH SET pattern.

        Correct pattern:
            MERGE (n:Label {prop: $val})
            ON CREATE SET n.created = datetime()
            ON MATCH SET n.updated = datetime()
            SET n.otherProp = $other

        WRONG pattern (causes Incident #18):
            MERGE (n:Label {prop: $val})
            SET n.otherProp = $other
            ON CREATE SET n.created = datetime()  <-- ERROR: ON CREATE after SET

        Returns:
            List of errors found
        """
        errors = []

        # Find all MERGE statements
        merges = list(self.MERGE_PATTERN.finditer(query))

        if not merges:
            return errors  # No MERGE, no validation needed

        # Find all ON CREATE SET
        on_creates = list(self.ON_CREATE_SET_PATTERN.finditer(query))

        # Find all ON MATCH SET
        on_matches = list(self.ON_MATCH_SET_PATTERN.finditer(query))

        # Find all standalone SETs
        # This is tricky - we need to find SET that's NOT part of ON CREATE/MATCH SET
        standalone_sets = self._find_standalone_sets(query)

        # Validate ordering for each MERGE block
        for merge in merges:
            merge_pos = merge.start()

            # Find the next MERGE or end of query
            next_merge_pos = len(query)
            for other_merge in merges:
                if other_merge.start() > merge_pos:
                    next_merge_pos = min(next_merge_pos, other_merge.start())
                    break

            # Get positions within this MERGE block
            block_on_creates = [
                oc.start() for oc in on_creates
                if merge_pos < oc.start() < next_merge_pos
            ]
            block_on_matches = [
                om.start() for om in on_matches
                if merge_pos < om.start() < next_merge_pos
            ]
            block_sets = [
                s for s in standalone_sets
                if merge_pos < s < next_merge_pos
            ]

            # Check: ON CREATE SET should come BEFORE standalone SET
            for oc_pos in block_on_creates:
                for set_pos in block_sets:
                    if set_pos < oc_pos:
                        errors.append(
                            f"ON CREATE SET found AFTER standalone SET at position {oc_pos}. "
                            f"ON CREATE SET must come immediately after MERGE, before SET."
                        )

            # Check: ON MATCH SET should come BEFORE standalone SET
            for om_pos in block_on_matches:
                for set_pos in block_sets:
                    if set_pos < om_pos:
                        errors.append(
                            f"ON MATCH SET found AFTER standalone SET at position {om_pos}. "
                            f"ON MATCH SET must come immediately after MERGE/ON CREATE, before SET."
                        )

        return errors

    def _find_standalone_sets(self, query: str) -> List[int]:
        """
        Find positions of standalone SET keywords.

        Excludes SET that's part of ON CREATE SET or ON MATCH SET.
        """
        positions = []

        # Find all SET occurrences
        for match in re.finditer(r'\bSET\b', query, re.IGNORECASE):
            pos = match.start()

            # Check if preceded by ON CREATE or ON MATCH
            prefix = query[max(0, pos-20):pos].upper()

            if 'ON CREATE' in prefix or 'ON MATCH' in prefix:
                continue  # This is ON CREATE SET or ON MATCH SET

            positions.append(pos)

        return positions

    def _check_common_mistakes(self, query: str) -> List[str]:
        """Check for common Cypher mistakes that might not cause errors but are suspicious."""
        warnings = []

        # Warning: Multiple consecutive SETs (might be a mistake)
        if re.search(r'\bSET\b.*\bSET\b.*\bSET\b', query, re.IGNORECASE):
            warnings.append(
                "Multiple SET clauses found. Consider combining into single SET."
            )

        # Warning: DETACH DELETE without MATCH
        if 'DETACH DELETE' in query.upper() and 'MATCH' not in query.upper():
            warnings.append(
                "DETACH DELETE without MATCH - this might delete all nodes!"
            )

        # Warning: CREATE without checking existence
        if 'CREATE' in query.upper() and 'MERGE' not in query.upper():
            if 'IF NOT EXISTS' not in query.upper():
                warnings.append(
                    "Using CREATE without MERGE may create duplicates. "
                    "Consider using MERGE for idempotent operations."
                )

        return warnings

    def validate_before_execution(
        self,
        query: str,
        raise_on_error: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Convenience method for pre-execution validation.

        Args:
            query: Cypher query to validate
            raise_on_error: If True, raise ValueError on validation failure

        Returns:
            Tuple of (is_valid, error_message)

        Raises:
            ValueError: If raise_on_error=True and validation fails
        """
        result = self.validate(query)

        if not result.is_valid:
            error_msg = f"Cypher syntax validation failed: {'; '.join(result.errors)}"

            if raise_on_error:
                raise ValueError(error_msg)

            return False, error_msg

        return True, None

    def get_stats(self) -> Dict:
        """Get validation statistics."""
        return {
            "total_validations": self._validation_count,
            "total_errors": self._error_count,
            "error_rate": (
                self._error_count / self._validation_count
                if self._validation_count > 0 else 0
            )
        }


# Global validator instance
cypher_validator = CypherSyntaxValidator()


def validate_cypher_syntax(query: str, raise_on_error: bool = False) -> ValidationResult:
    """
    Validate Cypher query syntax.

    Convenience function using global validator.

    Args:
        query: Cypher query to validate
        raise_on_error: If True, raise CypherSyntaxError on validation failure

    Returns:
        ValidationResult

    Raises:
        CypherSyntaxError: If raise_on_error=True and validation fails

    Example:
        result = validate_cypher_syntax('''
            MERGE (c:Company {symbol: $symbol})
            ON CREATE SET c.created_at = datetime()
            SET c.name = $name
        ''')

        if not result.is_valid:
            print(f"Errors: {result.errors}")
    """
    result = cypher_validator.validate(query)

    if raise_on_error and not result.is_valid:
        query_preview = query[:200] if len(query) > 200 else query
        raise CypherSyntaxError(
            message=f"Cypher validation failed: {'; '.join(result.errors)}",
            errors=result.errors,
            query_preview=query_preview
        )

    return result
