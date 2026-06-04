import os

from dotenv import load_dotenv
from pydantic import BaseModel

# Carga .env automáticamente cuando se ejecuta localmente.
# (En producción se recomienda usar variables de entorno del sistema.)
load_dotenv()


class Settings(BaseModel):
    app_name: str = "banking-ai-assistant"
    environment: str = os.getenv("ENVIRONMENT", "local")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5.2")
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
    fineract_base_url: str = "http://localhost:8443/litecore-provider"
    fineract_username: str = "mifos"
    fineract_password: str = "password"
    fineract_tenant_id: str = "default"
    enable_real_execution: bool = True

    def validate_required(self) -> None:
        if not self.openai_api_key:
            raise RuntimeError("Falta OPENAI_API_KEY. Configura el .env antes de iniciar.")


settings = Settings()
settings.validate_required()
