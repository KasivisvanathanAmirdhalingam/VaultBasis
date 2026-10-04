# MMP-2 Open-Source & Framework Governance

> **Specification Ref:** `MMP2-GOV-001`  
> **Core Concept:** Framework Minimization and Software Bill of Materials (SBOM) Tracking

---

## 1. The Anti-Sprawl Principle: Framework Minimization

Modern AI projects frequently collapse under dependency sprawl (e.g., pulling in LangChain, LangGraph, AutoGen, CrewAI, LlamaIndex simultaneously), leading to massive distribution bundle bloat, dependency conflicts, and hidden network telemetry.

**VaultBasis enforces strict Framework Minimization:**
- A compact, in-house agent orchestration loop (< 500 lines of clean Python).
- Standardized Model Context Protocol (MCP) for tool binding.
- Direct C/C++ bindings for inference (`llama-cpp-python` / ONNX).
- Zero third-party telemetry or cloud-logging SDKs.

---

## 2. Software Bill of Materials (SBOM) Ledger

All dependencies in the intelligence runtime must maintain an entry in the SBOM catalog:

| Component | Category | Permitted License | Telemetry Status | Commercial Status |
|---|---|---|---|---|
| `llama-cpp-python` / `llama.cpp` | Model Runtime | MIT | Zero Telemetry | Approved |
| `sqlite3` | Relational Store | Public Domain | Zero Telemetry | Approved |
| `fastapi` / `uvicorn` | Loopback REST / WebSockets | BSD-3-Clause | Zero Telemetry | Approved |
| `pydantic` | Schema Validation | MIT | Zero Telemetry | Approved |
| `numpy` | Vector Math | BSD-3-Clause | Zero Telemetry | Approved |
| `sentencepiece` / `tiktoken` | Tokenization | Apache-2.0 / MIT | Zero Telemetry | Approved |

Any dependency with non-commercial (CC-BY-NC), copyleft (GPL), or telemetric tracking is rejected at the build gate.
