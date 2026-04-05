# Security Checklist for Developers

**Purpose:** Ensure secure coding practices when working with UQ Module, Event Publishing, and LLM integrations.

**Last Updated:** 2025-11-02
**Owner:** Security Team

---

## Pre-Commit Checklist

Before committing code, verify:

### 1. Secrets Management ✅

- [ ] No API keys in source code
- [ ] No API keys in log statements
- [ ] Credentials loaded from environment variables or secrets manager
- [ ] `.env` files in `.gitignore`
- [ ] Sensitive config fields use `repr=False` in Pydantic

**Bad:**
```python
OPENAI_API_KEY = "sk-proj-abc123..."  # ❌ Hardcoded
logger.info(f"Using API key: {api_key}")  # ❌ Logs secret
```

**Good:**
```python
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # ✅ From env
logger.info("OpenAI API key configured")  # ✅ No secret
```

---

### 2. Input Validation ✅

- [ ] All user inputs validated with Pydantic schemas
- [ ] String lengths limited (e.g., max 1000 chars)
- [ ] Numeric ranges validated (e.g., 0.0 <= score <= 1.0)
- [ ] HTML/JS sanitized with `bleach.clean()`
- [ ] SQL injection patterns rejected

**Bad:**
```python
payload = {"content": user_input}  # ❌ No validation
```

**Good:**
```python
class ContentPayload(BaseModel):
    content: str = Field(..., max_length=1000)

    @field_validator('content')
    @classmethod
    def sanitize(cls, v: str) -> str:
        return bleach.clean(v, tags=[], strip=True)

payload = ContentPayload(content=user_input)  # ✅ Validated
```

---

### 3. LLM Integration ✅

- [ ] Rate limiting configured (3500 RPM for OpenAI)
- [ ] Cost tracking enabled
- [ ] Circuit breaker configured (5 failures → open)
- [ ] Prompt injection defense implemented
- [ ] Content sanitized before sending to LLM
- [ ] LLM responses validated before use

**Bad:**
```python
llm_response = await llm.generate(f"Analyze: {user_content}")  # ❌ No limits
```

**Good:**
```python
sanitized_content = sanitize_for_llm(user_content)
async with rate_limiter:
    if not cost_tracker.can_make_request():
        raise CostLimitError()
    llm_response = await llm.generate(f"Analyze: {sanitized_content}")
```

---

### 4. Event Publishing ✅

- [ ] Event payloads validated with Pydantic schemas
- [ ] Sensitive fields encrypted or truncated
- [ ] Message size limited (< 256 KB)
- [ ] Correlation IDs validated (UUID format)
- [ ] RabbitMQ connection uses TLS (`amqps://`)

**Bad:**
```python
await publisher.publish_event("test.event", {"data": raw_input})  # ❌ No validation
```

**Good:**
```python
class TestEventPayload(BaseModel):
    data: str = Field(..., max_length=1000)

payload = TestEventPayload(data=raw_input)
await publisher.publish_event("test.event", payload.model_dump())  # ✅ Validated
```

---

### 5. Error Handling ✅

- [ ] Generic error messages in production
- [ ] Detailed errors only in development
- [ ] No stack traces in production logs
- [ ] Sensitive data redacted in error logs
- [ ] Error IDs for tracking (instead of full error text)

**Bad:**
```python
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)  # ❌ Exposes internals
    raise HTTPException(500, detail=str(e))  # ❌ Leaks to client
```

**Good:**
```python
except Exception as e:
    error_id = str(uuid4())
    logger.error(f"Error ID {error_id}: {e.__class__.__name__}")  # ✅ Generic
    if settings.ENVIRONMENT == "development":
        logger.debug(f"Detail: {e}", exc_info=True)
    raise HTTPException(500, detail=f"Error ID: {error_id}")  # ✅ Safe
```

---

### 6. Testing ✅

- [ ] Security tests written for new features
- [ ] Input validation tests (XSS, SQL injection)
- [ ] Rate limiting tests
- [ ] Error handling tests
- [ ] Integration tests with mocked LLM

**Required Tests:**
```python
def test_xss_blocked():
    """Test XSS payloads are sanitized."""
    malicious_input = "<script>alert('XSS')</script>"
    sanitized = sanitize_input(malicious_input)
    assert "<script>" not in sanitized

def test_rate_limit_enforced():
    """Test rate limit prevents excessive requests."""
    for _ in range(10):
        await make_request()  # Should succeed
    with pytest.raises(RateLimitError):
        await make_request()  # Should fail

def test_api_key_not_logged():
    """Test API keys are redacted in logs."""
    with mock.patch('logging.Logger.info') as mock_log:
        logger.info(f"API key: {api_key}")
        assert api_key not in str(mock_log.call_args)
```

