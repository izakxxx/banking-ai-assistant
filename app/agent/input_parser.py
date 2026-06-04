import re


def parse_user_inputs(text: str) -> dict:
    data = {}

    patterns = {
        "chargeId": r"chargeId\s*=?\s*(\d+)",
        "amount": r"amount\s*=?\s*([\d.]+)",
        "officeId": r"officeId\s*=?\s*(\d+)",
        "firstname": r"firstname\s*=?\s*([A-Za-z]+)",
        "lastname": r"lastname\s*=?\s*([A-Za-z]+)",
        "externalId": r"externalId\s*=?\s*([A-Za-z0-9\-_]+)",
        "mobileNo": r"mobileNo\s*=?\s*([\d]+)",
        "savingsProductId": r"savingsProductId\s*=?\s*(\d+)",
    }

    for field, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)

        if not match:
            continue

        value = match.group(1)

        if field in {
            "chargeId",
            "officeId",
            "savingsProductId",
        }:
            value = int(value)

        elif field == "amount":
            value = float(value)

        data[field] = value

    # fechas
    dob_match = re.search(
        r"dateOfBirth\s*=?\s*(\d{1,2}\s+\w+\s+\d{4})",
        text,
        re.IGNORECASE,
    )

    if dob_match:
        data["dateOfBirth"] = dob_match.group(1)

    submitted_match = re.search(
        r"submittedOnDate\s*=?\s*(\d{1,2}\s+\w+\s+\d{4})",
        text,
        re.IGNORECASE,
    )

    if submitted_match:
        data["submittedOnDate"] = submitted_match.group(1)

    return data


def parse_execution_command(text: str) -> str | None:
    q = text.lower().strip()

    if q in {"dry run", "dry-run", "simulate", "simulation", "simular"}:
        return "dry_run"

    if q in {"execute", "run", "confirm", "confirm execute", "ejecutar", "confirmar"}:
        return "execute"

    if q in {"cancel", "cancelar", "abort"}:
        return "cancel"

    return None