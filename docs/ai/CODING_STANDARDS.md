# Coding Standards

Last updated: 2026-07-14

## Purpose

These are normative standards for future work in AI Banking Lab. They describe the direction new code must follow. Existing deviations are not silently reclassified as compliant; they are listed in [SESSION_STATE.md](SESSION_STATE.md) and the Sprint 13.1 validation report.

## General Principles

1. Preserve deterministic banking behavior after natural-language interpretation.
2. Prefer composition over inheritance. Use inheritance only for small, stable interfaces such as `BaseCapability` and `BasePreExecutionValidator`.
3. Apply SOLID principles pragmatically:
   - one module or class should have one clear reason to change;
   - add new capabilities through registries and implementations, not conditionals spread across layers;
   - depend on typed contracts and injected collaborators where testing benefits;
   - keep interfaces narrow;
   - do not make high-level planning depend on low-level transport.
4. Reuse existing services, registries, models, and runtime behavior before adding abstractions.
5. Keep changes scoped. Do not redesign stable runtime components while adding a planning or AI feature.
6. Fail safely. Unsupported, ambiguous, or invalid input must produce no executable plan.
7. Never log secrets or complete customer/banking payloads.

## Layer Dependency Rules

Preferred dependency direction:

```text
API / Orchestration
    -> Retrieval and Planning
    -> Capability contracts
    -> Execution plans
    -> Runtime and transport
    -> Verification / Recovery / Observability
```

### Planning Layer

Planning may depend on:

- planning models;
- deterministic classifiers and path planners;
- capability identifiers and registry lookup contracts;
- capability validation/plan-building orchestration;
- the execution-plan output type.

Planning must never:

- import `httpx`, `requests`, or another HTTP client;
- import `FineractClient` or `fineract_client`;
- contain `/api/v1/` or other REST endpoint literals;
- select `GET`, `POST`, `PUT`, `PATCH`, or `DELETE` for execution;
- authenticate to Fineract;
- execute requests;
- implement retries, runtime context propagation, or business verification;
- duplicate capability sanitization or validation.

### Capability Layer

The Capability Layer owns business capabilities:

- supported intent/capability identity;
- input aliases and normalization;
- business-required fields;
- local validation;
- conversion of valid capability input into an execution plan.

All business workflows must execute through registered capabilities. Do not let an LLM, route, or planner construct arbitrary Fineract operations.

Target rule: capabilities should reference transport-neutral tools. Current `create_savings_monthly_fee` and `pay_savings_charge` capabilities contain direct method/endpoint steps; this is existing debt and must not be copied into new capabilities.

### Execution Plan Layer

The Execution Layer owns execution-plan contracts. Plans must be typed data, not executable callbacks.

Each step should declare:

- stable sequence and action identity;
- a registered tool name;
- payload;
- dependencies;
- output mappings;
- whether the step performs verification.

Avoid embedding generated curl commands and direct endpoints in new business capabilities. The current model lives in `app/capabilities/models.py`; moving it requires a separate compatibility-aware change.

### Runtime Layer

Runtime owns transport and execution:

- tool-to-method/endpoint resolution;
- authentication and tenant headers;
- template resolution;
- Fineract requests;
- output extraction and runtime context;
- retries and recovery application;
- business verification and follow-up routing;
- execution audit and traces.

Only the Runtime may perform Fineract writes. Read-only pre-execution validators currently call the shared Fineract client; do not add write behavior to validators.

### LLM Boundary

- An LLM may classify, extract, summarize, or propose.
- An LLM must never call Fineract directly.
- Model output must be parsed into a typed contract.
- Model-proposed goals must resolve to registered capabilities.
- Model-proposed fields must pass capability validation.
- Explicit caller values must not be silently overwritten by model output.
- Model failure, malformed output, or an unknown capability must produce a safe non-executable result.

## Python Standards

### Version and syntax

- Support the version declared in `pyproject.toml` (`>=3.11`).
- Use `from __future__ import annotations` in modules that benefit from forward references and modern union syntax.
- Prefer built-in generic types: `list[str]`, `dict[str, Any]`, `X | None`.
- Keep files ASCII unless an existing file requires another encoding. Fix mojibake instead of adding more.

### Typing

- Type public functions, methods, constructor parameters, and return values.
- Use `TypedDict`, Pydantic models, enums, dataclasses, or protocols for structured contracts.
- Avoid untyped `dict` at layer boundaries.
- Use `Any` only at external/raw-data boundaries, then validate or normalize promptly.
- Prefer enums over repeated strings for finite states, goals, modes, and error classes.

### Pydantic models

- Use Pydantic for API and cross-layer data contracts.
- Use `Field(default_factory=list)` and `Field(default_factory=dict)` for mutable defaults.
- Keep request, domain, plan, and response concerns separate when their ownership differs.
- Treat serialized enum values as API contracts; test them explicitly.
- Add schema examples only when they reflect real supported fields.

### Functions and classes

- Prefer small pure functions for normalization, mapping, parsing, and policy decisions.
- Inject collaborators when a service must be tested without external calls.
- Do not add a base class unless multiple implementations need a stable polymorphic contract.
- Avoid global mutable state. Existing caches, `SessionStore`, Fineract client, and SQLite connection are current exceptions that require care.

### Error handling

- Raise or return typed domain errors at layer boundaries.
- Preserve Fineract status and response details only where safe and necessary.
- Never catch broad exceptions without logging or returning a safe result at an API boundary.
- Retry only when a policy explicitly proves the retry is safe.
- Limit retries and record every retry decision.

## Naming Conventions

