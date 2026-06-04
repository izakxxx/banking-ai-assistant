from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agent.input_parser import parse_execution_command, parse_user_inputs
from app.agent.session_store import session_store
from app.capabilities.models import MultiStepExecutionPlan
from app.execution.executor import dry_run_execution, execute_plan_real
from app.langgraph_workflow.state import FineractAgentState
from app.services.execution_service import build_execution_plan
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from pathlib import Path

CHECKPOINT_DIR = Path("data/checkpoints")
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

CHECKPOINT_DB = CHECKPOINT_DIR / "langgraph.db"

sqlite_conn = sqlite3.connect(
    str(CHECKPOINT_DB),
    check_same_thread=False,
)

checkpointer = SqliteSaver(sqlite_conn)

def parse_input_node(state: FineractAgentState) -> FineractAgentState:
    question = state.get("question") or ""
    initial_payload = state.get("initial_payload") or {}

    parsed = parse_user_inputs(question)

    return {
        **state,
        "initial_payload": {
            **initial_payload,
            **parsed,
        },
        "command": parse_execution_command(question),
    }


def load_session_node(state: FineractAgentState) -> FineractAgentState:
    session_id = state["session_id"]
    session = session_store.get(session_id)

    if session.get("execution_plan"):
        return {
            **state,
            "execution_plan": MultiStepExecutionPlan(**session["execution_plan"]),
            "intent": session.get("intent"),
            "approval_required": True,
        }

    return state


def build_plan_node(state: FineractAgentState) -> FineractAgentState:
    intent, plan, validation = build_execution_plan(
        question=state.get("question"),
        payload=state.get("initial_payload") or {},
        account_id=state.get("account_id"),
        tenant_id=state.get("tenant_id") or "default",
        intent=state.get("intent"),
    )

    validation_dict = (
        validation.model_dump()
        if hasattr(validation, "model_dump")
        else dict(validation)
    )

    if plan is not None:
        session_store.set(state["session_id"], {
            "intent": intent,
            "payload": state.get("initial_payload") or {},
            "execution_plan": plan.model_dump(),
            "status": "approval_required",
        })

    return {
        **state,
        "intent": intent,
        "execution_plan": plan,
        "validation": validation_dict,
        "approval_required": plan is not None,
        "approved": False,
    }


def approval_node(state: FineractAgentState) -> FineractAgentState:
    command = state.get("command")

    approved = command in {
        "execute",
        "confirm",
    }

    return {
        **state,
        "approved": approved,
    }


def dry_run_node(state: FineractAgentState) -> FineractAgentState:
    plan = state.get("execution_plan")

    if plan is None:
        return {
            **state,
            "execution_result": {
                "status": "no_pending_plan",
                "message": "There is no execution plan pending for this session.",
            },
        }

    result = dry_run_execution(
        plan=plan,
        session_id=state["session_id"],
    )

    return {
        **state,
        "execution_result": result,
    }


def execute_node(state: FineractAgentState) -> FineractAgentState:
    plan = state.get("execution_plan")

    if plan is None:
        return {
            **state,
            "execution_result": {
                "status": "no_pending_plan",
                "message": "There is no execution plan pending for this session.",
            },
        }

    result = execute_plan_real(
        plan=plan,
        session_id=state["session_id"],
        tenant_id=state.get("tenant_id") or "default",
    )

    session_store.clear(state["session_id"])

    return {
        **state,
        "execution_result": result,
        "approved": True,
    }


def final_response_node(state: FineractAgentState) -> FineractAgentState:
    result = state.get("execution_result")
    validation = state.get("validation") or {}
    plan = state.get("execution_plan")

    if result:
        answer = result.get("message", "Execution finished.")

    elif validation and not validation.get("is_valid", True):
        errors = validation.get("errors", [])
        answer = f"Missing or invalid inputs: {', '.join(errors)}"

    elif plan and state.get("approval_required"):
        answer = (
            "Execution plan is ready and awaiting approval. "
            "Send 'execute' to continue."
        )

    elif plan:
        answer = "Execution plan is ready. Confirm if you want to run dry-run or execute."

    else:
        answer = "Could not build an execution plan."

    return {
        **state,
        "final_answer": answer,
    }


def route_after_session(state: FineractAgentState) -> str:
    command = state.get("command")
    has_plan = state.get("execution_plan") is not None

    if command == "dry_run":
        return "dry_run"

    if command == "execute":
        return "approval"

    if has_plan:
        return "final_response"

    return "build_plan"


def route_after_plan(state: FineractAgentState) -> str:
    validation = state.get("validation") or {}

    if validation and not validation.get("is_valid", True):
        return "final_response"

    return "final_response"


def route_after_approval(state: FineractAgentState) -> str:
    if state.get("approved"):
        return "execute"

    return "final_response"


def build_fineract_agent_graph():
    graph = StateGraph(FineractAgentState)

    graph.add_node("parse_input", parse_input_node)
    graph.add_node("load_session", load_session_node)
    graph.add_node("build_plan", build_plan_node)
    graph.add_node("approval", approval_node)
    graph.add_node("dry_run", dry_run_node)
    graph.add_node("execute", execute_node)
    graph.add_node("final_response", final_response_node)

    graph.add_edge(START, "parse_input")
    graph.add_edge("parse_input", "load_session")

    graph.add_conditional_edges(
        "load_session",
        route_after_session,
        {
            "build_plan": "build_plan",
            "dry_run": "dry_run",
            "approval": "approval",
            "final_response": "final_response",
        },
    )

    graph.add_conditional_edges(
        "build_plan",
        route_after_plan,
        {
            "final_response": "final_response",
        },
    )

    graph.add_conditional_edges(
        "approval",
        route_after_approval,
        {
            "execute": "execute",
            "final_response": "final_response",
        },
    )

    graph.add_edge("dry_run", "final_response")
    graph.add_edge("execute", "final_response")
    graph.add_edge("final_response", END)

    return graph.compile(checkpointer=checkpointer)


fineract_agent_graph = build_fineract_agent_graph()