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

SYSTEM_PROMPT = """You are an internal AI assistant for banking engineering teams.
You help users understand Apache Fineract/Litecore behavior, APIs, and operational runbooks.
If you are unsure, say you don't know and ask for the missing documentation context.
Never invent endpoints or internal procedures."""
# Nota: todavía no hay RAG, así que esto es “best effort” con honestidad.

def ask_llm(user_message: str) -> str:
    safe_message = redact_secrets(user_message)

    logger.info("Solicitud al modelo (sanitizada).")  # log en español
    response = client.responses.create(
        model=settings.openai_model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": safe_message},
        ],
    )
    # output_text está en la guía de librerías / quickstart. :contentReference[oaicite:3]{index=3}
    return response.output_text

def ask_llm_rag(question: str, context: str) -> str:
    safe_question = redact_secrets(question)
    safe_context = redact_secrets(context)

    rag_system_prompt = (
        "You are an expert in Apache Fineract Legacy. "
        "Use ONLY the provided documentation excerpts. "
        "If the excerpts contain relevant fields or definitions, summarize them and answer the question. "
        "Only say you couldn't find it if the excerpts do NOT mention the relevant fields at all. "
        "When possible, list the exact field names (e.g., feeOnMonthDay, monthDayFormat, feeInterval) and what they mean."
    )

    rag_user_prompt = (
        f"Documentation excerpts:\n{safe_context}\n\n"
        f"User question:\n{safe_question}\n"
    )

    logger.info("Solicitud RAG al modelo (sanitizada).")  # log en español
    response = client.responses.create(
        model=settings.openai_model,
        reasoning={"effort": "minimal"},   # ✅ baja costo/tiempo para Q&A directo :contentReference[oaicite:2]{index=2}
        max_output_tokens=550,          # ✅ control de costo (incluye reasoning) :contentReference[oaicite:3]{index=3}
        input=[
            {"role": "system", "content": rag_system_prompt},
            {"role": "user", "content": rag_user_prompt},
        ],
    )
    return response.output_text

def ask_llm_rag_explain(question: str, context: str) -> str:
    safe_question = redact_secrets(question)
    safe_context = redact_secrets(context)

    system_prompt = (
        "You are an expert in Apache Fineract Legacy and banking systems. "
        "Use ONLY the provided documentation excerpts. "
        "If the excerpts contain relevant fields/definitions, answer the question concisely. "
        "Only say you couldn't find it if the excerpts do NOT mention the relevant fields at all. "
        "When possible, list the exact field names and their meaning."
    )

    user_prompt = (
        f"Documentation excerpts:\n{safe_context}\n\n"
        f"User question:\n{safe_question}\n"
    )

    logger.info("Solicitud RAG (explain) al modelo (sanitizada).")  # log en español
    response = client.responses.create(
        model=settings.openai_model,
        reasoning={"effort": "minimal"},
        max_output_tokens=650,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.output_text


def ask_llm_rag_sample(question: str, context: str) -> str:
    safe_question = redact_secrets(question)
    safe_context = redact_secrets(context)

    system_prompt = (
        "You are an expert in Apache Fineract Legacy APIs. "
        "Generate a SINGLE JSON request body that matches the user's request, "
        "using ONLY fields explicitly present in the provided documentation excerpts. "
        "Do NOT invent endpoints, commands, or fields. "
        "Type rules: IDs must be integers (e.g., chargeId), amount must be a string (e.g., \"25\", \"0.15\"). "
        "Consistency rules: feeOnMonthDay MUST match monthDayFormat "
        "(e.g., \"May-10\" -> \"MMMM-dd\"). "
        "If the excerpts do not explicitly mention the required fields for the requested payload, respond with exactly: "
        "\"INSUFFICIENT_EXCERPTS\" (no extra words). "
        "Return ONLY raw JSON (no markdown, no explanations)."
    )

    user_prompt = (
        f"Documentation excerpts:\n{safe_context}\n\n"
        f"User request:\n{safe_question}\n"
    )

    logger.info("Solicitud RAG (sample) al modelo (sanitizada).")  # log en español
    response = client.responses.create(
        model=settings.openai_model,
        reasoning={"effort": "minimal"},
        max_output_tokens=450,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.output_text

def ask_llm_rag_execution(question: str, context: str) -> str:
    safe_question = redact_secrets(question)
    safe_context = redact_secrets(context)

    system_prompt = (
        "You are an expert in Apache Fineract Legacy APIs. "
        "Use ONLY the provided documentation excerpts. "
        "Generate a SINGLE JSON object for execution planning. "
        "Return ONLY raw JSON with no markdown and no explanations. "
        "Do NOT invent fields not supported by the excerpts. "
        "For monthly savings charges, prefer the fields explicitly evidenced in the excerpts, "
        "including chargeId, amount, feeOnMonthDay, monthDayFormat, feeInterval, locale when relevant. "
        "If the excerpts are insufficient to fully populate all fields, still return a JSON object with the best possible structure. "
        "Use null for unknown fields. Do not refuse. "
    )

    user_prompt = (
        f"Documentation excerpts:\n{safe_context}\n\n"
        f"User request:\n{safe_question}\n"
    )

    logger.info("Solicitud RAG (execution) al modelo (sanitizada).")
    response = client.responses.create(
        model=settings.openai_model,
        reasoning={"effort": "minimal"},
        max_output_tokens=450,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.output_text