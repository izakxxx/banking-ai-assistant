# Roadmap

Last updated: 2026-07-14

## Status Legend

- **Implemented:** the deliverable exists in the repository.
- **In progress:** code exists, but acceptance or closure is incomplete.
- **Planned:** future direction; not current behavior.
- **Status not evidenced:** Git history and repository documentation do not establish the historical sprint contents or completion.

The Git history has no sprint labels, and `README.md` contains only the repository name. This roadmap does not retroactively assign existing modules to Sprints 1-11 without evidence.

## Roadmap Summary

| Sprint | Theme | Status |
|---:|---|---|
| 1-11 | Core Runtime | Status not evidenced by individual sprint |
| 12 | Enterprise Retrieval | Feature set implemented; formal closure not evidenced |
| 13 | Planning Layer | In progress; Sprint 13.1 implemented but not accepted |
| 14 | LLM Goal Planner, Capability Resolver, Tool Calling | Planned |
| 15 | Golden Paths | Planned |
| 16 | Multi-Agent Collaboration | Planned |
| 17 | Evaluation Framework | Planned |
| 18 | Observability | Planned expansion; foundations already exist |
| 19 | MCP Server | Planned |
| 20 | Governance | Planned |
| 21 | Autonomous Banking Workflows | Planned |
| 22 | AI Banking Platform v2 | Planned |

## Sprints 1-11: Core Runtime History

The current repository contains a core runtime, but the exact sequence in which it was built cannot be recovered from sprint documentation or commit messages. Each historical sprint is therefore recorded without invented deliverables.

| Sprint | Objectives | Expected deliverables | Success criteria | Dependencies | Status |
|---:|---|---|---|---|---|
| 1 | Historical Core Runtime increment; exact objective not evidenced | Not evidenced | No sprint acceptance record found | Not evidenced | Status not evidenced |
| 2 | Historical Core Runtime increment; exact objective not evidenced | Not evidenced | No sprint acceptance record found | Not evidenced | Status not evidenced |
| 3 | Historical Core Runtime increment; exact objective not evidenced | Not evidenced | No sprint acceptance record found | Not evidenced | Status not evidenced |
| 4 | Historical Core Runtime increment; exact objective not evidenced | Not evidenced | No sprint acceptance record found | Not evidenced | Status not evidenced |
| 5 | Historical Core Runtime increment; exact objective not evidenced | Not evidenced | No sprint acceptance record found | Not evidenced | Status not evidenced |
| 6 | Historical Core Runtime increment; exact objective not evidenced | Not evidenced | No sprint acceptance record found | Not evidenced | Status not evidenced |
| 7 | Historical Core Runtime increment; exact objective not evidenced | Not evidenced | No sprint acceptance record found | Not evidenced | Status not evidenced |
| 8 | Historical Core Runtime increment; exact objective not evidenced | Not evidenced | No sprint acceptance record found | Not evidenced | Status not evidenced |
| 9 | Historical Core Runtime increment; exact objective not evidenced | Not evidenced | No sprint acceptance record found | Not evidenced | Status not evidenced |
| 10 | Historical Core Runtime increment; exact objective not evidenced | Not evidenced | No sprint acceptance record found | Not evidenced | Status not evidenced |
| 11 | Historical Core Runtime increment; exact objective not evidenced | Not evidenced | No sprint acceptance record found | Not evidenced | Status not evidenced |

### Current code-backed Core Runtime milestone

The repository now contains these runtime capabilities, but they must not be attributed to a particular Sprint 1-11 without historical evidence:

- typed execution steps and multi-step plans;
- capability, tool, and pre-execution-validator registries;
- runtime template resolution and output extraction;
- dynamic runtime context propagation;
- centralized Fineract transport;
- dry-run and real-execution paths;
- business verification and follow-up routing;
- error classification, recovery policy, and bounded retry;
- JSONL audit, timing, analytics, and optional LangSmith traces;
- LangGraph orchestration and SQLite checkpoints.

Success evidence for the collective milestone is code presence and controlled validation only. Full external integration and production acceptance are not evidenced.

## Sprint 12: Enterprise Retrieval

**Status:** Feature set implemented in the current worktree; formal sprint closure is not evidenced.

### Objectives

- Combine lexical and semantic retrieval over local Fineract documentation.
- Improve recall and ranking quality.
- Build structured context and evidence summaries for downstream LLM calls.

### Expected deliverables

- BM25 retrieval.
- OpenAI embedding-based semantic retrieval.
- Weighted Reciprocal Rank Fusion.
- Intent/context-aware reranking.
- Context grouping and evidence summary generation.
- Retrieval and context debug output.

### Success criteria

- Both retrieval strategies return a common result shape.
- Hybrid retrieval combines duplicate chunks and records sources.
- Reranking is deterministic for the same inputs and indexes.
- Context output identifies evidence classes and source chunks.
- Retrieval debug route exposes intermediate and final candidates.

### Dependencies

- Local documentation ingestion and chunk index.
- OpenAI API key and embedding access for semantic retrieval.
- `rank-bm25`, NumPy, and vector index files.

