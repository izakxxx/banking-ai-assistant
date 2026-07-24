# Sprint 13.1 Validation Report

Validation date: 2026-07-14  
Repository: `D:\LocalRepo\banking-ai-assistant`  
Validation method: repository inspection, AST boundary scan, repository unit tests, direct service checks, FastAPI `TestClient`, controlled regression mocks, compilation/import checks, and Git whitespace validation.

## Executive Summary

- Overall status: **FAIL**
- Repository unit tests run: **6**
- Passed: **6**
- Failed: **0**
- Skipped/not executable as a repository test: **1 PowerShell endpoint suite**
- Additional validation performed: five direct planner scenarios, five structured-payload API scenarios, three message-only API probes, two payload-merge probes, thirteen regression checks, static AST inspection, 38 module imports, compilation, dependency, and Git checks.
- Environment limitations:
  - No real Apache Fineract requests were allowed or executed.
  - OpenAI, LangSmith, and external retrieval integrations were not exercised.
  - `test/test_endpoints.ps1` requires a persistent server and references routes that are not registered by the current application. It was inspected and its route coverage was checked through `TestClient`; it was not run against a live server.
  - No repository-configured formatter, linter, or type checker was found. `ruff`, `flake8`, `mypy`, and `black` are not installed in the project virtual environment.

The Planning Layer is statically isolated from HTTP and runtime execution details. Deterministic goal classification, capability selection, existing capability validation, and execution-plan compilation work when a complete structured payload is supplied. Sprint closure is blocked by three end-to-end contract issues:

1. Values embedded in the natural-language request are not parsed or merged by `PlannerService`, so the exact message-only scenarios do not produce plans even when the message contains `chargeId`, `amount`, or `accountId`.
2. The API serializes `GoalType` as uppercase values such as `PAY_SAVINGS_CHARGE`, while the requested contract expects lowercase snake case such as `pay_savings_charge`.
3. In the existing non-explicit execution-service branch, parsed LLM values override explicit structured payload values on key collisions. The controlled test changed explicit `amount=50` to parsed `amount=99`.

## Architecture Validation

### Planning/runtime boundary

**Status: PASS**

Every Python file under `app/planning/` was parsed through the Python AST. No prohibited imports, symbols, endpoint literals, or HTTP method constants were found.

Checked files:

- `app/planning/__init__.py`
- `app/planning/planner_models.py`
- `app/planning/goal_classifier.py`
- `app/planning/path_planner.py`
- `app/planning/planner_service.py`

The AST scan found no use of:

- `httpx`
- `requests`
- `FineractClient`
- `fineract_client`
- `/api/v1/`
- HTTP execution method literals (`POST`, `GET`, `PUT`, `DELETE`, `PATCH`)
- direct request calls
- runtime context, tool registry, business verification, or executor imports

Relevant boundaries:

- `GoalClassifier.classify()` only normalizes text and applies deterministic regular expressions: `app/planning/goal_classifier.py:47-60`.
- `PathPlanner.plan()` only maps `GoalType` to `CapabilityInvocation` objects: `app/planning/path_planner.py:11-31`.
- `PlannerService.plan()` classifies, selects a path, resolves the registry entry, and delegates compilation: `app/planning/planner_service.py:39-100`.
- Capability sanitization, validation, and plan construction remain in `build_execution_plan()`: `app/services/execution_service.py:90-115`.
- HTTP resolution and execution remain in the runtime: `app/execution/executor.py:27-45` and `app/execution/executor.py:93-180`.
- Fineract HTTP calls remain in `app/execution/fineract_client.py:22-100`.
- REST endpoint and method definitions remain in `app/execution/tool_registry.py:15-65`.

The Planning Layer imports `MultiStepExecutionPlan` as the required output type (`app/planning/planner_models.py:8,48`) but does not inspect or create its HTTP fields. This is an output contract dependency, not direct execution logic.

### Planning/capability boundary

**Status: PASS WITH FINDINGS**

The planner does not duplicate capability validation. `PlannerService` delegates to `build_execution_plan()` at `app/planning/planner_service.py:85-92`. The execution service resolves the existing capability, calls `sanitize()`, calls `validate()`, and only then calls `build_plan()` at `app/services/execution_service.py:90-115`.

Missing-field tests returned errors authored by existing capability validators:

```text
Missing savingsAccountChargeId.
Missing amount.
Missing dueDate.
```

