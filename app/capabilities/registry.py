from __future__ import annotations

from app.capabilities.base import BaseCapability
from app.capabilities.savings.create_monthly_fee import CreateSavingsMonthlyFeeCapability
from app.capabilities.savings.pay_charge import PaySavingsChargeCapability
from app.capabilities.savings.onboard_client_with_savings_fee import (
    OnboardClientWithSavingsFeeCapability,
)


class CapabilityRegistry:
    def __init__(self) -> None:
        self._capabilities: dict[str, BaseCapability] = {
            "create_savings_monthly_fee": CreateSavingsMonthlyFeeCapability(),
            "pay_savings_charge": PaySavingsChargeCapability(),
            "onboard_client_with_savings_fee": OnboardClientWithSavingsFeeCapability(),
        }

    def get(self, intent: str) -> BaseCapability | None:
        return self._capabilities.get(intent)

    def list_intents(self) -> list[str]:
        return list(self._capabilities.keys())


registry = CapabilityRegistry()