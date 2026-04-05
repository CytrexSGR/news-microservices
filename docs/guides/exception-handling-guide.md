# Exception Handling Developer Guide

**Last Updated:** 2025-10-23
**Applies To:** All microservices (content-analysis-service implemented)
**Status:** Production Standard

---

## Quick Reference

### Pattern at a Glance

```python
from app.core.exceptions import SpecificError, DomainError

try:
    result = await operation()
except SpecificError as e:
    logger.error(f"Specific error: {e}", exc_info=True)
    # Handle or re-raise
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise DomainError(f"Operation failed: {e}") from e
```

### The Three Rules

1. **Catch Specific First:** Most specific exception type first
2. **Always Chain:** Use `from e` when wrapping exceptions
3. **Always Log with Context:** Use `exc_info=True` in `logger.error()`

---

## Exception Hierarchy

### Content-Analysis Service

```
ContentAnalysisError (base - catch this to catch all)
├── LLMProviderError
│   ├── LLMAPIError              # API call failed
│   ├── LLMTimeoutError          # Request timeout
│   ├── LLMValidationError       # Invalid request/response
│   ├── LLMRateLimitError        # Rate limit exceeded
│   └── LLMResponseError         # Invalid response format
├── DatabaseError
│   ├── DatabaseConnectionError  # Connection failed
│   ├── AnalysisNotFoundError    # Record not found
│   └── DatabaseQueryError       # Query execution failed
├── MessageQueueError
│   ├── MessageProcessingError   # Message processing failed
│   ├── MessageDeserializationError  # JSON parsing failed
│   └── MessagePublishError      # Event publishing failed
├── CacheError
│   ├── CacheConnectionError     # Redis connection failed
│   └── CacheKeyError            # Key operation failed
├── ValidationError
│   ├── SchemaValidationError    # Schema validation failed
│   └── ConfigurationError       # Invalid configuration
├── AnalysisError
│   ├── EventAnalysisError       # Event analysis failed
│   ├── ClaimExtractionError     # Claim extraction failed
│   ├── SentimentAnalysisError   # Sentiment analysis failed
│   └── EntityExtractionError    # Entity extraction failed
└── AdminError
    └── AdminAuthorizationError  # Admin auth failed
```

---

## Common Patterns

### Pattern 1: Service Method with LLM Call

**Use Case:** Analysis service methods that call LLM providers

```python
async def analyze_sentiment(
    self,
    content: str,
    article_id: UUID,
    db: Session
) -> SentimentAnalysisResponse:
    """Perform sentiment analysis on content."""
    try:
        # Get LLM provider
        provider = get_llm_provider(analysis_type=AnalysisType.SENTIMENT)

        # Call LLM
        response = await provider.analyze(content)

        # Return result
        return SentimentAnalysisResponse(**response)

    except LLMAPIError as e:
        # LLM API failed - update DB state and re-raise
        logger.error(f"LLM API error during sentiment analysis: {e}", exc_info=True)
        self._mark_analysis_failed(article_id, str(e), db)
        raise  # Let caller decide how to handle

    except DatabaseError as e:
        # Database error - critical, must raise
        logger.error(f"Database error during sentiment analysis: {e}", exc_info=True)
        raise

    except Exception as e:
        # Unexpected error - wrap in domain exception
        logger.error(f"Sentiment analysis failed: {e}", exc_info=True)
        self._mark_analysis_failed(article_id, str(e), db)
        raise SentimentAnalysisError(f"Sentiment analysis failed: {e}") from e
```

**Key Points:**
- Specific exceptions handled differently (LLM vs Database)
- Database state updated before raising (analysis marked failed)
- Generic Exception wrapped in domain-specific `SentimentAnalysisError`
- Exception chaining with `from e` preserves original error

### Pattern 2: Cache Operations with Graceful Degradation

**Use Case:** Redis cache operations that should degrade gracefully

