"""
Query Validator Service

Validates Cypher queries for security before execution.
Prevents write operations and malicious queries.
"""

import re
import logging
from typing import List, Tuple
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class QueryValidator:
    """
    Validates Cypher queries for security.

    Enforces read-only operations and prevents malicious queries.
    """

    # Forbidden keywords that indicate write operations
    FORBIDDEN_KEYWORDS = [
        'CREATE', 'DELETE', 'SET', 'MERGE', 'DROP',
        'DETACH', 'REMOVE', 'INDEX', 'CONSTRAINT',
        'LOAD', 'CSV', 'CALL', 'FOREACH'
    ]

    # Additional dangerous patterns
    DANGEROUS_PATTERNS = [
        r'CALL\s+dbms',  # Database management procedures
        r'CALL\s+db\.',  # Database procedures
        r';\s*\w+',      # Multiple statements (command injection)
        r'/\*.*?\*/',    # Block comments (obfuscation)
        r'--\s*\w+',     # Line comments with content after
    ]

    # Maximum query length (prevent DoS)
    MAX_QUERY_LENGTH = 10000

    def __init__(self):
        """Initialize query validator."""
        self.forbidden_regex = re.compile(
            r'\b(' + '|'.join(self.FORBIDDEN_KEYWORDS) + r')\b',
            re.IGNORECASE
        )

    def validate(self, query: str) -> Tuple[bool, str]:
        """
        Validate a Cypher query.

        Args:
            query: Cypher query string to validate

        Returns:
            Tuple of (is_valid, error_message)

        Raises:
            HTTPException: If query is invalid
        """
        # 1. Check query length
        if len(query) > self.MAX_QUERY_LENGTH:
            error_msg = f"Query too long ({len(query)} chars). Max: {self.MAX_QUERY_LENGTH}"
            logger.warning(f"Query validation failed: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )

        # 2. Check for forbidden keywords
        matches = self.forbidden_regex.findall(query)
        if matches:
            error_msg = f"Write operations not allowed: {', '.join(set(matches))}"
            logger.warning(f"Query validation failed: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )

        # 3. Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                error_msg = f"Dangerous pattern detected: {pattern}"
                logger.warning(f"Query validation failed: {error_msg}")
                raise HTTPException(
                    status_code=400,
                    detail="Query contains forbidden patterns"
                )

        # 4. Ensure query contains MATCH or RETURN
        if not re.search(r'\b(MATCH|RETURN)\b', query, re.IGNORECASE):
            error_msg = "Query must contain MATCH or RETURN clause"
            logger.warning(f"Query validation failed: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )

        return True, ""

    def get_allowed_clauses(self) -> List[str]:
        """
        Get list of allowed Cypher clauses.

        Returns:
            List of allowed clause keywords
        """
        return [
            'MATCH', 'OPTIONAL MATCH', 'RETURN', 'WITH',
            'WHERE', 'ORDER BY', 'SKIP', 'LIMIT',
            'UNWIND', 'DISTINCT', 'AS', 'count', 'collect'
        ]

    def get_forbidden_clauses(self) -> List[str]:
        """
        Get list of forbidden Cypher clauses.

        Returns:
            List of forbidden clause keywords
        """
        return self.FORBIDDEN_KEYWORDS


# Global validator instance
query_validator = QueryValidator()
