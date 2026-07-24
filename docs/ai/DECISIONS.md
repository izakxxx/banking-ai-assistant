# Architecture Decision Log

Last updated: 2026-07-14

## About This Log

The repository did not previously contain ADR files. The entries below are **retrospective records of decisions visible in the current code**, not claims that these ADR numbers existed when the code was written.

Statuses:

- **Implemented:** clearly present in code.
- **Partially implemented:** the direction exists with known boundary gaps.
- **Planned:** approved direction documented for future work, not current behavior.

## ADR-001: Use Hybrid Retrieval

- Status: Implemented
- Context: Fineract documentation queries benefit from exact field-name matching and semantic similarity.
- Decision: Combine BM25 and semantic retrieval, then merge ranked candidates with weighted Reciprocal Rank Fusion.
- Reason: Improve recall across exact API vocabulary and natural-language phrasing.
- Consequences: Two indexes and retrieval paths must remain compatible; semantic retrieval requires OpenAI embeddings.
- Evidence: `app/retrieval/bm25_retriever.py`, `semantic_retriever.py`, `hybrid_retriever.py`.

## ADR-002: Add Deterministic Reranking and Evidence Context

- Status: Implemented
- Context: Raw fused results can contain contextually weak or noisy documentation chunks.
- Decision: Apply heuristic domain/context reranking, section grouping, evidence classification, and evidence summaries.
- Reason: Improve downstream context quality without another model call.
- Consequences: Ranking behavior depends on maintained domain-term and negative-context dictionaries.
- Evidence: `app/retrieval/reranker.py`, `context_builder.py`.

## ADR-003: Represent Banking Operations as Capabilities

- Status: Implemented
- Context: Natural-language intents must not map directly to arbitrary REST operations.
- Decision: Define `BaseCapability` with sanitization, validation, and plan construction, and resolve implementations through `CapabilityRegistry`.
- Reason: Create a business-level allowlist and reusable abstraction above Fineract transport.
- Consequences: Every supported business workflow requires a registered capability and tests.
- Evidence: `app/capabilities/base.py`, `registry.py`, `savings/`.

## ADR-004: Use Typed Execution Plans

- Status: Implemented
- Context: Multi-step banking operations need inspectable ordering, dependencies, payloads, outputs, and verification markers.
- Decision: Represent work as `MultiStepExecutionPlan` and `ExecutionStep` Pydantic models.
- Reason: Separate plan creation from execution and enable dry-run, audit, and deterministic runtime behavior.
- Consequences: Plan schema compatibility is a cross-layer contract.
- Evidence: `app/capabilities/models.py`.

## ADR-005: Resolve Transport Through a Tool Registry

- Status: Partially implemented
- Context: Business steps should not duplicate HTTP endpoint knowledge.
- Decision: Map stable tool names to HTTP methods and endpoint templates in `ToolRegistry`.
- Reason: Centralize transport details and let composite capabilities remain transport-neutral.
- Consequences: Runtime must reject unregistered tools. Two existing single-step capabilities still embed direct methods/endpoints and remain technical debt.
- Evidence: `app/execution/tool_registry.py`, `executor.py`, onboarding capability.

## ADR-006: Propagate Dynamic Values Through Runtime Context

- Status: Implemented
- Context: Later workflow steps need identifiers created by earlier Fineract responses.
- Decision: Extract response values through `output_mapping`, store them in `RuntimeContext`, and resolve `{{key}}` templates before execution.
- Reason: Support dynamic multi-step workflows without hard-coded IDs or planner-side execution state.
- Consequences: Output paths and template names become plan contracts and require tests.
- Evidence: `app/execution/runtime_context.py`, `template_resolver.py`, `executor.py`.

## ADR-007: Centralize Fineract Transport

- Status: Implemented
- Context: Authentication, tenant headers, timeouts, errors, and response parsing must be consistent.
- Decision: Route runtime HTTP through a shared `FineractClient` and raise `FineractExecutionError` for transport/API failures.
- Reason: Keep transport out of Planning and make runtime failure handling uniform.
- Consequences: The current global client caches an auth key and configuration is process-global.
- Evidence: `app/execution/fineract_client.py`.

## ADR-008: Verify Business State After Execution

- Status: Implemented
- Context: HTTP success does not prove that a client, account, or charge reached the required business state.
- Decision: Mark verification steps and interpret response bodies through deterministic business rules.
- Reason: Establish business correctness, not only technical success.
- Consequences: Every new verified domain action needs an explicit rule and test.
- Evidence: `app/execution/business_verification.py`, `verification.py`.

## ADR-009: Add Business Follow-Up Steps Dynamically

- Status: Implemented
- Context: A savings account may exist but remain pending approval or inactive.
- Decision: Append approval/activation and re-verification steps based on business verification status.
- Reason: Continue a known safe workflow toward the required business state.
- Consequences: Runtime plans can expand during execution; diagrams and audit results must use the expanded plan. Current dates/dependencies are hard-coded debt.
- Evidence: `app/execution/business_router.py`, `executor.py`.

## ADR-010: Separate Local Capability Validation From Pre-Execution Validation

- Status: Implemented
- Context: Some checks require only input data; others require current Fineract state.
- Decision: Validate payload structure in capabilities and use registered pre-execution validators for external-state reads.
- Reason: Avoid building invalid plans while still checking account/charge state before execution.
- Consequences: Pre-execution validators currently depend directly on Fineract transport and are available for only two intents.
- Evidence: capability `validate()` methods and `app/validators/`.

## ADR-011: Use LangGraph for Stateful Workflow Orchestration

