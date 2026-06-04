from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


class FineractExecutionError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: Any | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class FineractClient:
    def __init__(self) -> None:
        self.base_url = settings.fineract_base_url.rstrip("/")
        self.timeout = settings.request_timeout_seconds
        self._auth_key: str | None = None

    def authenticate(self, tenant_id: str | None = None) -> str:
        url = f"{self.base_url}/api/v1/authentication"

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Litecore-Platform-TenantId": tenant_id or settings.fineract_tenant_id,
        }

        payload = {
            "username": settings.fineract_username,
            "password": settings.fineract_password,
        }

        try:
            response = httpx.post(
                url=url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
        except httpx.TimeoutException as exc:
            raise FineractExecutionError("Fineract authentication timed out.") from exc
        except httpx.RequestError as exc:
            raise FineractExecutionError(f"Fineract authentication failed: {str(exc)}") from exc

        try:
            response_body = response.json()
        except Exception:
            response_body = response.text

        if response.status_code >= 400:
            raise FineractExecutionError(
                message=f"Fineract authentication returned HTTP {response.status_code}.",
                status_code=response.status_code,
                response_body=response_body,
            )

        auth_key = response_body.get("base64EncodedAuthenticationKey")

        if not auth_key:
            raise FineractExecutionError(
                message="Fineract authentication response did not include base64EncodedAuthenticationKey.",
                status_code=response.status_code,
                response_body=response_body,
            )

        self._auth_key = auth_key
        return auth_key

    def _headers(self, tenant_id: str | None = None) -> dict[str, str]:
        if not self._auth_key:
            self.authenticate(tenant_id=tenant_id)

        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Litecore-Platform-TenantId": tenant_id or settings.fineract_tenant_id,
            "Authorization": f"Basic {self._auth_key}",
        }

    def request(
        self,
        method: str,
        endpoint: str,
        payload: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{endpoint}"

        try:
            response = httpx.request(
                method=method.upper(),
                url=url,
                json=payload or {},
                headers=self._headers(tenant_id=tenant_id),
                timeout=self.timeout,
            )
        except httpx.TimeoutException as exc:
            raise FineractExecutionError("Fineract request timed out.") from exc
        except httpx.RequestError as exc:
            raise FineractExecutionError(f"Fineract request failed: {str(exc)}") from exc

        try:
            response_body = response.json()
        except Exception:
            response_body = response.text

        if response.status_code == 401:
            self._auth_key = None

        if response.status_code >= 400:
            raise FineractExecutionError(
                message=f"Fineract returned HTTP {response.status_code}.",
                status_code=response.status_code,
                response_body=response_body,
            )

        return {
            "status_code": response.status_code,
            "body": response_body,
        }


fineract_client = FineractClient()