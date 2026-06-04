from __future__ import annotations

from typing import Any

from app.capabilities.models import MultiStepExecutionPlan
from app.core.config import settings
from app.execution.audit_log import write_audit_event
from app.execution.fineract_client import fineract_client, FineractExecutionError
from app.execution.plan_diagram import build_mermaid_diagram
from app.execution.runtime_context import RuntimeContext
from app.execution.template_resolver import extract_outputs, resolve_templates
from app.execution.tool_registry import tool_registry
from app.execution.verification import VerificationTracker
from app.recovery.error_classifier import ClassifiedError, classify_fineract_error
from app.recovery.recovery_policy import decide_recovery
from app.recovery.retry_engine import mutate_payload_for_retry
from app.observability.execution_trace import (
    duration_ms,
    isoformat,
    new_execution_id,
    now_utc,
)
from app.observability.langsmith_config import get_langsmith_client
from app.execution.business_verification import verify_business_state
from app.execution.business_router import build_business_followup_steps

def resolve_step_http(step, context_values: dict[str, Any]) -> tuple[str, str]:
    if step.tool:
        tool = tool_registry.get(step.tool)

        if tool is None:
            raise ValueError(f"No tool registered for: {step.tool}")

        method = tool.method
        endpoint_template = tool.endpoint_template
    else:
        if not step.method or not step.endpoint:
            raise ValueError(
                f"Step {step.step} must define either tool or method+endpoint."
            )

        method = step.method
        endpoint_template = step.endpoint

    resolved_endpoint = resolve_templates(endpoint_template, context_values)

    return method, resolved_endpoint


def should_auto_retry(
    classified_error: ClassifiedError,
    recovery_strategy: str,
) -> bool:
    return (
        classified_error == ClassifiedError.TEMPORARY_FAILURE
        and recovery_strategy == "RETRY_SAME_STEP"
    )


def dry_run_execution(
    plan: MultiStepExecutionPlan,
    session_id: str,
) -> dict[str, Any]:
    result = {
        "status": "dry_run",
        "message": "Dry run completed. No real API calls were executed.",
        "steps": [],
        "plan_diagram": build_mermaid_diagram(plan),
    }

    for step in plan.steps:
        result["steps"].append({
            "step": step.step,
            "action": step.action,
            "method": step.method,
            "endpoint": step.endpoint,
            "tool": step.tool,
            "payload": step.payload,
            "would_execute": True,
            "is_verification": step.is_verification,
        })

    write_audit_event({
        "session_id": session_id,
        "event_type": "dry_run",
        "plan": plan.model_dump(),
        "result": result,
    })

    return result


