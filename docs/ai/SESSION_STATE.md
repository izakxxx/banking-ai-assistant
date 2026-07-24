# Session State

Last updated: 2026-07-14

This file is the handoff point for the next human or AI coding agent. Read [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) and [ARCHITECTURE.md](ARCHITECTURE.md) before acting on it.

## Current Sprint

**Sprint 13: Planning Layer, hardening phase.**

Sprint 13.1 code is implemented in the current worktree, but the end-to-end validation decision is **FAIL / not ready to close**. The current documentation task created the permanent `docs/ai/` knowledge base and did not change product behavior.

## Completed Sprint

- **Sprint 12 feature set:** Enterprise Retrieval capabilities are present in the worktree. Formal sprint closure evidence is not stored in the repository.
- **Sprints 1-11:** individual sprint completion is **Status not evidenced**. The repository collectively contains a substantial Core Runtime, but its historical sprint allocation is unknown.
- **Sprint 13.1:** not completed for acceptance purposes. Implementation exists; validation blockers remain.

## Current Milestone

Stabilize the first deterministic Planning Layer on top of the existing capability and runtime infrastructure, with explicit API and payload contracts, before adding LLM autonomy.

## Current Architecture Version

- Repository package version: `0.1.0` (`pyproject.toml`).
- Separate architecture version: **not defined in the repository**.
- Current descriptive state: layered ADP prototype with Enterprise Retrieval, deterministic Planning v1, registered capabilities, LangGraph orchestration, and a stable execution runtime foundation.

## Completed Features

### Retrieval and ingestion

- Markdown/text/HTML loading.
- Character chunking with overlap.
- Local chunk and vector indexes.
- BM25 retrieval.
- OpenAI embedding semantic retrieval.
- Weighted Reciprocal Rank Fusion.
- Intent-aware heuristic reranking.
- Context grouping, evidence classification, and evidence summaries.
- Retrieval and context debug data.

### Planning

- Typed goal, mode, capability, path, request, and result models.
- Deterministic classification for payment, monthly-fee, onboarding, and unknown goals.
- Static goal-to-root-capability path mapping.
- Capability Registry resolution.
- Delegation to the existing execution-plan builder.
- `POST /planning/debug`.
- Six passing planning unit tests.

### Capability and validation

- `create_savings_monthly_fee` capability.
- `pay_savings_charge` capability.
- `onboard_client_with_savings_fee` composite capability.
- Capability sanitization and local validation.
- Pre-execution validator registry.
- Fineract-backed account/charge read validations for monthly fee and charge payment.

### Execution and runtime

- Typed multi-step plans and steps.
- Tool Registry with eight tools.
- Dry-run representation and plan diagrams.
- Central Fineract authentication/request client.
- Template resolution and output extraction.
- Runtime Context propagation.
- Verification tracking.
- Business verification for client, savings account, and savings charge.
- Dynamic approval/activation follow-up steps.
- Error classification, recovery decisions, and one bounded temporary retry.

### Orchestration and observability

- LangGraph workflow and typed state.
- SQLite checkpointing.
- Process-local pending-plan session store.
- JSONL audit records.
- Execution IDs and timing.
- Execution analytics endpoint.
- Optional LangSmith traces.
- Graph state and history endpoints.

### Delivery

- FastAPI/Uvicorn application.
- Dockerfile.
- Docker Compose MariaDB and Litecore stack.
- GHCR build and external GitOps manifest update workflow.

## Pending Features

### Active Planning Layer work

- Decide and test serialized goal values.
- Define whether `/planning/debug` extracts message parameters or requires all execution fields in `payload`.
- Define safe explicit-versus-parsed payload precedence and conflict behavior.
- Map operation-specific field aliases safely.
- Design true ordered multi-capability path composition or explicitly retain root composite capabilities.
- Add complete service/API contract tests for validation scenarios A-F.

### Planned roadmap

- LLM Goal Planner, Capability Resolver, and governed Tool Calling.
- Golden Paths.
- Multi-Agent Collaboration.
- Evaluation Framework.
- Expanded Observability.
- MCP Server.
- Governance.
- Autonomous Banking Workflows.
- AI Banking Platform v2.

## Known Risks

1. **Explicit payload overwrite risk:** in the non-explicit execution-service branch, parsed LLM values override explicit values on duplicate keys.
2. **Natural-language parameter gap:** the planning route classifies message text but does not consume embedded execution parameters.
3. **API contract mismatch:** `GoalType` serializes uppercase while the Sprint validation contract expected lowercase snake case.
4. **Execution safety default:** `enable_real_execution` defaults to `True` in `app/core/config.py`.
5. **Credential/configuration risk:** default Fineract credentials and URL are hard-coded in settings.
6. **Sensitive logging:** onboarding sanitization prints raw and normalized customer payloads; execution service prints raw and parsed LLM responses.
7. **Session durability:** pending plans are stored in memory while LangGraph checkpoints are stored in SQLite.
8. **Debug exposure:** planning, retrieval, graph state, and history endpoints can expose internal/request data.
9. **External validation gap:** no real Fineract, OpenAI, LangSmith, or deployment integration was validated in Sprint 13.1 testing.
10. **Limited test suite:** health test is empty and the PowerShell endpoint suite is stale.

