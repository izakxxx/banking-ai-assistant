import logging

from fastapi import APIRouter, HTTPException
from app.schemas.chat import ChatRequest, ChatResponse
from app.langgraph_workflow.graph import fineract_agent_graph
from app.observability.execution_analytics import build_execution_analytics
from app.retrieval.hybrid_retriever import hybrid_retrieve
from app.services.openai_service import ask_llm_rag

logger = logging.getLogger("routes")
router = APIRouter()

@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


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

# ---------------------------------------------------------------------------------------------------------------

@router.post("/chat-docs", response_model=ChatResponse)
def chat_docs(req: ChatRequest) -> ChatResponse:
    try:
        results = hybrid_retrieve(req.message, top_k=5)

        context = "\n\n---\n\n".join(
            f"doc_id={r.get('doc_id')} chunk_id={r.get('chunk_id')} score={r.get('score')}\n"
            f"{r.get('snippet')}"
            for r in results
        )

        answer = ask_llm_rag(
            question=req.message,
            context=context,
        )

        return ChatResponse(
            answer=answer,
            confidence="high" if results else "low",
            sources=results,
            execution_plan=None,
            validation=None,
            debug={
                "retrieval_results": results,
                "context": context,
            } if req.debug else None,
        )

    except Exception as e:
        logger.exception("Error procesando /chat-docs")
        raise HTTPException(status_code=500, detail=str(e))