```python
async def get_analysis_cache(
    self,
    content: str,
    analysis_type: AnalysisType
) -> Optional[Dict[str, Any]]:
    """Get cached analysis result (graceful degradation)."""

    # Early return if cache disabled
    if not self.enabled or not self.redis_client:
        return None

    try:
        key = self.generate_cache_key(content, analysis_type)
        value = await self.redis_client.get(key)

        if value:
            logger.debug(f"Cache hit for key: {key}")
            return json.loads(value)

        logger.debug(f"Cache miss for key: {key}")
        return None

    except CacheKeyError as e:
        # Key doesn't exist or parsing failed - degrade gracefully
        logger.error(f"Cache key error: {e}", exc_info=True)
        return None  # Don't raise - cache is optional

    except Exception as e:
        # Unexpected error - wrap and raise
        logger.error(f"Cache get error: {e}", exc_info=True)
        raise CacheError(f"Failed to get cache key {key}: {e}") from e
```

**Key Points:**
- Non-critical errors return None (graceful degradation)
- Critical errors (unexpected) still raise wrapped exceptions
- Debug logging for cache hits/misses
- Early return for disabled cache

### Pattern 3: Worker Message Processing

**Use Case:** RabbitMQ consumer processing with message requeue

```python
async def _process_message(self, message: aio_pika.IncomingMessage):
    """Process article.created event from RabbitMQ."""

    async with message.process():  # Auto-ACK on success, NACK on exception
        try:
            # Deserialize message
            payload = json.loads(message.body.decode())

            # Extract data
            feed_id = payload.get("feed_id")
            item_id = payload.get("item_id")

            logger.info(f"Processing article.created: {item_id} from feed {feed_id}")

            # Call handler
            await self.handler.handle_message(payload)

        except json.JSONDecodeError as e:
            # JSON parsing failed - message is malformed
            logger.error(f"Failed to deserialize article.created event: {e}", exc_info=True)
            raise MessageDeserializationError(f"Invalid JSON: {e}") from e
            # Re-raising causes NACK and message requeue

        except MessageProcessingError as e:
            # Processing failed - transient error, should retry
            logger.error(f"Failed to process article.created event: {e}", exc_info=True)
            raise  # Requeue message

        except Exception as e:
            # Unexpected error - wrap and requeue
            logger.error(f"Error processing article.created event: {e}", exc_info=True)
            raise MessageProcessingError(f"Failed to process event: {e}") from e
```

**Key Points:**
- `async with message.process()` auto-ACKs on success
- Re-raising exceptions causes NACK and message requeue
- JSON errors explicitly wrapped in `MessageDeserializationError`
- Contextual logging with item_id for debugging

### Pattern 4: Admin Health Checks

**Use Case:** Health check operations that should degrade gracefully

```python
async def _check_database_health(self) -> DependencyHealth:
    """Check database connectivity (graceful degradation)."""

    try:
        # Test database connection
        async with SessionLocal() as db:
            await db.execute(text("SELECT 1"))

        # Success
        return DependencyHealth(
            name="Database",
            status=ServiceStatus.HEALTHY,
            message="Connected"
        )

    except DatabaseConnectionError as e:
        # Connection failed - degraded but not critical
        self.logger.error(f"Database connection failed: {e}", exc_info=True)
        return DependencyHealth(
            name="Database",
            status=ServiceStatus.UNHEALTHY,
            message=f"Connection failed: {str(e)}"
        )

    except Exception as e:
        # Unexpected error - wrap but still return degraded state
        self.logger.error(f"Database health check failed: {e}", exc_info=True)
        # Wrap for type safety but don't raise - health check should not crash
        raise DatabaseConnectionError(f"Health check failed: {e}") from e
```

**Key Points:**
- Returns degraded state instead of raising on expected errors
- Still wraps unexpected errors for type safety
- Detailed error messages in response
- Health checks should not crash the admin service

---

## Import Statements

### Standard Imports