- Status: Implemented
- Context: Planning, validation, approval, dry-run, and execution span multiple states and user requests.
- Decision: Model orchestration as a LangGraph state machine with SQLite checkpointing.
- Reason: Make transitions explicit and expose current/history state.
- Consequences: Graph routing and session persistence must remain consistent. The separate pending-plan store is in memory and is not restart-durable.
- Evidence: `app/langgraph_workflow/graph.py`, `state.py`, state API routes.

## ADR-012: Require Dry-Run and Approval Paths

- Status: Implemented
- Context: Banking writes require inspection and user intent confirmation.
- Decision: Support dry-run without API calls, persist pending plans, and require an execute command before real runtime execution.
- Reason: Reduce accidental execution and make plans inspectable.
- Consequences: Session identity and command parsing are safety-relevant contracts.
- Evidence: `app/execution/executor.py`, `app/langgraph_workflow/graph.py`, `app/agent/input_parser.py`.

## ADR-013: Classify Failures Before Recovery

- Status: Implemented
- Context: Retrying every Fineract failure is unsafe.
- Decision: Classify errors, apply a recovery policy, and automatically retry only bounded temporary failures.
- Reason: Distinguish safe transient recovery from duplicates, validation errors, authorization failures, and human-review cases.
- Consequences: Recovery coverage is intentionally narrow; unhandled failures stop execution.
- Evidence: `app/recovery/`, `app/execution/executor.py`.

## ADR-014: Audit Every Runtime Outcome

- Status: Implemented
- Context: Banking workflows require traceability across dry-run, blocked, successful, and failed execution.
- Decision: Append JSONL audit records and derive aggregate execution analytics from them.
- Reason: Provide a local, inspectable execution history and operational metrics.
- Consequences: File-based audit is synchronous and local; retention, integrity, access control, and redaction are not yet formalized.
- Evidence: `app/execution/audit_log.py`, `app/observability/execution_analytics.py`.

## ADR-015: Make LangSmith Optional and Non-Blocking

- Status: Implemented
- Context: External tracing should improve observability without becoming an execution dependency.
- Decision: Enable LangSmith only when `LANGSMITH_API_KEY` exists and tolerate trace creation/update failures.
- Reason: Preserve runtime availability when observability is unavailable.
- Consequences: Trace failures can be silent; local audit remains the fallback evidence.
- Evidence: `app/observability/langsmith_config.py`, `app/execution/executor.py`.

## ADR-016: Add a Deterministic Planning Layer Above Capabilities

- Status: Partially implemented
- Context: The project needs goal-oriented reasoning without exposing transport to Planning or replacing the stable runtime.
- Decision: Classify requests into `GoalType`, map them to capability paths, resolve the Capability Registry, and call the existing execution-plan builder.
- Reason: Introduce a planning abstraction incrementally while reusing validation and execution infrastructure.
- Consequences: The current planner supports one root capability, does not consume message parameters, and has an unresolved serialized-goal contract.
- Evidence: `app/planning/`, `POST /planning/debug`, Sprint 13.1 validation report.

## ADR-017: Keep LLM Planning Output Structured and Capability-Limited

- Status: Implemented in the legacy/non-explicit execution-service path; contract needs hardening
- Context: Free-form model output cannot safely drive banking execution.
- Decision: Prompt OpenAI to return `{intent, payload}` JSON limited to three supported intents, parse it, and then resolve the Capability Registry.
- Reason: Constrain model output before capability validation and plan creation.
- Consequences: JSON parsing is permissive, model payload currently overrides explicit payload on conflicts, and raw responses are printed. These are open risks.
- Evidence: `app/services/openai_service.py`, `execution_service.py`.

## ADR-018: Use a Composite Capability for Customer/Savings/Fee Onboarding

- Status: Implemented
- Context: Onboarding requires dependent client, savings account, fee, and verification operations.
- Decision: Represent the workflow as one registered capability that emits a six-step plan and uses runtime outputs for later steps.
- Reason: Keep the supported business workflow atomic at the capability-selection level while allowing deterministic multi-step execution.
- Consequences: Planning currently reports one root capability rather than each internal operation as a capability path.
- Evidence: `app/capabilities/savings/onboard_client_with_savings_fee.py`.

## ADR-019: Expose Debug and State Interfaces

- Status: Implemented
- Context: Retrieval, planning, and stateful execution need inspectable intermediate data during development.
- Decision: Add retrieval debug, planning debug, graph state/history, and execution analytics endpoints.
- Reason: Improve diagnosis and architectural transparency.
- Consequences: Debug responses can contain request and execution data and require access control/redaction before production exposure.
- Evidence: `app/api/routes.py`.

## ADR-020: Package and Deploy as a Container

- Status: Implemented
- Context: The API needs repeatable runtime packaging and deployment automation.
- Decision: Build a Python/Uvicorn image, publish it to GHCR, and update an external GitOps Kubernetes manifest.
- Reason: Provide a simple delivery path from `main` to a deployment repository.
- Consequences: Deployment correctness depends on external secrets, repository access, and manifest conventions not validated in this codebase.
- Evidence: `Dockerfile`, `.github/workflows/cd-banking-ai-assistant.yml`.

## Planned Decisions Requiring ADRs

The following must receive explicit ADRs before implementation:

- serialized `GoalType` API values;
- explicit versus parsed payload precedence and conflict handling;
- deterministic parameter extraction ownership;
- multi-capability plan composition;
- one source of truth for capability IDs;
- durable pending-plan session storage;
- governance and authorization enforcement points;
- MCP exposure boundaries;
- autonomous workflow eligibility and stop conditions.