---

## Code Review Checklist

When reviewing code, check:

### Security Red Flags 🚩

- [ ] Hardcoded credentials or API keys
- [ ] Unvalidated user input
- [ ] Plaintext RabbitMQ URLs (`amqp://`)
- [ ] Missing rate limits on external API calls
- [ ] Unencrypted sensitive data in events
- [ ] Generic exception handlers (`except Exception`)
- [ ] SQL query string concatenation
- [ ] `eval()` or `exec()` usage
- [ ] File paths from user input without validation
- [ ] Deserialization of untrusted data (`pickle.loads()`)

### Security Best Practices ✅

- [ ] Pydantic validation for all inputs
- [ ] Rate limiters configured correctly
- [ ] TLS enabled for external connections
- [ ] Sensitive data redacted in logs
- [ ] Error messages don't expose internals
- [ ] Tests cover security scenarios
- [ ] Documentation updated with security notes

---

## Quick Reference: Common Vulnerabilities

### OWASP Top 10 2021

| Category | Check | Example |
|----------|-------|---------|
| **A01: Broken Access Control** | API keys, JWT tokens, permissions | ✅ Redact keys in logs |
| **A02: Cryptographic Failures** | TLS, encryption at rest | ✅ Use `amqps://` not `amqp://` |
| **A03: Injection** | SQL, NoSQL, LDAP, OS commands | ✅ Validate with Pydantic |
| **A04: Insecure Design** | Threat modeling, security patterns | ✅ Review architecture |
| **A05: Security Misconfiguration** | Defaults, error messages, CORS | ✅ Production-safe configs |
| **A06: Vulnerable Components** | Dependencies, libraries | ✅ Run `pip-audit` regularly |
| **A07: Authentication Failures** | Weak passwords, missing MFA | ✅ Use strong JWT secrets |
| **A08: Data Integrity Failures** | Unsigned data, no checksums | ✅ Sign RabbitMQ messages |
| **A09: Logging Failures** | Missing logs, sensitive data in logs | ✅ Log securely |
| **A10: Server-Side Request Forgery** | User-controlled URLs | ✅ Validate URLs |

---

## Security Tools

### Pre-Commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# .pre-commit-config.yaml
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-r', 'services/', '-ll']

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

### Security Scanning

```bash
# Scan for secrets
detect-secrets scan --all-files --force-use-all-plugins

# Scan for vulnerabilities
bandit -r services/ -ll

# Dependency audit
pip-audit

# Container scanning
docker scan content-analysis-v2:latest
```

---

## Emergency Response

### Incident: API Key Leaked

1. **Immediate Actions:**
   ```bash
   # Revoke compromised key
   export OLD_KEY="sk-proj-abc123"
   export NEW_KEY="sk-proj-xyz789"

   # Rotate in production
   kubectl set env deployment/content-analysis-v2 OPENAI_API_KEY=$NEW_KEY

   # Check for unauthorized usage
   # (OpenAI dashboard → Usage → Filter by key)
   ```

2. **Investigation:**
   - Check git history: `git log -S "sk-proj-abc123"`
   - Check Docker logs: `docker logs content-analysis-v2 | grep "sk-proj"`
   - Check log aggregation systems (Splunk, ELK)

3. **Prevention:**
   - Enable secret scanning in GitHub
   - Add pre-commit hooks
   - Audit all logs for sensitive data

---

## Resources

**Internal:**
- [Security Audit Report](../../reports/SECURITY_AUDIT_UQ_MODULE_EVENT_PUBLISHING.md)
- [Remediation Plan](../../reports/SECURITY_REMEDIATION_PLAN.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)

**External:**
- [OWASP Top 10](https://owasp.org/Top10/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [OpenAI Security Best Practices](https://platform.openai.com/docs/guides/safety-best-practices)
- [RabbitMQ Security](https://www.rabbitmq.com/ssl.html)

---

## Contact

**Security Team:** security@news-mcp.com
**Security Hotline:** [Slack #security-incidents]
**Escalation Path:** Security Lead → CTO → CISO

---

**Last Reviewed:** 2025-11-02
**Next Review:** 2025-12-02
