from __future__ import annotations

from app.validators.base import BasePreExecutionValidator
from app.validators.savings.create_monthly_fee_validator import CreateSavingsMonthlyFeePreExecutionValidator
from app.validators.savings.pay_charge_validator import PaySavingsChargePreExecutionValidator


class PreExecutionValidatorRegistry:
    def __init__(self) -> None:
        self._validators: dict[str, BasePreExecutionValidator] = {
            "create_savings_monthly_fee": CreateSavingsMonthlyFeePreExecutionValidator(),
            "pay_savings_charge": PaySavingsChargePreExecutionValidator(),
        }

    def get(self, intent: str) -> BasePreExecutionValidator | None:
        return self._validators.get(intent)


pre_execution_validator_registry = PreExecutionValidatorRegistry()