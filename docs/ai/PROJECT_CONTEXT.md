# AI Banking Lab: Project Context

Last verified against the repository: 2026-07-14

## How To Read This Document

This is the master context document for humans and AI coding agents. Statements use these status labels:

- **Implemented**: present in the current repository or worktree.
- **Planned**: an intended direction, not current behavior.
- **Status not evidenced**: the repository does not contain enough history to make the claim.

Before changing code, also read [ARCHITECTURE.md](ARCHITECTURE.md), [CODING_STANDARDS.md](CODING_STANDARDS.md), [DECISIONS.md](DECISIONS.md), and [SESSION_STATE.md](SESSION_STATE.md).

## Project Vision

AI Banking Lab is not intended to be a general-purpose chatbot. Its stated direction is an **Agentic Development Platform (ADP) specialized in Apache Fineract banking operations**.

The platform should translate a natural-language banking goal into a governed, inspectable, deterministic execution path:

```text
Goal
  -> evidence and context
  -> classified intent
  -> capability path
  -> validated execution plan
  -> approved runtime execution
  -> business verification
  -> audit and observability
```

An LLM may help interpret a request, but it must not become the banking runtime. Business operations are represented as capabilities and execution plans. Transport, retries, verification, and audit remain deterministic application responsibilities.

## Long-Term Objective

**Planned:** evolve the current lab into a platform that converts natural-language goals into deterministic, governed workflows over Apache Fineract while preserving explicit boundaries between reasoning, business capability definition, transport execution, verification, observability, and governance.

The long-term roadmap supplied for the project includes an LLM goal planner, golden paths, multi-agent collaboration, evaluations, expanded observability, an MCP server, governance, autonomous banking workflows, and an AI Banking Platform v2. These items are not implemented unless explicitly listed below.

## Why This Project Exists

The codebase addresses the gap between flexible natural-language input and the precision required by banking APIs. The current design uses:

- retrieval to ground model prompts in local Fineract documentation;
- typed capabilities to own supported banking operations;
- validation before plan creation and before selected executions;
- execution plans to make operations inspectable;
- a runtime context to carry identifiers between workflow steps;
- business verification to check domain outcomes, not only HTTP success;
- recovery policies, audit records, and optional LangSmith traces.

## Scope

### Implemented scope

- FastAPI service with health, retrieval debug, planning debug, document Q&A, LangGraph workflow, state/history, and execution analytics routes.
- Local document ingestion for Markdown, text, and HTML.
- BM25 and OpenAI-embedding semantic retrieval.
- Reciprocal Rank Fusion, an intent-aware heuristic reranker, context grouping, and evidence summaries.
- Deterministic Planning Layer for three goal types.
- Capability registry with three savings-related capabilities.
- Typed multi-step execution plans.
- Tool registry for eight Fineract operations.
- Runtime template resolution, output extraction, and dynamic context propagation.
- Dry-run and guarded real execution paths.
- Business verification and dynamic savings-account approval/activation follow-up steps.
- Error classification, recovery decisions, and a bounded temporary-failure retry path.
- JSONL audit logging, execution analytics, execution timing, and optional LangSmith traces.
- LangGraph orchestration with SQLite checkpoints and an in-memory session store.
- Docker packaging, a local MariaDB/Litecore compose stack, and a GitHub Actions container/GitOps deployment workflow.

### Planned scope

- A production-grade LLM goal planner and capability resolver.
- Explicit multi-capability planning and composition.
- Golden-path workflow definitions and evaluations.
- Multi-agent collaboration.
- An MCP server.
- A formal governance layer and autonomous workflow controls.

## Non-Goals

- This is **not a chatbot product**. Conversational endpoints exist, but they are supporting interfaces, not the architectural objective.
- The LLM must not call Fineract directly.
- The Planning Layer must not contain HTTP methods, REST endpoints, Fineract clients, or execution loops.
- Unsupported banking operations must not be invented or routed to arbitrary endpoints.
- A successful HTTP response alone is not sufficient evidence of business success.
- This repository is not currently documented or tested as production-ready.

