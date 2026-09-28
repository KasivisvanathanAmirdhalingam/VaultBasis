# VaultBasis MMP-2-AI Tasks Ledger (AI Engineering)

**Mission**: Explore how modern AI can help a practitioner understand, investigate, research, navigate and review consequential digital outcomes while every authoritative VaultBasis determination remains grounded in deterministic evidence and independently verifiable artifacts.
**Branch**: `lab/mmp-2-ai`

## 7 Labs Implementation Sequence

### [ ] Lab AI-01: Model Gateway + Structured Output
**Build**: Model Gateway, provider abstraction, multi-LLM routing, structured output, streaming, retries, token/cost accounting.
**Learn**: APIs, routing, retries, multi-model, costs.
**Promotion Gate**: Model-independent tests.

### [ ] Lab AI-02: Evals + Observability
**Build**: Evaluation pipelines and comprehensive tracing (trace_id, prompt version, retrieved docs, tool calls, costs, policy decisions).
**Learn**: Evaluation engineering, privacy-safe tracing.
**Promotion Gate**: Repeatable benchmark.

### [ ] Lab AI-03: Regulatory RAG
**Build**: Embeddings, hybrid search (BM25 + vector), reranking, temporal metadata (effective dates), citation grounding.
**Learn**: Information retrieval, temporal RAG mechanics.
**Promotion Gate**: Groundedness/retrieval thresholds.

### [ ] Lab AI-04: VaultBasis MCP Server
**Build**: Safe subset of deterministic APIs as bounded MCP tools (`cases.get_summary`, `findings.get`, `findings.explain`, `regulations.search`, etc).
**Learn**: Tool/API contracts, permission policies.
**Promotion Gate**: Bounded read-only tool suite.

### [ ] Lab AI-05: Finding Investigator (Single Agent)
**Build**: Agent workflow + Human In The Loop (HITL). Bounded read-only investigation using the state machine to own workflow progression and permissions.
**Learn**: Durable state, real task success/evaluation, recovery.
**Promotion Gate**: Real task success/eval against baseline.

### [ ] Lab AI-06: Workpaper Assistant
**Build**: Structured generation of draft workpapers containing explicitly separated verified facts vs. AI-generated narratives.
**Learn**: Practitioner usefulness, structured reporting.
**Promotion Gate**: Practitioner usefulness.

### [ ] Lab AI-07: A2A Challenge Experiment
**Build**: Review Orchestrator routing to Evidence Agent, Regulatory Agent, and Challenge/Review Agent.
**Learn**: Agent interoperability, peer review automation.
**Promotion Gate**: Must beat simpler baseline (single agent).

> **CRITICAL BOUNDARY**: AI must sit strictly *above* the assurance kernel. AI may explain, retrieve, research, navigate, orchestrate, or assist, but it must NEVER silently determine reconciliation outcomes (MATCHED, BASIS_DIFFERENCE).