```python
# At top of file
from app.core.exceptions import (
    # Database exceptions
    DatabaseError,
    DatabaseConnectionError,
    DatabaseQueryError,
    AnalysisNotFoundError,
    # LLM exceptions
    LLMAPIError,
    LLMTimeoutError,
    # Cache exceptions
    CacheError,
    CacheConnectionError,
    CacheKeyError,
    # Message queue exceptions
    MessageQueueError,
    MessageProcessingError,
    MessageDeserializationError,
    MessagePublishError,
    # Analysis exceptions
    AnalysisError,
    SentimentAnalysisError,
    EntityExtractionError,
    # Config exceptions
    ConfigurationError,
)
```

### Import Only What You Need

```python
# Good - specific imports
from app.core.exceptions import LLMAPIError, DatabaseError

# Avoid - importing everything
from app.core.exceptions import *
```

---

## Logging Best Practices

### Always Use exc_info=True

**Bad:**
```python
except LLMAPIError as e:
    logger.error(f"LLM API failed: {e}")  # ❌ Missing stack trace
```

**Good:**
```python
except LLMAPIError as e:
    logger.error(f"LLM API failed: {e}", exc_info=True)  # ✅ Includes stack trace
```

### Include Context in Messages

**Bad:**
```python
except DatabaseError as e:
    logger.error(f"Error: {e}", exc_info=True)  # ❌ Vague
```

**Good:**
```python
except DatabaseError as e:
    logger.error(
        f"Database error during sentiment analysis for article {article_id}: {e}",
        exc_info=True
    )  # ✅ Specific context
```

### Use Appropriate Log Levels

```python
# Debug - Expected behavior (cache miss, etc.)
logger.debug(f"Cache miss for key: {key}")

# Info - Important events (processing started, completed)
logger.info(f"Processing article {article_id}")

# Warning - Degraded but functioning (cache disabled, etc.)
logger.warning(f"Cache is disabled, skipping cache check")

# Error - Exceptions and failures
logger.error(f"Analysis failed: {e}", exc_info=True)

# Critical - System-level failures
logger.critical(f"Database connection lost, service unusable: {e}", exc_info=True)
```

---

## Exception Chaining

### Always Use 'from e'

**Bad:**
```python
except Exception as e:
    raise DomainError(f"Failed: {e}")  # ❌ Lost original exception
```

**Good:**
```python
except Exception as e:
    raise DomainError(f"Failed: {e}") from e  # ✅ Preserves original exception
```

### Why Exception Chaining Matters

```python
# Without chaining
try:
    result = json.loads(invalid_json)
except json.JSONDecodeError as e:
    raise MessageDeserializationError("Parsing failed")
    # ❌ Original JSONDecodeError lost - can't see what was invalid

# With chaining
try:
    result = json.loads(invalid_json)
except json.JSONDecodeError as e:
    raise MessageDeserializationError(f"Parsing failed: {e}") from e
    # ✅ Full stack trace: MessageDeserializationError -> JSONDecodeError
    #    Can see exact JSON parsing error
```

---

## When to Raise vs. Return

### Raise for Programming Errors

```python
def process_analysis(analysis_id: str):
    if not analysis_id:
        raise ValidationError("analysis_id is required")  # ✅ Raise - programming error
```

### Return for Expected Failures

```python
async def get_cached_result(key: str) -> Optional[Dict]:
    try:
        return await cache.get(key)
    except CacheKeyError:
        return None  # ✅ Return None - expected (key doesn't exist)
```

### Raise for Unexpected Failures

```python
async def get_cached_result(key: str) -> Optional[Dict]:
    try:
        return await cache.get(key)
    except CacheConnectionError:
        raise  # ✅ Raise - unexpected (Redis down)
```

---

## Testing Exception Handling

### Test That Exceptions Are Raised

