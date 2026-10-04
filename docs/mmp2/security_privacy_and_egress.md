# MMP-2 Security, Privacy & Zero Network Egress Contract

> **Specification Ref:** `MMP2-POL-004`, `PRD §21.1`  
> **Core Concept:** Verifiable Air-Gap Qualification and Zero Telemetry Invariant

---

## 1. Zero Network Egress Engineering Invariant

In `LOCAL` intelligence mode, the application enforces complete network isolation:

```python
# Formal Runtime Security State
NETWORK_EGRESS = "DENIED"
EXTERNAL_LLM_API = "DENIED"
TELEMETRY = "DENIED"
PROMPT_UPLOAD = "DENIED"
CASE_DATA_UPLOAD = "DENIED"
RUNTIME_DOWNLOADS = "DENIED"
```

---

## 2. Automated Egress Qualification Testing

To prove to CPA firms and enterprise security auditors that no data leaks, the CI and pre-commit validation suite executes negative socket tests:

1. **Socket Interception Gate:** Monkeypatches standard Python `socket.connect`, `urllib`, and `requests` to assert that any attempt to establish a non-loopback outbound socket raises an immediate security exception.
2. **DNS Resolution Block:** Asserts that DNS resolution calls fail closed.
3. **Loopback Only:** Restricts HTTP server binding strictly to `127.0.0.1` / `localhost`.
4. **Offline Air-Gap Qualification:** Validates that the entire intelligence suite (investigation, gap analysis, question drafting, RAG retrieval) executes successfully with all network interfaces disabled.
