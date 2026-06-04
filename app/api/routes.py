import logging
import json
from fastapi import APIRouter, HTTPException
from app.agent.session_store import session_store
from app.agent.input_parser import parse_execution_command
from app.capabilities.models import MultiStepExecutionPlan
from app.execution.executor import dry_run_execution, execute_plan_real
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.openai_service import (
    ask_llm,
    ask_llm_rag,
    ask_llm_rag_explain,
    ask_llm_rag_sample,
    ask_llm_rag_execution,
)
from app.services.execution_service import build_execution_plan, parse_llm_json
from app.retrieval.retriever import retrieve
from app.retrieval.semantic_retriever import semantic_retrieve
from app.retrieval.hybrid_retriever import hybrid_retrieve
from app.agent.agent_service import run_agent
from app.langgraph_workflow.graph import fineract_agent_graph
from app.observability.execution_analytics import build_execution_analytics

logger = logging.getLogger("routes")
router = APIRouter()

@router.get("/health")
def health() -> dict:
    return {"status": "ok"}

@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    try:
        answer = ask_llm(req.message)
        return ChatResponse(answer=answer, confidence="low", sources=[])
    except Exception as e:
        logger.exception("Error procesando /chat")  # log en español
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
def search(req: ChatRequest):
    return {"query": req.message, "results": retrieve(req.message)}

@router.post("/answer-draft")
def answer_draft(req: ChatRequest):
    results = retrieve(req.message, top_k=5)

    if not results:
        return {
            "question": req.message,
            "draft": "No relevant sources found in the local index. Please ingest more documents.",
            "sources": [],
        }

    bullets = []
    for r in results:
        bullets.append(f"- Source: {r['doc_id']} ({r['chunk_id']}) | score={r['score']}\n  Snippet: {r['snippet']}")

    draft = (
        "I found the following relevant excerpts in the documentation. "
        "Based on these sources, the likely answer involves savings charges configuration "
        "(e.g., monthly fee settings, fee interval, and due timing). "
        "Review the sources below for exact field definitions and behavior."
    )

    return {
        "question": req.message,
        "draft": draft,
        "sources": bullets,
    }

@router.post("/semantic-search")
def semantic_search(req: ChatRequest):
    return {
        "query": req.message,
        "results": semantic_retrieve(req.message),
    }

@router.post("/hybrid-search")
def hybrid_search(req: ChatRequest):
    return {
        "query": req.message,
        "results": hybrid_retrieve(req.message),
    }

def _build_context(results: list[dict], max_chars: int = 3500) -> tuple[str, list[dict]]:
    context_parts: list[str] = []
    sources: list[dict] = []
    used = 0

    for r in results:
        doc_id = r.get("doc_id", "unknown")
        chunk_id = r.get("chunk_id", "unknown")
        snippet = (r.get("snippet") or "").strip()
        if not snippet:
            continue

        block = f"[Source: {doc_id} | {chunk_id}]\n{snippet}\n"
        if used + len(block) > max_chars:
            break

        context_parts.append(block)
        used += len(block)

        sources.append({
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "score": r.get("score"),
            "sources": r.get("sources", []),
            "excerpt": snippet[:180],
        })

    return "\n".join(context_parts).strip(), sources