The capability registry remained the source used for resolution (`app/capabilities/registry.py:11-26`). However, capability identifiers are duplicated in a Planning enum (`app/planning/planner_models.py:22-25`) and the registry (`app/capabilities/registry.py:13-16`), creating a low-level drift risk.

### Responsibility separation

| Responsibility | Owning component | Result |
|---|---|---|
| Natural language request to `GoalType` | `GoalClassifier` | PASS |
| `GoalType` to `ExecutionPath` | `PathPlanner` | PASS |
| Classification, path selection, registry resolution, compilation delegation | `PlannerService` | PASS |
| Payload sanitization and validation | Capability Layer through `build_execution_plan()` | PASS |
| Execution-plan creation | Capability Layer | PASS |
| HTTP resolution, execution, retries, and business verification | Runtime Layer | PASS |

### Boundary flow confirmation

The implemented flow is:

```text
Natural language request
    -> GoalClassifier
    -> PathPlanner
    -> registered root capability selection
    -> existing build_execution_plan()
    -> capability sanitize/validate/build_plan
    -> MultiStepExecutionPlan
```

The Planning Layer does not directly create REST calls. The onboarding path currently selects one registered composite capability, `onboard_client_with_savings_fee`, which expands to six execution steps. `PlannerService` explicitly rejects paths containing anything other than one root capability at `app/planning/planner_service.py:75-83`. This limits the advertised ordered multi-capability path model and is recorded as a finding.

## Test Results

### Repository planning tests