```python
def test_analysis_raises_llm_error(sync_db_session):
    """Test that LLMAPIError is raised on LLM failure."""
    service = AnalysisService()

    # Mock LLM to raise error
    with patch('app.services.analysis_service.get_llm_provider') as mock_llm:
        mock_llm.return_value.analyze = Mock(side_effect=LLMAPIError("API timeout"))

        # Verify exception is raised
        with pytest.raises(LLMAPIError) as exc_info:
            service.analyze_sentiment(content="test", article_id=uuid4(), db=sync_db_session)

        # Verify exception message
        assert "API timeout" in str(exc_info.value)
```

### Test Exception Chaining

```python
def test_exception_chaining_preserves_original():
    """Test that exception chaining preserves original error."""
    service = CacheService()

    original_error = ConnectionError("Redis connection refused")

    with patch.object(service.redis_client, 'get', side_effect=original_error):
        with pytest.raises(CacheError) as exc_info:
            await service.get("key")

        # Verify chaining
        assert exc_info.value.__cause__ is original_error
        assert isinstance(exc_info.value.__cause__, ConnectionError)
```

### Test Logging with exc_info

```python
def test_logging_includes_exc_info():
    """Test that errors are logged with exc_info=True."""
    service = CacheService()

    with patch('app.services.cache_service.logger') as mock_logger:
        with patch.object(service.redis_client, 'get', side_effect=Exception("Error")):
            try:
                await service.get("key")
            except CacheError:
                pass

            # Verify logger.error called with exc_info=True
            mock_logger.error.assert_called()
            call_kwargs = mock_logger.error.call_args[1]
            assert call_kwargs.get('exc_info') is True
```

---

## Anti-Patterns to Avoid

### ❌ Bare Exception Without Chaining

```python
# BAD
try:
    result = operation()
except Exception as e:
    logger.error(f"Failed: {e}")
    raise AnalysisError("Operation failed")  # ❌ Lost original exception
```

```python
# GOOD
try:
    result = operation()
except Exception as e:
    logger.error(f"Failed: {e}", exc_info=True)
    raise AnalysisError(f"Operation failed: {e}") from e  # ✅ Preserved
```

### ❌ Silent Failures

```python
# BAD
try:
    result = critical_operation()
except Exception as e:
    logger.error(f"Error: {e}")
    return None  # ❌ Critical error silently ignored
```

```python
# GOOD
try:
    result = critical_operation()
except Exception as e:
    logger.error(f"Critical operation failed: {e}", exc_info=True)
    raise CriticalError(f"Critical operation failed: {e}") from e  # ✅ Raised
```

### ❌ Missing exc_info=True

```python
# BAD
except Exception as e:
    logger.error(f"Error: {e}")  # ❌ No stack trace
```

```python
# GOOD
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)  # ✅ Full stack trace
```

### ❌ Catching Too Broad

```python
# BAD
try:
    result = operation()
except Exception:  # ❌ Catches EVERYTHING, even KeyboardInterrupt
    return None
```

```python
# GOOD
try:
    result = operation()
except (LLMAPIError, DatabaseError) as e:  # ✅ Specific exceptions
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise
except Exception as e:  # ✅ Fallback with wrapping
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise OperationError(f"Operation failed: {e}") from e
```

### ❌ Swallowing Exceptions in Workers

```python
# BAD
async def _process_message(self, message):
    try:
        await self.handler.handle(message)
    except Exception as e:
        logger.error(f"Error: {e}")
        # ❌ Exception swallowed - message ACKed even on failure
```

```python
# GOOD
async def _process_message(self, message):
    async with message.process():  # Auto-ACK on success, NACK on exception
        try:
            await self.handler.handle(message)
        except MessageProcessingError as e:
            logger.error(f"Processing failed: {e}", exc_info=True)
            raise  # ✅ Re-raised - message NACKed and requeued
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise MessageProcessingError(f"Processing failed: {e}") from e
```

---

## Migration Guide

### Step 1: Identify Bare Exceptions