@router.post("/chat-rag", response_model=ChatResponse)
def chat_rag(req: ChatRequest) -> ChatResponse:
    try:
        retrieval_results = hybrid_retrieve(req.message, top_k=12)

        if req.mode == "sample":
            bad_terms = ("client charge", "loan charge")
        elif req.mode == "execution":
            bad_terms = ("client charge", "loan charge")
        else:
            bad_terms = ()

        filtered = []
        for r in retrieval_results:
            snip = (r.get("snippet") or "").lower()
            if bad_terms and any(t in snip for t in bad_terms):
                continue
            filtered.append(r)

        if len(filtered) >= 2:
            retrieval_results = filtered
        else:
            retrieval_results = retrieval_results[:5]

        context, sources = _build_context(retrieval_results, max_chars=5000)

        if not context:
            return ChatResponse(
                answer="I couldn't find relevant sources in the local index. Please ingest more documents.",
                confidence="low",
                sources=[],
            )

        if req.mode == "sample":
            answer = ask_llm_rag_sample(req.message, context).strip()

            if answer == "INSUFFICIENT_EXCERPTS":
                return ChatResponse(answer=answer, confidence="low", sources=sources)

            try:
                json.loads(answer)
            except Exception:
                return ChatResponse(answer=answer, confidence="low", sources=sources)

            confidence = "high" if len(sources) >= 3 else "medium"
            return ChatResponse(answer=answer, confidence=confidence, sources=sources)

        if req.mode == "execution":

            command = parse_execution_command(req.message)
            session = session_store.get(req.session_id or "default-session")

            if command and not session.get("execution_plan"):
                return ChatResponse(
                    answer="There is no execution plan pending for this session. Create a plan first.",
                    confidence="low",
                    sources=[],
                    execution_plan=None,
                    validation={
                        "is_valid": False,
                        "errors": ["No pending execution plan found in session."],
                        "warnings": [],
                    },
                    debug={
                        "status": "no_pending_plan",
                        "command": command,
                        "session": session,
                    } if req.debug else None,
                )

            if command and session.get("execution_plan"):
                plan = MultiStepExecutionPlan(**session["execution_plan"])

                if command == "cancel":
                    session_store.clear(req.session_id or "default-session")
                    return ChatResponse(
                        answer="Execution cancelled.",
                        confidence="high",
                        sources=[],
                        execution_plan=None,
                        validation=None,
                        debug={"status": "cancelled"} if req.debug else None,
                    )

                if command == "dry_run":
                    result = dry_run_execution(
                        plan=plan,
                        session_id=req.session_id or "default-session",
                    )
                    return ChatResponse(
                        answer=result["message"],
                        confidence="high",
                        sources=[],
                        execution_plan=plan,
                        validation=None,
                        debug=result if req.debug else None,
                    )

                if command == "execute":
                    result = execute_plan_real(
                        plan=plan,
                        session_id=req.session_id or "default-session",
                        tenant_id=req.tenant_id or "default",
                    )

                    confidence = "high" if result["status"] == "executed" else "medium"

                    return ChatResponse(
                        answer=result["message"],
                        confidence=confidence,
                        sources=[],
                        execution_plan=plan,
                        validation=None,
                        debug=result if req.debug else None,
                    )

            raw_answer = ask_llm_rag_execution(req.message, context).strip()

            if raw_answer == "INSUFFICIENT_EXCERPTS":
                raw_answer = "{}"

            payload = parse_llm_json(raw_answer)

            agent_result = run_agent(
                session_id=req.session_id or "default-session",
                question=req.message,
                initial_payload=payload,
                account_id=req.account_id,
                tenant_id=req.tenant_id or "default",
            )

            if agent_result["status"] == "needs_input":
                return ChatResponse(
                    answer=f"Missing required inputs: {', '.join(agent_result['missing_inputs'])}. Please provide them.",
                    confidence="medium",
                    sources=sources,
                    execution_plan=None,
                    validation=None,
                    debug=agent_result if req.debug else None,
                )

            if agent_result["status"] == "error":
                return ChatResponse(
                    answer=agent_result["message"],
                    confidence="low",
                    sources=sources,
                    execution_plan=None,
                    validation={
                        "is_valid": False,
                        "errors": agent_result.get("validation_errors", []),
                        "warnings": [],
                    },
                    debug=agent_result if req.debug else None,
                )
            
            if agent_result["status"] == "confirm_required":
                return ChatResponse(
                    answer=agent_result["message"],
                    confidence="high",
                    sources=sources,
                    execution_plan=agent_result["execution_plan"],
                    validation=None,
                    debug=agent_result if req.debug else None,
                )

            plan = agent_result["execution_plan"]

            return ChatResponse(
                answer="Execution plan ready.",
                confidence="high",
                sources=sources,
                execution_plan=plan,
                validation=None,
                debug=agent_result if req.debug else None,
            )

        answer = ask_llm_rag_explain(req.message, context)

        answer_l = answer.lower()
        if "couldn't find" in answer_l or "could not find" in answer_l:
            confidence = "low"
        else:
            must_terms = ("feeonmonthday", "monthdayformat", "feeinterval", "paycharge", "savingsaccounts")
            hits = 0
            for s in sources:
                excerpt = (s.get("excerpt") or "").lower()
                if any(t in excerpt for t in must_terms):
                    hits += 1

            if hits >= 2 and len(sources) >= 3:
                confidence = "high"
            elif len(sources) >= 2:
                confidence = "medium"
            else:
                confidence = "low"

        return ChatResponse(answer=answer, confidence=confidence, sources=sources)

    except Exception as e:
        logger.exception("Error procesando /chat-rag")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat-rag-graph", response_model=ChatResponse)
def chat_rag_graph(req: ChatRequest) -> ChatResponse:
    try:
        thread_id = req.session_id or "default-session"

        result = fineract_agent_graph.invoke(
            {
                "session_id": thread_id,
                "question": req.message,
                "initial_payload": {},
                "account_id": req.account_id,
                "tenant_id": req.tenant_id or "default",
            },
            config={
                "configurable": {
                    "thread_id": thread_id,
                }
            },
        )

        return ChatResponse(
            answer=result.get("final_answer", "Graph execution finished."),
            confidence="high",
            sources=[],
            execution_plan=result.get("execution_plan"),
            validation=result.get("validation"),
            debug=result if req.debug else None,
        )

    except Exception as e:
        logger.exception("Error procesando /chat-rag-graph")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/execution/analytics")
def execution_analytics():
    return build_execution_analytics()

@router.get("/chat-rag-graph/state/{thread_id}")
def get_graph_state(thread_id: str):
    try:
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        state = fineract_agent_graph.get_state(config)

        return {
            "thread_id": thread_id,
            "values": state.values,
            "next": state.next,
            "metadata": state.metadata,
            "config": state.config,
        }

    except Exception as e:
        logger.exception("Error obteniendo estado de LangGraph")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/chat-rag-graph/state/{thread_id}/history")
def get_graph_state_history(thread_id: str):
    try:
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        history = list(fineract_agent_graph.get_state_history(config))

        return {
            "thread_id": thread_id,
            "checkpoints": [
                {
                    "values": item.values,
                    "next": item.next,
                    "metadata": item.metadata,
                    "config": item.config,
                }
                for item in history
            ],
        }

    except Exception as e:
        logger.exception("Error obteniendo historial de LangGraph")
        raise HTTPException(status_code=500, detail=str(e))