Command:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s test -p "test_*.py" -v
```

Result:

```text
Ran 6 tests in 0.003s
OK
```

All six tests in `test/test_planning.py` passed:

- three supported classifier examples
- unknown classifier result
- onboarding composite path mapping
- existing capability validation propagation
- explicit capability delegation to the execution-plan builder
- unknown goal does not compile a plan

### Scenario A: Pay savings charge

- Input: `pay savings account charge accountId=1 chargeId=2 amount=50`
- Detected goal: `GoalType.PAY_SAVINGS_CHARGE`
- Serialized goal: `PAY_SAVINGS_CHARGE`
- Selected capability: `pay_savings_charge`
- Complete structured payload used for the successful variant: `savingsAccountChargeId=2`, `amount=50`, `dueDate="14 July 2026"`, `account_id=1`
- Validation result with structured payload: valid, no errors
- Execution plan generated with structured payload: yes, one step
- Message-only result: no plan; missing `savingsAccountChargeId`, `amount`, and `dueDate`
- Status: **FAIL for the exact message-only contract; PASS when complete structured payload is supplied**
- Relevant output excerpt:

```text
goal=PAY_SAVINGS_CHARGE
capability=pay_savings_charge
structured_payload_plan=true
message_only_plan=false
message_only_errors=[Missing savingsAccountChargeId., Missing amount., Missing dueDate.]
```

The input names `chargeId`, while the payment capability requires `savingsAccountChargeId`. It also omits the capability-required `dueDate`.

### Scenario B: Create monthly savings fee

- Input: `apply a monthly maintenance fee of 15 to savings account 27 chargeId=3`
- Detected goal: `GoalType.CREATE_SAVINGS_MONTHLY_FEE`
- Serialized goal: `CREATE_SAVINGS_MONTHLY_FEE`
- Selected capability: `create_savings_monthly_fee`
- Complete structured payload used for the successful variant: `chargeId=3`, `amount=15`, `account_id=27`
- Validation result with structured payload: valid, no errors
- Execution plan generated with structured payload: yes, one step
- Message-only result: no plan; missing `chargeId` and `amount`
- Status: **FAIL for the exact message-only contract; PASS when structured payload is supplied**
- Relevant output excerpt:

```text
goal=CREATE_SAVINGS_MONTHLY_FEE
capability=create_savings_monthly_fee
structured_payload_plan=true
message_only_plan=false
message_only_errors=[Missing chargeId., Missing amount.]
```

### Scenario C: Customer onboarding

- Input: `create a new client with a savings account and monthly fee`
- Detected goal: `GoalType.ONBOARD_CUSTOMER_WITH_SAVINGS_FEE`
- Serialized goal: `ONBOARD_CUSTOMER_WITH_SAVINGS_FEE`
- Selected capability: `onboard_client_with_savings_fee`
- Validation with complete structured onboarding payload: valid, no errors
- Execution plan generated with complete structured payload: yes, six steps
- Message-only result: capability selected safely, no plan, missing customer/account/fee fields returned
- Status: **PASS for goal and capability selection; serialized goal contract differs; plan requires structured data**
- Relevant output excerpt:

```text
goal=ONBOARD_CUSTOMER_WITH_SAVINGS_FEE
capability=onboard_client_with_savings_fee
execution_plan_steps=6
```

### Scenario D: Unknown goal

- Input: `show me the weather tomorrow`
- Detected goal: `GoalType.UNKNOWN`
- Serialized goal: `UNKNOWN`
- Selected capability: none
- Validation result: `The request does not match a supported banking goal.`
- Execution plan generated: no
- Status: **PASS for safe behavior; serialized goal contract differs from lowercase `unknown`**
- Relevant output excerpt:

```text
goal=UNKNOWN
capabilities=[]
execution_plan=null
validation_errors=[The request does not match a supported banking goal.]
```

### Scenario E: Missing required fields

- Input: `pay a savings account charge`
- Detected goal: `GoalType.PAY_SAVINGS_CHARGE`
- Serialized goal: `PAY_SAVINGS_CHARGE`
- Selected capability: `pay_savings_charge`
- Validation result: missing `savingsAccountChargeId`, `amount`, and `dueDate`
- Execution plan generated: no
- Unsafe execution: none
- Status: **PASS for safe validation behavior; serialized goal contract differs**
- Relevant output excerpt:

```text
capability=pay_savings_charge
execution_plan=null
validation_errors=[Missing savingsAccountChargeId., Missing amount., Missing dueDate.]
```

### Scenario F: Payload merge

Two controlled execution-service branches were tested without external calls.

Non-explicit intent branch:

```text
explicit payload: {amount: 50, explicitOnly: explicit}
parsed payload:   {amount: 99, parsedOnly: parsed}
merged payload:   {amount: 99, explicitOnly: explicit, parsedOnly: parsed}
```

The behavior is deterministic, but parsed values override explicit values because the merge order is `{**payload, **llm_payload}` at `app/services/execution_service.py:66-69`.

Planner branch:

```text
explicit_intent=pay_savings_charge
returned payload={amount: 50, explicitOnly: explicit}
parsed branch executed=false
```

`PlannerService` always supplies an explicit capability ID. Therefore `build_plan_with_llm_payload()` returns immediately at `app/services/execution_service.py:46-47`, and no parsed values are merged into the planner payload.

- Status: **FAIL against the requested planner payload-merge objective**

## API Test Results

Endpoint: `POST /planning/debug`  
Client: FastAPI `TestClient`  
Fineract protection: `fineract_client.request` and `authenticate` were patched to raise if called. Both call counts were zero.

The response schema was stable across all five structured API scenarios:

```text
debug
execution_path
execution_plan
goal
validation_errors
validation_warnings
```

| Scenario | Request summary | HTTP | Goal returned | Capability | Plan | Validation | Result |
|---|---|---:|---|---|---|---|---|
| A | Pay charge plus complete structured payload | 200 | `PAY_SAVINGS_CHARGE` | `pay_savings_charge` | Yes | No errors | Behavior pass; lowercase goal contract fail |
| B | Monthly fee plus complete structured payload | 200 | `CREATE_SAVINGS_MONTHLY_FEE` | `create_savings_monthly_fee` | Yes | No errors | Behavior pass; lowercase goal contract fail |
| C | Onboarding plus complete structured payload | 200 | `ONBOARD_CUSTOMER_WITH_SAVINGS_FEE` | `onboard_client_with_savings_fee` | Yes, 6 steps | No errors | Behavior pass; lowercase goal contract fail |
| D | Weather request | 200 | `UNKNOWN` | None | No | Unsupported goal error | Safe behavior pass; lowercase goal contract fail |
| E | Pay charge with missing fields | 200 | `PAY_SAVINGS_CHARGE` | `pay_savings_charge` | No | Three missing-field errors | Safe behavior pass; lowercase goal contract fail |

Useful debug keys were present:

```text
classifier
planning_mode
registered_capabilities
request
selected_capabilities
resolved_intent (supported goals only)
```

No real Fineract authentication or request was executed:

```text
fineract.request call count = 0
fineract.authenticate call count = 0
```

Message-only API probes confirmed that values embedded in scenario A and B text are not extracted by this endpoint. The classifier and capability are correct, but plans remain absent because the structured payload is empty.

## Regression Results

### Existing repository tests

| Test artifact | Result | Notes |
|---|---|---|
| `test/test_planning.py` | PASS | 6 tests passed |
| `test/test_health.py` | NO TESTS | File is empty (0 bytes) |
| `test/test_endpoints.ps1` | NOT EXECUTED / STALE | Requires a persistent server and tests routes absent from the current app |

`test/test_endpoints.ps1:21-30` references `/search`, `/semantic-search`, `/hybrid-search`, `/answer-draft`, `/chat`, and `/chat-rag`. Route introspection confirmed all six are absent. This is an existing test-suite maintenance issue, not evidence that Sprint 13.1 removed those routes.

### Controlled regression harness

Thirteen checks were run. Twelve passed and one failed because of the stale PowerShell route expectations.

| Check | Result | Evidence |
|---|---|---|
| Capability registry contents | PASS | All 3 capabilities present |
| Capability resolution | PASS | All 3 resolve to implementations |
| Tool registry contents | PASS | All 8 tools present |
| Validator registry | PASS | Monthly-fee and payment validators present |
| Execution service explicit-intent path | PASS | Valid plan produced |
| Runtime dry run | PASS | `status=dry_run`, one step |
| Runtime real-execution guard | PASS | `status=blocked`, zero Fineract calls under disabled setting |
| Health endpoint | PASS | HTTP 200, `{"status":"ok"}` |
| `chat-docs` endpoint wiring | PASS | HTTP 200 with retrieval and LLM mocked |
| `chat-rag-graph` endpoint wiring | PASS | HTTP 200 with graph mocked |
| LangGraph state endpoint wiring | PASS | HTTP 200 with graph state mocked |
| LangGraph history endpoint wiring | PASS | HTTP 200 with graph history mocked |
| Legacy PowerShell routes present | FAIL | Six expected routes absent |

External behavior was deliberately not claimed:

- The real LangGraph planning/execution workflow was not invoked because it can call OpenAI and runtime services.
- `chat-docs` retrieval and OpenAI response generation were mocked.
- LangGraph endpoint wiring was tested with a fake graph object.
- Runtime dry-run and disabled-execution paths were tested; real runtime execution was not tested.
- Fineract authentication, reads, and writes were not tested.

## Code Quality Results

### Compilation

Command:

```powershell
.\.venv\Scripts\python.exe -m compileall -q app test
```

Result: **PASS** (`COMPILEALL:PASS`).

### Import checks

All modules discoverable through `pkgutil.walk_packages()` imported successfully:

```text
module_count=38
imported=38
failures=[]
```

Result: **PASS**. No circular import failure was observed.

### Dependency check

Command:

```powershell
.\.venv\Scripts\python.exe -m pip check
```

Result: **PASS** (`No broken requirements found.`).

### Formatting and linting

No formatter/linter/type-checker configuration was found beyond `pyproject.toml` project metadata. `ruff`, `flake8`, `mypy`, and `black` are not installed in `.venv`.

Result: **NOT AVAILABLE**. No lint result is claimed.

### Git whitespace check

Command:

```powershell
git -c safe.directory=D:/LocalRepo/banking-ai-assistant diff --check
```

Result: **PASS**. Git emitted only a line-ending warning for `app/api/routes.py` (`LF will be replaced by CRLF`), not a whitespace error.

### Mutable Pydantic defaults

Planning models use `Field(default_factory=...)` for list and dictionary fields at `app/planning/planner_models.py:34,39,49-51`. This is correct.

Pre-existing shared model definitions still use mutable literals:

- `app/capabilities/models.py:18,23-24,36-37`
- `app/schemas/chat.py:20,26-27,33`
- `app/validators/models.py:11,17-18`

Pydantic v2 normally copies these defaults per model instance, so no shared-state failure was observed. `default_factory` is still the clearer and safer style.

### Naming and magic strings

- Goal enum members and serialized values are uppercase: `app/planning/planner_models.py:11-15`.
- Capability enum values are lowercase registry intents: `app/planning/planner_models.py:22-25`.
- Registry intent strings are duplicated at `app/capabilities/registry.py:13-16`.
- Onboarding intentionally uses `CUSTOMER` in the goal and `client` in the existing capability intent.

No dead planning code was proven. `PlanningMode` currently has one value and is used only as request/debug metadata; this is acceptable for the first deterministic version.

## Findings

### Critical

No critical findings.

### High

#### H1. Explicit structured values can be overwritten by parsed LLM values

- Description: In the non-explicit execution-service path, `llm_payload` is expanded after the explicit payload. The controlled test changed explicit `amount=50` to parsed `amount=99`.
- Impact: A model-produced value can override an explicit banking amount or identifier. If this branch is used for execution planning, it can produce a materially different operation from the caller's structured input.
- File: `app/services/execution_service.py`
- Line: 66
- Recommended fix: Define and document payload precedence. Prefer trusted explicit structured input over parsed/model values (`{**llm_payload, **explicit_payload}`), reject conflicting critical fields, and add collision tests for amounts and resource identifiers.

#### H2. Planner does not consume parameter values embedded in natural-language requests

- Description: `PlannerService` classifies the message but passes only `PlanningRequest.payload` to the execution-plan builder. Supplying an explicit capability causes `build_plan_with_llm_payload()` to return before parsing. Exact message-only scenarios A and B selected the right capability but produced no plan.
- Impact: The advertised natural-language-to-deterministic-plan flow requires callers to separately construct a complete structured payload. Values such as `chargeId=3`, `amount=15`, and savings account `27` in the request are ignored by `/planning/debug`.
- File: `app/planning/planner_service.py`
- Line: 85
- Related file: `app/services/execution_service.py`
- Related line: 46
- Recommended fix: Add a deterministic parameter extraction/normalization stage outside the Planning Layer's capability-selection responsibility, merge it with explicit payload under a documented precedence rule, and map operation-specific aliases such as `chargeId` to `savingsAccountChargeId` only in the appropriate capability/input adapter.

### Medium

#### M1. API goal serialization does not match the requested lowercase contract

- Description: `GoalType` values serialize as uppercase strings, while validation expectations use `pay_savings_charge`, `create_savings_monthly_fee`, `onboard_customer_with_savings_fee`, and `unknown`.
- Impact: API consumers comparing against the specified lowercase values will fail even though classification is semantically correct.
- File: `app/planning/planner_models.py`
- Line: 11
- Recommended fix: Keep uppercase Python member names but assign lowercase enum values, then update contract tests and OpenAPI examples.

#### M2. PlannerService cannot compile an ordered path containing multiple capabilities

- Description: `ExecutionPath` is a list, but `PlannerService` returns a validation error unless the path contains exactly one capability. Onboarding is represented as one composite capability rather than the advertised ordered capability path.
- Impact: The first planning abstraction cannot yet express or compile a genuine multi-capability execution path without introducing another composite capability.
- File: `app/planning/planner_service.py`
- Line: 75
- Related file: `app/planning/path_planner.py`
- Related line: 11
- Recommended fix: In the next planning sprint, define how multiple capability outputs are composed into one execution plan, including step renumbering, dependencies, runtime context outputs, and validation aggregation. Do not move HTTP knowledge into Planning.

#### M3. Onboarding sanitization prints raw and normalized customer payloads

- Description: The onboarding capability writes the full raw and sanitized payload to stdout.
- Impact: Names, phone numbers, dates of birth, external IDs, and other customer data can appear in logs. The validation run observed four output lines for onboarding.
- File: `app/capabilities/savings/onboard_client_with_savings_fee.py`
- Line: 42
- Related line: 99
- Recommended fix: Remove direct prints. Use structured logging with redaction and avoid logging full banking/customer payloads.

#### M4. Existing PowerShell endpoint regression suite is stale

- Description: The endpoint script expects six routes not registered by the current application.
- Impact: The existing endpoint suite cannot provide a valid regression signal and will fail against a running current app.
- File: `test/test_endpoints.ps1`
- Line: 21
- Recommended fix: Replace it with `TestClient` tests for current routes, separating mocked unit/API wiring tests from optional external-integration tests.

### Low

#### L1. Capability identifiers have multiple sources of truth

- Description: `CapabilityId` repeats the same strings stored in `CapabilityRegistry` and individual capability `intent` fields.
- Impact: Adding or renaming a capability can leave the planner enum and registry inconsistent. The runtime check catches the mismatch only when planning is attempted.
- File: `app/planning/planner_models.py`
- Line: 22
- Related file: `app/capabilities/registry.py`
- Related line: 13
- Recommended fix: Define capability IDs in one dependency-neutral module or expose typed IDs from the capability registry without introducing a Planning-to-Runtime dependency.

#### L2. Pre-existing Pydantic models use mutable literal defaults

- Description: Several capability, chat, and validator models use `[]` and `{}` defaults instead of `Field(default_factory=...)`.
- Impact: Pydantic v2 currently protects instances by copying defaults, but the style is easy to misuse if models change or are converted to plain dataclasses/classes.
- File: `app/capabilities/models.py`
- Line: 18
- Recommended fix: Convert mutable model defaults to `Field(default_factory=list)` and `Field(default_factory=dict)` in a separate cleanup change with regression tests.

### Informational

#### I1. No lint/type-check toolchain is configured

- Description: No available repository command for `ruff`, `flake8`, `mypy`, or `black` was found.
- Impact: Compilation catches syntax/import issues but not style, unused symbols, or type inconsistencies.
- File: `pyproject.toml`
- Line: 1
- Recommended fix: Add a minimal, pinned quality toolchain and CI command in a later maintenance sprint.

#### I2. External integrations were intentionally not validated

- Description: Fineract, OpenAI, LangSmith, and real retrieval/embedding services were outside this safe validation run.
- Impact: This report does not establish external-service availability, authentication, request correctness, or real banking behavior.
- File: N/A
- Line: N/A
- Recommended fix: Maintain a separately gated integration suite using disposable test tenants and explicit write authorization.

## Final Acceptance Decision

**Sprint 13.1 is not ready to close under the stated end-to-end acceptance criteria.**

The architectural boundary is acceptable and the existing six unit tests pass. However, closure should wait until:

1. The expected serialized goal contract is decided and tested.
2. Natural-language parameter extraction/merging is connected to the planner flow or the API contract explicitly states that all execution fields must be supplied in `payload`.
3. Explicit-versus-parsed payload precedence is made safe for banking fields.
4. The intended single composite capability versus true ordered multi-capability path behavior is documented and tested.

The stale PowerShell endpoint suite and raw onboarding payload prints should also be addressed, but they are pre-existing issues rather than Planning Layer boundary violations.

## Recommended Next Step

Make the next Sprint 13 task a **Planner Input Contract and Safe Payload Resolution** sprint:

- define lowercase/uppercase API enum serialization explicitly;
- introduce deterministic parameter extraction outside the Planning Layer or clearly require structured payloads;
- define explicit payload precedence and conflict handling;
- add table-driven service and `TestClient` contract tests for scenarios A-F;
- specify how future multi-capability paths compose existing capability plans without exposing HTTP details to Planning.

Do not add execution logic to the Planning Layer and do not redesign the stable Runtime.

## Commands Executed

Primary validation commands:

```powershell
Get-ChildItem app\planning -File
Get-Content app\planning\*.py
Get-Content test\test_planning.py
Get-Content test\test_endpoints.ps1
rg -n -i "httpx|requests|FineractClient|fineract_client|/api/v1/|..." app\planning
rg -n "PAY_SAVINGS_CHARGE|CREATE_SAVINGS_MONTHLY_FEE|..." app test
.\.venv\Scripts\python.exe -m pip show pytest ruff flake8 mypy black
.\.venv\Scripts\python.exe -m unittest discover -s test -p "test_*.py" -v
.\.venv\Scripts\python.exe -m compileall -q app test
.\.venv\Scripts\python.exe -m pip check
git -c safe.directory=D:/LocalRepo/banking-ai-assistant diff --check
git -c safe.directory=D:/LocalRepo/banking-ai-assistant status --short
```

Inline Python validation harnesses were executed through the project virtual environment for:

```text
AST import/string boundary scan of app/planning
direct PlannerService scenarios A-E
controlled explicit/parsed payload merge behavior
FastAPI TestClient scenarios A-E with Fineract methods mocked
message-only API probes A-C
capability/tool/validator registry checks
execution-service explicit-intent check
runtime dry-run and disabled-real-execution checks
health/chat-docs/LangGraph endpoint wiring checks with external dependencies mocked
application route introspection for the legacy PowerShell suite
import of all 38 discoverable app modules
```

One initial regression harness run completed its product checks but failed while serializing a Python `set` in the harness output. It was immediately rerun with JSON-safe list details; no production code was changed.