```bash
# Find all bare exceptions in a file
grep -n "except Exception" file.py

# Find all files with bare exceptions
grep -r "except Exception" app/ --include="*.py"
```

### Step 2: Determine Exception Type

Ask yourself:
1. **What operation failed?** (database, cache, LLM, etc.)
2. **What specific failure?** (connection, query, timeout, etc.)
3. **Should this degrade gracefully or raise?**

### Step 3: Add Import

```python
from app.core.exceptions import SpecificError, DomainError
```

### Step 4: Replace Exception Handler

**Before:**
```python
try:
    result = await redis_client.get(key)
except Exception as e:
    logger.error(f"Error: {e}")
    return None
```

**After:**
```python
try:
    result = await redis_client.get(key)
    if result:
        return json.loads(result)
    return None
except CacheKeyError as e:
    logger.error(f"Cache key error: {e}", exc_info=True)
    return None  # Graceful degradation
except Exception as e:
    logger.error(f"Cache get error: {e}", exc_info=True)
    raise CacheError(f"Failed to get cache key {key}: {e}") from e
```

### Step 5: Add Tests

```python
def test_new_exception_handling():
    with pytest.raises(SpecificError):
        # Test that specific exception is raised
        pass
```

### Step 6: Commit

```bash
git add file.py
git commit -m "refactor: replace bare exceptions in file.py

- Replace generic Exception with SpecificError
- Add exception chaining with 'from e'
- Add exc_info=True to logging
- Add graceful degradation for non-critical errors"
```

---

## Checklist

Before committing exception handling changes:

- [ ] All specific exception types imported
- [ ] All `logger.error()` calls have `exc_info=True`
- [ ] All generic `Exception` handlers use `from e` when wrapping
- [ ] Critical operations raise, non-critical degrade gracefully
- [ ] Contextual information in log messages (item_id, key, etc.)
- [ ] Tests added for new exception handling
- [ ] Worker message requeue behavior preserved
- [ ] Database state updated before raising (if applicable)

---

## Quick Decision Tree

```
Exception occurred
    │
    ├─ Is this expected? (e.g., cache miss, key doesn't exist)
    │   └─ YES → Return None/default value + debug log
    │
    ├─ Is this a specific known error? (e.g., LLMAPIError, DatabaseConnectionError)
    │   └─ YES → Catch specific exception
    │               ├─ Is operation critical?
    │               │   ├─ YES → Log error + re-raise
    │               │   └─ NO → Log error + return degraded state
    │
    └─ Is this unexpected?
        └─ YES → Catch Exception
                  └─ Log error + wrap in domain exception + raise with 'from e'
```

---

## Resources

- **Exception Hierarchy:** `app/core/exceptions.py`
- **Test Examples:** `tests/integration/test_*_exceptions.py`
- **ADR:** `docs/decisions/ADR-014-exception-handling-architecture.md`
- **Completion Summary:** `/home/cytrex/userdocs/TAG-2-COMPLETION-SUMMARY.md`

---

## FAQ

**Q: When should I create a new exception type?**
A: Create a new exception type when:
- You need to handle this error differently from similar errors
- The error represents a distinct failure mode
- You want callers to be able to catch this specific error

**Q: Should I always use `from e`?**
A: Yes, always use `from e` when wrapping exceptions. This preserves the full stack trace and makes debugging much easier.

**Q: What if I don't know which exception to use?**
A: Start with the category exception (e.g., `DatabaseError`) and refine later if needed. Check `app/core/exceptions.py` for available types.

**Q: Should health checks raise exceptions?**
A: Health checks should return degraded states for expected errors (connection failures, etc.) but can raise for truly unexpected errors. The health check endpoint itself should never crash.

**Q: How do I test exception handling?**
A: Mock the failing operation to raise the exception, then use `pytest.raises()` to verify the correct exception is raised with proper chaining.

---

**Last Updated:** 2025-10-23
**Maintained By:** Development Team
**Questions?** See ADR-014 or ask in #engineering