### Repository evidence

`app/ingestion/`, `app/retrieval/`, `data/docs/`, `data/index/`, and `POST /retrieval/debug`.

## Sprint 13: Planning Layer

**Status:** In progress.

### Sprint 13.1: Deterministic Planning Foundation

**Status:** Implemented, validation failed, not accepted/closed.

#### Objectives

- Introduce typed goals and planning results.
- Classify supported natural-language goals deterministically.
- Map goals to registered capabilities.
- Reuse the existing capability validation and execution-plan builder.
- Add planning diagnostics without changing the stable runtime.

#### Expected deliverables

- `app/planning/` package.
- `GoalClassifier`, `PathPlanner`, and `PlannerService`.
- Typed `GoalType`, `CapabilityInvocation`, `ExecutionPath`, and `PlannerResult`.
- `POST /planning/debug`.
- Focused planning tests.

#### Success criteria

- Planning contains no HTTP, REST endpoint, Fineract client, or execution logic.
- Supported goals select the correct registered capability.
- Capability validation errors are preserved.
- Valid structured payloads produce existing execution plans.
- Unknown goals produce no executable path.
- API goal and payload contracts are explicit and tested.

#### Dependencies

- Capability Registry.
- `build_execution_plan()`.
- Existing capability models and validators.
- Sprint 12 retrieval only for legacy/non-explicit LLM planning paths; deterministic planning itself does not use retrieval.

#### Current acceptance blockers

- message-embedded parameters are not consumed by `PlannerService`;
- API goal values are uppercase while the validation contract requested lowercase values;
- parsed LLM payload values can override explicit values in the non-explicit execution-service branch;
- only one root capability is supported per path.

See [../../SPRINT_13_1_VALIDATION_REPORT.md](../../SPRINT_13_1_VALIDATION_REPORT.md).

### Sprint 13.2: Planner Input Contract and Safe Payload Resolution

**Status:** Planned recommendation from Sprint 13.1 validation; not implemented.

#### Objectives

- Close the Planner/API input and output contract.
- Define parameter extraction ownership.
- Define safe explicit-versus-parsed payload precedence.
- Specify how ordered multi-capability paths compose plans.

#### Expected deliverables

- A documented and tested goal serialization contract.
- A deterministic input adapter or an explicit structured-payload-only API contract.
- Conflict handling for critical banking values.
- Table-driven service and `TestClient` tests for validation scenarios A-F.
- A design decision for multi-capability plan composition.

#### Success criteria

- Explicit amounts and identifiers cannot be silently overwritten.
- Message and structured payload behavior is predictable and documented.
- Every supported goal has service and API contract tests.
- No new transport knowledge enters Planning.
- Sprint 13.1 validation findings are resolved or explicitly accepted.

#### Dependencies

- Sprint 13.1 implementation.
- Existing input parser, execution service, capability aliases, and registries.
- Architecture decision on goal serialization and payload precedence.

## Sprint 14: LLM Goal Planner, Capability Resolver, Tool Calling

**Status:** Planned.

### Objectives

- Add model-assisted goal interpretation without bypassing deterministic controls.
- Resolve model proposals only to registered capabilities.
- Define governed tool-call proposals that cannot directly invoke Fineract.

### Expected deliverables

- Typed LLM goal-planning response contract.
- Capability resolver backed by the Capability Registry.
- Tool-call proposal adapter with allowlisting and validation.
- Deterministic fallback and rejection behavior.
- Prompt and contract tests.

### Success criteria

- LLM output cannot introduce an unregistered capability or arbitrary endpoint.
- All proposed payloads pass capability validation before plan creation.
- Explicit caller values have documented precedence.
- Model failure produces a safe result with no execution.

### Dependencies

- Accepted Sprint 13 Planning Layer contracts.
- Capability ID source-of-truth decision.
- Evaluation fixtures for supported and unsupported goals.

## Sprint 15: Golden Paths

**Status:** Planned.

### Objectives

- Define canonical, repeatable workflows for supported banking goals.
- Turn existing supported capabilities into regression-grade end-to-end paths.

### Expected deliverables

- Versioned golden-path definitions for the currently registered capabilities.
- Deterministic fixtures and expected plans.
- Dry-run and mocked-runtime integration tests.
- Explicit success, failure, approval, verification, and recovery expectations.

### Success criteria

- Identical inputs produce equivalent approved plans.
- Golden paths verify runtime context propagation and business verification.
- No test requires uncontrolled production writes.

### Dependencies

- Accepted Planning Layer.
- Stable capability and execution-plan schemas.
- Safe Fineract test tenant or complete transport mocks.

## Sprint 16: Multi-Agent Collaboration

**Status:** Planned.

### Objectives

- Define controlled collaboration between specialized agents.
- Preserve one deterministic capability/runtime execution boundary.

### Expected deliverables

- Agent role and responsibility definitions.
- Typed handoff contracts.
- Shared-state and conflict-resolution rules.
- Human escalation and cancellation behavior.

