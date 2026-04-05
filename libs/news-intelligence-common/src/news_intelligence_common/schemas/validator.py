"""Event schema validation utilities."""

from typing import Any, Dict, List, Optional, Tuple

try:
    from jsonschema import Draft7Validator, ValidationError

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

    class Draft7Validator:  # type: ignore[no-redef]
        """Stub for when jsonschema is not installed."""

        def __init__(self, schema: Dict[str, Any]) -> None:
            pass

        def iter_errors(self, data: Dict[str, Any]) -> List[Any]:
            return []

    class ValidationError(Exception):  # type: ignore[no-redef]
        """Stub for ValidationError."""

        pass


from news_intelligence_common.event_envelope import EVENT_ENVELOPE_SCHEMA
from news_intelligence_common.schemas.event_schemas import EVENT_PAYLOAD_SCHEMAS


class EventValidator:
    """
    Validates events against JSON schemas.

    Supports two modes:
    - Strict: Raises exception on validation failure
    - Graceful: Returns validation result without raising

    Example:
        >>> validator = EventValidator()
        >>> envelope = {"event_type": "article.created", "payload": {...}}
        >>> is_valid, errors = validator.validate(envelope)
    """

    def __init__(self, strict: bool = False) -> None:
        """
        Initialize validator.

        Args:
            strict: If True, raise exceptions on validation failure
        """
        self.strict = strict
        self._envelope_validator: Optional[Draft7Validator] = None
        self._payload_validators: Dict[str, Draft7Validator] = {}

        if HAS_JSONSCHEMA:
            self._envelope_validator = Draft7Validator(EVENT_ENVELOPE_SCHEMA)
            for event_type, schema in EVENT_PAYLOAD_SCHEMAS.items():
                self._payload_validators[event_type] = Draft7Validator(schema)

    def validate_envelope(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate event envelope structure.

        Args:
            data: Event data to validate

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        if not HAS_JSONSCHEMA:
            # Graceful degradation: basic field check
            required = ["event_id", "event_type", "payload"]
            missing = [f for f in required if f not in data]
            if missing:
                return False, [f"Missing required fields: {missing}"]
            return True, []

        if self._envelope_validator is None:
            return True, []

        errors: List[str] = []
        for error in self._envelope_validator.iter_errors(data):
            errors.append(f"{error.json_path}: {error.message}")

        if errors and self.strict:
            raise ValidationError(f"Envelope validation failed: {errors}")

        return len(errors) == 0, errors

    def validate_payload(
        self, event_type: str, payload: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate event payload against schema for event type.

        Args:
            event_type: The event type (e.g., "article.created")
            payload: The payload data to validate

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        if event_type not in EVENT_PAYLOAD_SCHEMAS:
            # Unknown event type - graceful pass
            return True, []

        if not HAS_JSONSCHEMA:
            return True, []

        validator = self._payload_validators.get(event_type)
        if not validator:
            return True, []

        errors: List[str] = []
        for error in validator.iter_errors(payload):
            errors.append(f"{error.json_path}: {error.message}")

        if errors and self.strict:
            raise ValidationError(f"Payload validation failed for {event_type}: {errors}")

        return len(errors) == 0, errors

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate complete event (envelope + payload).

        Args:
            data: Complete event data

        Returns:
            Tuple of (is_valid, list of all error messages)
        """
        all_errors: List[str] = []

        # Validate envelope
        env_valid, env_errors = self.validate_envelope(data)
        all_errors.extend(env_errors)

        # Validate payload if envelope valid
        if env_valid and "event_type" in data and "payload" in data:
            _, payload_errors = self.validate_payload(
                data["event_type"], data["payload"]
            )
            all_errors.extend(payload_errors)

        return len(all_errors) == 0, all_errors


def validate_event(data: Dict[str, Any], strict: bool = False) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate an event.

    Args:
        data: Event data to validate
        strict: If True, raise exception on failure

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    validator = EventValidator(strict=strict)
    return validator.validate(data)
