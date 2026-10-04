# MMP-2 Local Model Runtime & Multi-LLM Specialization

> **Specification Ref:** `MMP2-MODEL-001`, `MMP2-MODEL-002`  
> **Core Concept:** Efficient, Local Open-Weight Execution with Role-Specialized Models

---

## 1. Local Runtime Engine Architecture

VaultBasis packages a lightweight local inference runtime (e.g. `llama.cpp` bindings / ONNX Runtime / embedded GGUF engine) executing directly on practitioner hardware (Apple Silicon Metal / Windows DirectX / x86_64 AVX2).

### Economic & Privacy Contract:
- **No Per-Token Billing:** Unlimited queries within local hardware capacity.
- **Zero Token Bleed:** Zero client data or prompts sent over WAN.
- **Offline Self-Sufficiency:** Functions without internet connectivity once model weights are installed.

---

## 2. Multi-Model Role Specialization

Rather than running an expensive, monolithic model for every operation, VaultBasis utilizes three specialized tiers:

```
┌────────────────────────────────────────────────────────────────────────────┐
│ MODEL A: Fast Local Router & Extractor (~1B-3B parameters, Q4_K_M)         │
│ • Intent classification & agent dispatch                                  │
│ • Query rewriting & keyword extraction                                    │
│ • Low latency (< 100ms response)                                          │
└────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ MODEL B: Reasoning & Investigation Engine (~7B-14B parameters, Q4_K_M)     │
│ • Complex case evidence synthesis                                         │
│ • Missing basis root-cause investigation                                  │
│ • Client question generation                                              │
│ • Deep multi-hop document reasoning                                       │
└────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼ (High-Risk Operations Only)
┌────────────────────────────────────────────────────────────────────────────┐
│ MODEL C: Critic & Citation Verifier (~3B-7B parameters)                    │
│ • Cross-examines Model B's output against deterministic evidence          │
│ • Flags ungrounded statements or hallucinated citations                   │
│ • Computes cross-model agreement metrics for confidence scoring           │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Hardware Resource Budgeting

The local runtime enforces strict RAM and CPU/GPU caps to prevent starving the host workstation:

| Target System | Model Footprint | Memory Cap | Target Throughput |
|---|---|---|---|
| **Base Workstation (16GB RAM)** | 3B + 7B Quantized (GGUF Q4) | 6.5 GB Max | 25-40 tokens/sec |
| **Power Workstation (32GB+ RAM / M-Series Pro)** | 3B + 14B Quantized (GGUF Q5/Q8) | 12.0 GB Max | 50-80 tokens/sec |
| **Air-Gapped Laptop (Battery Mode)** | Throttled thread pool (4 cores) | 5.0 GB Max | 15-25 tokens/sec |