### Success criteria

- No agent directly invokes Fineract.
- Agent disagreement produces review or rejection, not implicit execution.
- All accepted work resolves to the same capability and plan contracts.

### Dependencies

- Golden paths and evaluation fixtures.
- Stable planner and governance contracts.

## Sprint 17: Evaluation Framework

**Status:** Planned.

### Objectives

- Measure retrieval, classification, planning, validation, and workflow quality.
- Prevent regressions as model-assisted behavior grows.

### Expected deliverables

- Versioned evaluation datasets.
- Metrics for retrieval quality, goal accuracy, capability accuracy, payload validity, plan equivalence, and safe rejection.
- Offline evaluation runner and CI report.
- Failure taxonomy and baseline results.

### Success criteria

- Evaluations run without real banking writes.
- Baselines are reproducible.
- Release criteria identify unsafe regressions.

### Dependencies

- Golden paths.
- Stable API and planner contracts.
- Representative, non-sensitive test data.

## Sprint 18: Observability

**Status:** Planned expansion. Basic audit, timing, analytics, diagrams, and optional LangSmith traces are implemented.

### Objectives

- Make planning and execution decisions traceable across layers.
- Extend current runtime-only observability to planner, capability, and governance decisions.

### Expected deliverables

- Correlated request, planning, execution, and audit identifiers.
- Structured planner/capability decision events.
- Redaction policy and sensitive-field controls.
- Operational dashboards or exported metrics.
- Trace retention and failure-diagnosis guidance.

### Success criteria

- A workflow can be traced from request to verified outcome.
- Sensitive payloads are not emitted unredacted.
- Observability failures do not alter banking execution semantics.

### Dependencies

- Evaluation taxonomy.
- Stable event schemas and governance rules.
- Current audit and LangSmith foundations.

## Sprint 19: MCP Server

**Status:** Planned.

### Objectives

- Expose approved ADP capabilities through a Model Context Protocol server.
- Keep MCP as an interface to governed capabilities, not raw Fineract transport.

### Expected deliverables

- MCP server package and manifest/configuration.
- Read-only discovery resources for capabilities and schemas.
- Governed planning/dry-run tools.
- Authentication, authorization, and audit integration.

### Success criteria

- MCP clients cannot request arbitrary endpoints or methods.
- Every exposed operation maps to a registered capability.
- Write operations remain approval-gated and auditable.

### Dependencies

- Governance policy.
- Stable capability schemas and observability identifiers.

## Sprint 20: Governance

**Status:** Planned.

### Objectives

- Formalize authorization, policy, approval, risk, and audit requirements.
- Separate policy decisions from model and runtime implementation details.

### Expected deliverables

- Policy model and enforcement points.
- Role/tenant/capability authorization rules.
- Approval thresholds and segregation-of-duties rules.
- Data handling, redaction, retention, and audit policy.
- Emergency stop and incident procedures.

### Success criteria

- Unauthorized capabilities are rejected before execution.
- High-risk operations require explicit policy approval.
- Decisions are explainable and recorded.

### Dependencies

- Evaluation and observability foundations.
- Identity and deployment environment decisions.

## Sprint 21: Autonomous Banking Workflows

**Status:** Planned.

### Objectives

- Allow bounded autonomy only for evaluated, policy-approved workflows.
- Preserve human control for ambiguous or high-risk cases.

### Expected deliverables

- Autonomy levels and eligibility rules.
- Workflow budgets, timeouts, retries, and stop conditions.
- Human escalation and approval checkpoints.
- Simulation and rollback/compensation strategy where supported.

### Success criteria

- Autonomous execution is limited to allowlisted golden paths.
- Every action is policy-approved, observable, and auditable.
- Uncertainty or unexpected business state stops safely.

### Dependencies

- Governance, evaluations, golden paths, and production-grade observability.

## Sprint 22: AI Banking Platform v2

**Status:** Planned.

### Objectives

- Consolidate the validated ADP architecture into a versioned platform release.
- Define stable extension contracts for new banking domains and interfaces.

### Expected deliverables

- Versioned architecture and API contracts.
- Capability SDK or documented extension pattern.
- Migration plan from current modules and technical debt.
- Deployment, security, operations, and developer documentation.
- Release acceptance and compatibility policy.

### Success criteria

- New capabilities can be added without changing planner or runtime transport internals.
- Contracts are versioned and covered by evaluations.
- Security, governance, observability, and operational readiness criteria are met.

### Dependencies

- Completion and acceptance of Sprints 13-21.
- Proven golden paths and production environment decisions.

## Roadmap Maintenance Rules

1. Do not mark a sprint complete from code presence alone; link acceptance evidence.
2. Preserve **Planned** labels until implementation is merged and verified.
3. If historical evidence for Sprints 1-11 is recovered, update this file with links to commits, issues, or reports.
4. Update [SESSION_STATE.md](SESSION_STATE.md) whenever the active sprint or immediate TODO changes.
5. Record architectural changes in [DECISIONS.md](DECISIONS.md), not only in sprint prose.