## Technical Debt

- Direct HTTP method/endpoint construction in two capability implementations.
- Execution plan models live under `app/capabilities/` although target ownership is the Execution Layer.
- Capability IDs are duplicated across enums, registries, validators, prompts, and implementation classes.
- Mutable literal defaults exist in several Pydantic models.
- Business follow-up dates and dependency assumptions are hard-coded.
- Auth recovery is represented by policy but not automatically applied by the executor.
- `app/agent/agent_service.py` is not wired to current API routes and overlaps some LangGraph responsibilities.
- `app/services/intent_classifier.py` includes intents with no registered capabilities.
- Raw payload/model-response `print()` calls remain.
- No formatter, linter, type checker, coverage threshold, or evaluation framework is configured.
- `pyproject.toml` and `requirements.txt` do not fully agree about SentenceTransformers.
- README is effectively empty; this knowledge base now carries project context.
- Git history does not preserve sprint acceptance evidence.

## Validation State

Source: [../../SPRINT_13_1_VALIDATION_REPORT.md](../../SPRINT_13_1_VALIDATION_REPORT.md)

- Overall Sprint 13.1 validation: **FAIL**.
- Planning unit tests: **6 passed, 0 failed**.
- Planning static boundary: **PASS**.
- Fineract calls during planning API validation: **0**.
- Compilation: **PASS**.
- Import check: **38/38 discoverable modules imported**.
- Dependency check: **PASS**.
- Git diff whitespace check: **PASS** with an LF/CRLF warning on `app/api/routes.py`.
- Controlled regression harness: **12 passed, 1 failed** because legacy endpoint-test routes are absent.

## Worktree State

At the start of this documentation task, the worktree already contained uncommitted changes in:

- `app/api/routes.py`
- retrieval modules and new retrieval files
- `docker-compose.yml`
- `requirements.txt`
- the new `app/planning/` package
- `test/test_planning.py`
- `SPRINT_13_1_VALIDATION_REPORT.md`

The `docs/ai/` files are additional documentation-only changes. Future agents must run `git status --short`, preserve unrelated user changes, and avoid assuming that all current files are committed to `main`.

## Next Sprint

Recommended next increment: **Sprint 13.2, Planner Input Contract and Safe Payload Resolution**.

This is a planned recommendation, not implemented work. It should close the current validation blockers before Sprint 14 introduces more LLM behavior.

## Immediate TODO

1. Review and approve the target API serialization for `GoalType`.
2. Decide whether planner requests are message-only, structured-payload-only, or deterministically merged.
3. Define explicit payload precedence and conflict rejection for amounts and identifiers.
4. Write an ADR for parameter extraction and merge ownership.
5. Add table-driven service and `TestClient` tests for scenarios A-F before changing implementation.
6. Resolve the Sprint 13.1 findings without redesigning the stable runtime.
7. Remove/redact raw payload and model-response prints.
8. Replace or update stale endpoint tests.
9. Re-run the validation report and change Sprint status only after all acceptance criteria pass.

## Next Recommended Prompt

```text
Read every file under docs/ai/ and SPRINT_13_1_VALIDATION_REPORT.md before changing code.

Implement Sprint 13.2: Planner Input Contract and Safe Payload Resolution.

First inspect the current worktree and preserve unrelated changes. Produce a short implementation plan. Then:

1. Define and test the serialized GoalType API contract.
2. Decide and implement deterministic parameter extraction or an explicit structured-payload-only planner contract.
3. Ensure trusted explicit payload values cannot be silently overwritten by parsed/model values.
4. Handle operation-specific aliases such as chargeId versus savingsAccountChargeId in the correct layer.
5. Add table-driven PlannerService and FastAPI TestClient tests for scenarios A-F.
6. Keep Planning free of HTTP, REST endpoints, Fineract clients, and execution logic.
7. Reuse CapabilityRegistry and build_execution_plan(); do not redesign the runtime.

Document defects before fixing architectural issues, update docs/ai/, and do not perform real Fineract writes.
```

## Handoff Checklist For Future Agents

- [ ] Read all `docs/ai/` documents.
- [ ] Read the Sprint 13.1 validation report.
- [ ] Run `git status --short` and preserve existing changes.
- [ ] Confirm the active sprint and acceptance criteria.
- [ ] Inspect current code before trusting roadmap statements.
- [ ] Keep model, planning, capability, and runtime boundaries intact.
- [ ] Use mocked transport unless real integration is explicitly authorized.
- [ ] Update this file before ending a substantive development session.
