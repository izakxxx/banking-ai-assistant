import logging
import os
from openai import OpenAI
from app.core.config import settings
from app.services.guardrails import redact_secrets

logger = logging.getLogger("openai_service")

def _build_client() -> OpenAI:
    # Según docs oficiales: OpenAI() lee OPENAI_API_KEY por defecto, pero validamos igual. :contentReference[oaicite:2]{index=2}
    api_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Falta OPENAI_API_KEY en variables de entorno.")
    return OpenAI(api_key=api_key)

client = _build_client()

def ask_llm_execution_payload_with_context(question: str, context: str) -> str:
    safe_question = redact_secrets(question)
    safe_context = redact_secrets(context)

    system_prompt = (
        "You are an AI planner for a banking workflow runtime. "
        "Return ONLY raw JSON. No markdown. No explanations. "
        "Supported intents: onboard_client_with_savings_fee, "
        "create_savings_monthly_fee, pay_savings_charge. "
        "Return exactly this structure: "
        "{\"intent\": string, \"payload\": object}. "
        "The payload MUST be a flat object. "
        "Do NOT return nested objects. "
        "Use ISO date format YYYY-MM-DD. "
        "Use null for missing values. "
        "Do not invent unsupported fields."
    )

    user_prompt = (
        f"Documentation excerpts:\n{safe_context}\n\n"
        f"User request:\n{safe_question}"
    )

    logger.info("Solicitud LLM para execution payload con contexto RAG.")

    response = client.responses.create(
        model=settings.openai_model,
        reasoning={"effort": "minimal"},
        max_output_tokens=700,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.output_text


def ask_llm_rag(question: str, context: str) -> str:
    safe_question = redact_secrets(question)
    safe_context = redact_secrets(context)

    system_prompt = (
        "You are an expert in Apache Fineract Legacy and banking systems. "
        "Use ONLY the provided documentation excerpts. "
        "Answer naturally and conversationally. "
        "If the excerpts contain relevant information, explain it clearly. "
        "When possible, mention exact field names, API parameters, endpoints, "
        "request body fields and their meaning. "
        "If the answer is not present in the provided excerpts, clearly say so. "
        "Do not invent documentation."
    )

    user_prompt = (
        f"Documentation excerpts:\n{safe_context}\n\n"
        f"User question:\n{safe_question}"
    )

    logger.info("Solicitud RAG conversacional al modelo.")

    response = client.responses.create(
        model=settings.openai_model,
        reasoning={"effort": "minimal"},
        max_output_tokens=900,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.output_text