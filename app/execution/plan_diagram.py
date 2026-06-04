from __future__ import annotations

from app.capabilities.models import MultiStepExecutionPlan


def build_mermaid_diagram(plan: MultiStepExecutionPlan) -> str:
    lines = ["flowchart TD"]

    for step in plan.steps:
        node_id = f"S{step.step}"
        label = f"{step.step}. {step.action}"

        if step.is_verification:
            label = f"{label} ✅"

        lines.append(f'    {node_id}["{label}"]')

    for step in plan.steps:
        if step.depends_on:
            for dep in step.depends_on:
                lines.append(f"    S{dep} --> S{step.step}")
        elif step.step > 1:
            previous = step.step - 1
            lines.append(f"    S{previous} --> S{step.step}")

    return "\n".join(lines)