- Modules and functions: `snake_case`.
- Classes and Pydantic models: `PascalCase`.
- Constants and enum members: `UPPER_SNAKE_CASE`.
- Serialized capability IDs and intents: lowercase `snake_case`.
- Tool names: imperative lowercase `snake_case`, such as `create_client`.
- Verification actions: prefix with `verify_`.
- API routes: lowercase, hyphenated only where already established.
- Tests: `test_<behavior>_<expected_result>` where practical.

Do not create a second spelling for an existing capability. If domain language requires `customer` while Fineract uses `client`, document the mapping in one place.

## Folder Organization

```text
app/planning/       goal and capability-path reasoning only
app/capabilities/   business capability definitions
app/execution/      plan interpretation, transport, runtime context, verification
app/validators/     pre-execution checks
app/retrieval/      retrieval and context construction
app/ingestion/      source indexing
app/recovery/       error classification and recovery policy
app/observability/  traces and analytics
app/langgraph_workflow/ orchestration state and routing
app/api/            HTTP boundary
app/schemas/        shared API contracts
docs/ai/            permanent AI project knowledge
test/               automated tests
```

Do not place business logic in route functions. Do not place HTTP transport in Planning. Do not create broad `utils.py` modules when ownership is clear.

## Registries

- Register every supported capability in `CapabilityRegistry`.
- Register transport tools in `ToolRegistry`.
- Register external-state checks in `PreExecutionValidatorRegistry` when required.
- Registry keys must match typed IDs and implementation `intent` values.
- Add tests that fail if a declared path references an unregistered capability or tool.
- Avoid duplicating registry identifiers across prompts, enums, and modules without a single source of truth.

## Execution and Safety Standards

1. Validate locally before building a plan.
2. Perform required read-only pre-validation before approval/execution.
3. Produce a dry-run representation for new workflows.
4. Require explicit approval for real writes unless a future governance policy authorizes bounded autonomy.
5. Resolve all templates before transport.
6. Capture output mappings needed by later steps.
7. Verify business state after state-changing operations where a rule exists.
8. Stop safely on unknown failures or missing runtime values.
9. Audit success, failure, blocked execution, and recovery decisions.
10. Never use production credentials or tenants in unit tests.

## Security and Data Handling

- Load credentials from environment/secret stores; do not add hard-coded credentials.
- Redact API keys, authentication headers, customer identifiers, dates of birth, phone numbers, and payload bodies from logs unless a documented secure audit policy requires specific fields.
- Do not use `print()` for payloads or model responses in production paths.
- Separate debug output from normal API responses and protect it in deployed environments.
- Never include live secrets in fixtures, reports, prompts, or generated curl examples.
- Treat tenant ID as part of every Fineract request context.

## Testing Strategy

### Unit tests

Required for:

- goal classification and unknown-goal rejection;
- path mapping and registry resolution;
- capability sanitization and validation;
- template resolution and output extraction;
- error classification and recovery policy;
- business verification and follow-up routing;
- serialized API enum values and model defaults.

### Service tests

- Inject or patch retrieval, LLM, Fineract, audit, and LangSmith dependencies.
- Test explicit/parsed payload collisions.
- Verify invalid input never produces an executable plan.
- Verify capability validation is reused, not reimplemented.

### API tests

- Prefer FastAPI `TestClient` for deterministic route tests.
- Assert HTTP status, full response schema, goal serialization, path, validation, plan presence, and debug structure.
- Patch Fineract methods to raise if a planning-only route attempts transport.

### Runtime tests

- Use dry-run or mocked transport by default.
- Test runtime context propagation across multiple steps.
- Test success, business verification failure, follow-up routing, temporary retry, and safe failure.
- Real Fineract writes require explicit authorization, a disposable test tenant, and a separate integration marker.

### Regression and evaluation

- Keep all repository test scripts aligned with current routes.
- Do not count mocked wiring tests as external integration success.
- Record skipped external tests separately from code failures.
- Future model changes require versioned evaluation fixtures and baseline comparisons.

## Documentation Requirements

Update `docs/ai/` when a change affects:

- architecture or dependency boundaries;
- capability, tool, or validator registries;
- API contracts;
- execution-plan schema;
- runtime behavior, verification, recovery, or audit;
- sprint status, risks, technical debt, or next work.

Every new capability should document:

- intent and business purpose;
- required and optional fields;
- validation rules;
- execution steps and dependencies;
- runtime outputs;
- verification behavior;
- recovery constraints;
- tests.

Architectural changes require an ADR entry in [DECISIONS.md](DECISIONS.md).

## Pull Request Expectations

A pull request should include:

- a concise problem and scope statement;
- affected architecture layers;
- explicit non-goals;
- tests run and exact limitations;
- confirmation that no real Fineract write occurred, unless authorized;
- API or schema compatibility notes;
- security and tenant-impact notes;
- documentation updates;
- migration or rollback notes when contracts change.

Reviewers should reject a change that:

- lets Planning or an LLM call Fineract;
- bypasses capabilities;
- duplicates validation or runtime logic;
- silently changes explicit banking values;
- adds an unregistered tool or capability;
- claims external integration success from mocks;
- logs secrets or raw customer payloads;
- marks planned work complete without acceptance evidence.

## Current Known Deviations

Do not copy these patterns into new code:

- direct endpoint/method construction in two capabilities;
- mutable literal defaults in existing Pydantic models;
- raw payload and model-response `print()` calls;
- hard-coded Fineract credentials and real-execution default;
- hard-coded business follow-up dates;
- process-local session storage paired with persistent checkpoints;
- duplicate intent strings across registries, enums, prompts, and implementations;
- stale PowerShell endpoint tests.

Track remediation status in [SESSION_STATE.md](SESSION_STATE.md).