## Project Philosophy

1. **Determinism after interpretation.** Natural language may be ambiguous; approved execution must not be.
2. **Capabilities before endpoints.** A banking goal resolves to a supported business capability, not an arbitrary URL.
3. **Layered ownership.** Retrieval, planning, capability semantics, execution planning, runtime transport, verification, and observability have distinct responsibilities.
4. **Business correctness over transport success.** Verification checks client, savings-account, and charge states.
5. **Explicit safety gates.** Validation, pre-validation, dry-run, approval, error classification, and safe recovery are first-class concepts.
6. **Traceability.** Plans, runtime steps, outputs, timing, failures, recovery decisions, and audit events should remain inspectable.
7. **Incremental evolution.** Existing runtime behavior is treated as stable; new reasoning abstractions should compose with it rather than duplicate it.

## Current Implementation Status

### Retrieval

**Implemented.** `app/retrieval/` contains BM25 retrieval, OpenAI embedding-based semantic retrieval, weighted Reciprocal Rank Fusion, heuristic reranking, context construction, and debug output. `app/ingestion/` creates local chunk and vector indexes under `data/index/`.

### Planning

**Implemented, not accepted/closed.** `app/planning/` contains typed models, a deterministic regex classifier, a goal-to-root-capability path planner, and a service that delegates to the existing execution-plan builder. `POST /planning/debug` exposes this flow.

The validation report at [../../SPRINT_13_1_VALIDATION_REPORT.md](../../SPRINT_13_1_VALIDATION_REPORT.md) records unresolved acceptance findings. In particular, message-embedded parameters are not consumed by `PlannerService`, API goal values serialize in uppercase, parsed LLM payload values can override explicit values in another execution-service branch, and the planner currently supports only one root capability per path.

### Capabilities and validation

**Implemented.** The registry currently supports:

- `create_savings_monthly_fee`
- `pay_savings_charge`
- `onboard_client_with_savings_fee`

Each capability sanitizes input, validates required data, and builds a `MultiStepExecutionPlan`. Separate pre-execution validators exist for monthly-fee creation and charge payment; these validators perform Fineract reads.

### Runtime

**Implemented.** The runtime resolves tools and templates, invokes a centralized Fineract client, extracts outputs into `RuntimeContext`, records verification, adds business follow-up steps, classifies failures, performs one safe temporary retry, and writes audit records.

### Orchestration

**Implemented.** LangGraph coordinates input parsing, session loading, plan creation, pre-validation, approval, dry-run, execution, and final response. SQLite stores LangGraph checkpoints; a process-local `SessionStore` stores pending plans.

### Tests and quality

**Limited.** Six planning unit tests pass. `test/test_health.py` is empty. `test/test_endpoints.ps1` references routes absent from the current API. No repository-configured linter or type checker is present. See the Sprint 13.1 validation report for exact results.

## Current Architecture Maturity

The repository is an **advanced lab/prototype with a working layered runtime**, not a completed platform.

Mature areas:

- explicit execution plan model;
- capability and tool registries;
- runtime context and output propagation;
- centralized Fineract transport;
- business verification and follow-up routing;
- recovery, audit, and checkpoint foundations.

Developing areas:

- deterministic Planning Layer contract;
- payload extraction and safe merge precedence;
- true multi-capability path composition;
- comprehensive tests and evaluations;
- governance and production security controls;
- documentation and release/sprint traceability.

Current deviations from the target boundaries are documented in [ARCHITECTURE.md](ARCHITECTURE.md) and [SESSION_STATE.md](SESSION_STATE.md).

## Repository Structure

