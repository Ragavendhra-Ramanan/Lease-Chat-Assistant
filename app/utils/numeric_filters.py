import re
from datetime import datetime, timezone
from weaviate.collections.classes.filters import _FilterValue, _Operator

NUMERIC_FIELDS = ["price", "horsepower", "year", "mileage", "lease_term","monthlyEMI"]
DATE_FIELDS = {"lease_start_date": "leaseStartDate", "lease_expiry_date": "leaseExpiryDate"}

OP_MAP = {
    "<": _Operator.LESS_THAN,
    "<=": _Operator.LESS_THAN_EQUAL,
    ">": _Operator.GREATER_THAN,
    ">=": _Operator.GREATER_THAN_EQUAL,
    "=": _Operator.EQUAL
}

def to_datetime(date_str: str) -> datetime:
    # Convert YYYY-MM-DD to UTC datetime
    return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

def extract_filters(query: str):
    filters = []

    # Numeric filters
    for field in NUMERIC_FIELDS:
        match = re.search(rf"{field}\s*:?\s*(<=|>=|<|>|=)\s*(\d+)", query, re.IGNORECASE)
        if match:
            op_symbol = match.group(1) or "="
            operator = OP_MAP[op_symbol]
            value = int(match.group(2))
            filters.append(_FilterValue(value=value, operator=operator, target=field))

    # Date filters
    for key, prop_name in DATE_FIELDS.items():
        match = re.search(rf"{key}\s*:?\s*(<=|>=|<|>|=)\s*(\d{{4}}-\d{{2}}-\d{{2}})", query, re.IGNORECASE)
        if match:
            op_symbol = match.group(1) or "="
            operator = OP_MAP[op_symbol]
            value = to_datetime(match.group(2))
            filters.append(_FilterValue(value=value, operator=operator, target=prop_name))
    print(filters)
    return filters