def execute_plan_real(
    plan: MultiStepExecutionPlan,
    session_id: str,
    tenant_id: str = "default",
) -> dict[str, Any]:
    if not settings.enable_real_execution:
        result = {
            "status": "blocked",
            "message": (
                "Real execution is disabled. "
                "Set ENABLE_REAL_EXECUTION=true only when you are ready."
            ),
            "steps": [step.model_dump() for step in plan.steps],
            "plan_diagram": build_mermaid_diagram(plan),
        }

        write_audit_event({
            "session_id": session_id,
            "event_type": "real_execution_blocked",
            "plan": plan.model_dump(),
            "result": result,
        })

        return result

    executed_steps: list[dict[str, Any]] = []
    runtime_context = RuntimeContext()
    verification_tracker = VerificationTracker()

    execution_id = new_execution_id()
    workflow_started_at = now_utc()
    
    langsmith_client = get_langsmith_client()
    trace_run = None
    if langsmith_client:
        try:
            trace_run = langsmith_client.create_run(
                name="fineract-agent-workflow",
                run_type="chain",
                inputs={
                    "session_id": session_id,
                    "intent": plan.intent,
                    "execution_id": execution_id,
                }
            )
        except Exception:
            trace_run = None

    steps_queue = list(plan.steps)
    step_index = 0

    while step_index < len(steps_queue):
        step = steps_queue[step_index]
        retry_attempted = False
        current_payload = step.payload

        step_started_at = now_utc()

        while True:
            try:
                context_values = runtime_context.get_all()

                resolved_method, resolved_endpoint = resolve_step_http(
                    step=step,
                    context_values=context_values,
                )

                resolved_payload = resolve_templates(
                    current_payload,
                    context_values,
                )

                step_run = None
                if langsmith_client and trace_run:
                    try: 
                        step_run = langsmith_client.create_run(
                            name=step.action,
                            run_type="tool",
                            inputs={
                                "payload": resolved_payload,
                                "endpoint": resolved_endpoint,
                                "method": resolved_method,
                            },
                            parent_run_id=trace_run.id,
                        )
                    except Exception:
                        step_run = None

                response = fineract_client.request(
                    method=resolved_method,
                    endpoint=resolved_endpoint,
                    payload=resolved_payload,
                    tenant_id=tenant_id,
                )

                if langsmith_client and step_run:
                    langsmith_client.update_run(
                        step_run.id,
                        outputs=response,
                        end_time=now_utc(),
                    )

                extracted_outputs = extract_outputs(
                    response=response,
                    output_mapping=step.output_mapping,
                )

                runtime_context.update(extracted_outputs)

                business_verification = None

                if step.is_verification:
                    business_verification = verify_business_state(
                        action=step.action,
                        response=response,
                    )

                    if business_verification.passed:
                        verification_tracker.mark_success(step)
                    else:
                        verification_tracker.mark_failure(step)
                else:
                    verification_tracker.mark_success(step)

                step_finished_at = now_utc()

                executed_steps.append({
                    "step": step.step,
                    "action": step.action,
                    "method": resolved_method,
                    "endpoint": resolved_endpoint,
                    "tool": step.tool,
                    "payload": resolved_payload,
                    "status": "success",
                    "response": response,
                    "extracted_outputs": extracted_outputs,
                    "runtime_context": runtime_context.get_all(),
                    "is_verification": step.is_verification,
                    "execution_id": execution_id,
                    "step_started_at": isoformat(step_started_at),
                    "step_finished_at": isoformat(step_finished_at),
                    "step_duration_ms": duration_ms(step_started_at, step_finished_at),
                    "business_verification": (
                        {
                            "passed": business_verification.passed,
                            "status": business_verification.status,
                            "message": business_verification.message,
                            "details": business_verification.details,
                        }
                        if business_verification
                        else None
                    ),
                })

                if business_verification and not business_verification.passed:
                    
                    followup_steps = build_business_followup_steps(
                        action=step.action,
                        business_status=business_verification.status,
                        context=runtime_context.get_all(),
                        next_step_number=len(steps_queue) + 1,
                    )

                    if followup_steps:
                        steps_queue.extend(followup_steps)

                break

            except FineractExecutionError as exc:
                if langsmith_client and step_run:
                    langsmith_client.update_run(
                        step_run.id,
                        error=str(exc),
                        end_time=now_utc(),
                    )

                classified_error = classify_fineract_error(
                    status_code=exc.status_code,
                    response_body=exc.response_body,
                )

                recovery_decision = decide_recovery(
                    action=step.action,
                    classified_error=classified_error,
                    response_body=exc.response_body,
                )

                auto_retry = should_auto_retry(
                    classified_error=classified_error,
                    recovery_strategy=recovery_decision.strategy,
                )

                if auto_retry and not retry_attempted:
                    retry_attempted = True

                    current_payload = mutate_payload_for_retry(
                        action=step.action,
                        payload=resolved_payload,
                    )

                    executed_steps.append({
                        "step": step.step,
                        "action": step.action,
                        "tool": step.tool,
                        "status": "retrying",
                        "reason": classified_error.value,
                        "recovery_strategy": recovery_decision.strategy,
                        "original_payload": resolved_payload,
                        "mutated_payload": current_payload,
                        "execution_id": execution_id,
                        "retry_timestamp": isoformat(now_utc()),
                        "business_verification": (
                            {
                                "passed": business_verification.passed,
                                "status": business_verification.status,
                                "message": business_verification.message,
                                "details": business_verification.details,
                            }
                            if business_verification
                            else None
                        ),
                    })

                    continue

                verification_tracker.mark_failure(step)

                runtime_plan = MultiStepExecutionPlan(
                        intent=plan.intent,
                        steps=steps_queue,
                    )

                failed_result = {
                    "status": "failed",
                    "message": str(exc),
                    "failed_step": step.step,
                    "failed_action": step.action,
                    "steps": executed_steps,
                    "runtime_context": runtime_context.get_all(),
                    "verification_summary": verification_tracker.get_summary(),
                    "plan_diagram": build_mermaid_diagram(runtime_plan),
                    "classified_error": classified_error.value,
                    "recovery": {
                        "can_retry": recovery_decision.can_retry,
                        "strategy": recovery_decision.strategy,
                        "message": recovery_decision.message,
                    },
                    "error": {
                        "status_code": exc.status_code,
                        "response_body": exc.response_body,
                    },
                }

                write_audit_event({
                    "session_id": session_id,
                    "event_type": "real_execution_failed",
                    "plan": plan.model_dump(),
                    "result": failed_result,
                })

                return failed_result
        
        step_index += 1

    workflow_finished_at = now_utc()

    runtime_plan = MultiStepExecutionPlan(
        intent=plan.intent,
        steps=steps_queue,
    )

    result = {
        "status": "executed",
        "message": "Execution completed successfully.",
        "steps": executed_steps,
        "runtime_context": runtime_context.get_all(),
        "verification_summary": verification_tracker.get_summary(),
        "execution_id": execution_id,
        "workflow_started_at": isoformat(workflow_started_at),
        "workflow_finished_at": isoformat(workflow_finished_at),
        "workflow_duration_ms": duration_ms(workflow_started_at, workflow_finished_at),
        "plan_diagram": build_mermaid_diagram(runtime_plan),
    }

    if langsmith_client and trace_run:
        langsmith_client.update_run(
            trace_run.id,
            outputs=result,
            end_time=now_utc(),
        )

    write_audit_event({
        "session_id": session_id,
        "event_type": "real_execution_success",
        "plan": plan.model_dump(),
        "result": result,
    })

    return result