```text
app/
  agent/                 Legacy/session-oriented agent service and input parsing
  api/                   FastAPI routes
  capabilities/          Capability abstractions, models, registry, implementations
  core/                  Configuration and logging
  execution/             Runtime, Fineract transport, tools, verification, audit
  ingestion/             Document loading, chunking, and index creation
  langgraph_workflow/    Graph state, nodes, routing, SQLite checkpointing
  observability/         Timing, audit analytics, optional LangSmith client
  planning/              Deterministic goal classification and capability selection
  recovery/              Error classification, recovery policy, retry mutation
  retrieval/             BM25, semantic retrieval, fusion, reranking, context building
  schemas/               API request/response and validation models
  services/              Execution-plan service, OpenAI calls, guardrails, legacy helpers
  validators/            Pre-execution validation abstractions and registry
data/
  checkpoints/           LangGraph SQLite database files
  docs/                  Ingested source documentation
  execution/             JSONL audit log
  index/                 Chunk and vector indexes
docs/ai/                 Permanent AI knowledge base
mysql-init/              Local MariaDB initialization
test/                    Python and PowerShell tests
.github/workflows/       Container build and GitOps deployment workflow
```

## Technology Stack

### Application stack

- Python 3.11+ in `pyproject.toml`; Docker image currently uses Python 3.12.
- FastAPI and Uvicorn.
- Pydantic v2 models.
- `httpx` for Fineract transport.
- SQLite for LangGraph checkpoints.
- JSON and JSONL files for retrieval indexes and audit data.
- Docker, Docker Compose, GitHub Actions, GHCR, and an external GitOps repository.

### AI stack

- OpenAI Responses API through the `openai` Python package.
- Configured model defaults to `gpt-5.2` in `app/core/config.py`.
- OpenAI `text-embedding-3-small` embeddings.
- LangGraph and `langgraph-checkpoint-sqlite`.
- Optional LangSmith tracing when `LANGSMITH_API_KEY` is set.
- `rank-bm25` for lexical retrieval.
- Local Fineract documentation ingestion and vector index files.

`sentence-transformers` appears in `pyproject.toml` but is commented out in `requirements.txt`; the implemented embedding code uses OpenAI, not SentenceTransformers.

### Banking stack

- Apache Fineract-compatible Litecore service exposed locally through `/litecore-provider`.
- MariaDB 10.6 in Docker Compose.
- Tenant-aware headers (`Litecore-Platform-TenantId`).
- Basic authentication using the Fineract authentication endpoint.
- Current business domain coverage: clients, savings accounts, savings charges, monthly fees, savings approval, savings activation, and verification reads.

## Sprint Status

The repository has no sprint-labeled Git history and the README does not describe releases. Therefore sprint attribution is conservative.

- **Sprints 1-11:** **Status not evidenced.** The current repository collectively contains a substantial core runtime, but individual sprint objectives and completion cannot be reconstructed reliably.
- **Sprint 12, Enterprise Retrieval:** **Feature set implemented in the current worktree.** BM25, semantic retrieval, fusion, reranking, context building, and evidence summaries exist. Formal sprint closure evidence is absent.
- **Sprint 13.1, Planning Layer:** **Implemented, validation failed, not closed.** See the validation report.
- **Current active work:** Sprint 13.1 hardening and AI-native documentation. No additional product feature was added by the documentation task.

See [ROADMAP.md](ROADMAP.md) for the full evidence-aware roadmap.

## Future Direction

The next safe step is to close the Planning Layer contract before introducing more model autonomy. That means deciding goal serialization, defining deterministic parameter extraction or requiring structured payloads, establishing safe payload precedence, and specifying multi-capability plan composition.

After that foundation is accepted, the planned direction is:

```text
LLM goal planning and capability resolution
  -> golden paths
  -> evaluations
  -> multi-agent collaboration
  -> expanded observability and governance
  -> MCP exposure
  -> gated autonomous workflows
  -> platform v2
```

## Source-of-Truth Order

When documents and code disagree, use this order:

1. Executable code and tests.
2. [SESSION_STATE.md](SESSION_STATE.md) for current work status.
3. [DECISIONS.md](DECISIONS.md) for architectural intent.
4. [ARCHITECTURE.md](ARCHITECTURE.md) for system structure.
5. [ROADMAP.md](ROADMAP.md) for planned work.

Update these documents in the same change whenever architecture, capability coverage, API contracts, sprint status, or major risks change.
