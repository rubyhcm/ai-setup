---

# 🧠 LOGGING ARCHITECTURE RULE V3 (FOR AI AGENT)

## 0. 🎯 PURPOSE

```text
Ensure high-value, context-aware logging with:
- High coverage on critical paths (exception, return-value-check)
- Low noise
- Consistent structure
- Debuggable in production
```

---

# 1. 📦 LOG CLASSIFICATION (MANDATORY)

```text
Every log statement MUST belong to one category:

1. ASSERTION_CHECK
2. RETURN_VALUE_CHECK
3. EXCEPTION
4. LOGIC_BRANCH
5. OBSERVING_POINT
```

---

# 2. 🧠 LOGGING DECISION ENGINE

```text
FOR each potential log position:

IF (unexpected OR high-impact OR hard-to-debug)
    → MUST LOG

ELSE IF (important state / decision point)
    → SHOULD LOG

ELSE
    → DO NOT LOG
```

---

# 3. 🔥 PRIORITY ENFORCEMENT (VERY IMPORTANT)

```text
Agent MUST prioritize adding logs to:

1. EXCEPTION (catch blocks)
2. RETURN_VALUE_CHECK (error handling)

Reason:
- These areas have lowest real-world coverage (8–42%)
- Highest debugging value
```

---

# 4. 📊 DETAILED RULES

## 4.1 ASSERTION_CHECK

```text
MUST LOG:
- Input validation failure
- Security validation failure
- Data invariant violation

DO NOT LOG:
- Internal assertions already guaranteed by tests
```

---

## 4.2 RETURN_VALUE_CHECK ⚠️ (HIGH PRIORITY)

```text
MUST LOG:
- err != nil
- null / nil unexpected
- external call failure
- retry triggered

SHOULD LOG:
- external API response (optional sampling)

DO NOT LOG:
- pure function return
- simple getter
```

---

## 4.3 EXCEPTION 🚨 (HIGH PRIORITY)

```text
MUST LOG:
- exception not fully handled
- exception propagated upward
- DB / network / auth / payment error

SHOULD LOG:
- retryable exception (include retry_count)

DO NOT LOG:
- fully handled + no side effect
```

---

## 4.4 LOGIC_BRANCH

```text
MUST LOG:
- rare / unexpected branch
- fallback logic
- feature flag decision

SHOULD LOG:
- business decision (approve/reject)

DO NOT LOG:
- trivial if/else
```

---

## 4.5 OBSERVING_POINT

```text
MUST LOG:
- request start / end
- job start / end
- transaction boundary

SHOULD LOG:
- important state (user_id, request_id, latency)

DO NOT LOG:
- repetitive debug info
```

---

# 5. 🧩 CONTEXT-AWARE RULE (CRITICAL)

Agent MUST evaluate context before logging:

```text
Context Factors:

1. Impact:
   - crash?
   - data loss?
   - user-visible?

2. Recoverability:
   - retry?
   - fallback?

3. Ownership:
   - handled here?
   - handled upstream?

4. Frequency:
   - high-frequency path?
```

---

## 🎯 DECISION MATRIX

```text
Critical + Unhandled        → ERROR log (MUST)
Recoverable + Retry         → WARN log
Important State             → INFO log
High-frequency trivial      → NO LOG
```

---

# 6. 🚫 ANTI-PATTERNS (STRICTLY FORBIDDEN)

```text
❌ Blind logging:
   log("start function")
   log("end function")

❌ Missing error log:
   if err != nil { return err }

❌ Duplicate logging:
   - same error logged multiple layers

❌ Logging sensitive data:
   - password
   - token
   - full PII
```

---

# 7. 🧱 LOG FORMAT STANDARD (REQUIRED)

```json
{
  "level": "ERROR | WARN | INFO",
  "category": "EXCEPTION | RETURN_VALUE_CHECK | ...",
  "message": "clear and specific message",
  "context": {
    "request_id": "...",
    "trace_id": "...",
    "user_id": "...",
    "function": "...",
    "service": "...",
    "retry_count": 0
  }
}
```

---

# 8. 🔁 ERROR HANDLING + LOGGING RULE

```text
IF error is returned:
    → MUST LOG OR explicitly delegate logging to upper layer

IF delegated:
    → DO NOT log here (avoid duplication)
```

---

# 9. 📈 LOG DENSITY CONTROL

```text
High-frequency paths (loops, hot APIs):
    → use sampling OR aggregated logging

Example:
    log only 1 / N requests
```

---

# 10. 🧪 AGENT VALIDATION CHECKLIST

Before finishing code, agent MUST verify:

```text
[ ] All exceptions are logged or delegated
[ ] All err != nil paths are handled
[ ] No duplicate logs across layers
[ ] No sensitive data leaked
[ ] Log messages are meaningful (not generic)
[ ] High-value areas (exception, return-check) are covered
```

---

# 11. 🚀 EXPECTED OUTCOME

```text
- Exception logging coverage: ~80–90%
- Return-value logging: ~60–70%
- Reduced log noise
- Faster debugging in production
```

---

# 🔥 BONUS: SHORT VERSION (FOR SYSTEM PROMPT)

```text
Always log:
- unexpected errors
- unhandled exceptions
- external failures

Prioritize:
- exception
- return-value-check

Never log:
- trivial flow
- high-frequency noise

Avoid:
- duplicate logs
- missing error logs

Always include:
- category
- context
- meaningful message
```

---