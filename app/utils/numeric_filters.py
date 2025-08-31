import re
from datetime import datetime, timezone
from weaviate.collections.classes.filters import Filter, _FilterValue, _Operator

NUMERIC_FIELDS = ["price", "horsepower", "year", "mileage", "lease_term", "monthlyEMI"]
DATE_FIELDS = {"lease_start_date": "leaseStartDate", "lease_expiry_date": "leaseExpiryDate"}
STRING_FIELDS = ["vehicle_id", "contract_id", "quote_id", "product_id","country"]

OP_MAP = {
    "<": _Operator.LESS_THAN,
    "<=": _Operator.LESS_THAN_EQUAL,
    ">": _Operator.GREATER_THAN,
    ">=": _Operator.GREATER_THAN_EQUAL,
    "=": _Operator.EQUAL,
}

def to_datetime(date_str: str) -> datetime:
    """Convert YYYY-MM-DD string into UTC datetime."""
    return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def extract_filters(query: str):
    """
    Extract filters from query string.  
    - Multiple constraints on same field → combined with AND (`Filter.all_of`)  
    - Different fields → returned separately in a list  
    """
    field_filters = {}

    # Numeric filters
    for field in NUMERIC_FIELDS:
        pattern = rf"{field}\s*:?\s*(<=|>=|<|>|=)\s*(\d+)"
        matches = list(re.finditer(pattern, query, re.IGNORECASE))
        if not matches:
            continue

        per_field = []
        for match in matches:
            op_symbol = match.group(1) or "="
            operator = OP_MAP[op_symbol]
            value = int(match.group(2))
            per_field.append(_FilterValue(value=value, operator=operator, target=field))

        field_filters[field] = per_field

    # Date filters
    for key, prop_name in DATE_FIELDS.items():
        pattern = rf"{key}\s*:?\s*(<=|>=|<|>|=)\s*(\d{{4}}-\d{{2}}-\d{{2}})"
        matches = list(re.finditer(pattern, query, re.IGNORECASE))
        if not matches:
            continue

        per_field = []
        for match in matches:
            op_symbol = match.group(1) or "="
            operator = OP_MAP[op_symbol]
            value = to_datetime(match.group(2))
            per_field.append(_FilterValue(value=value, operator=operator, target=prop_name))

        field_filters[prop_name] = per_field
    
    #string id's
    for field in STRING_FIELDS:
        pattern = rf"{field}\s*:?\s*(=)?\s*([A-Za-z0-9_-]+)"
        matches = list(re.finditer(pattern, query, re.IGNORECASE))
        if matches:
            field_filters[field] = [
                _FilterValue(
                    value=m.group(2),
                    operator=_Operator.EQUAL,
                    target=field,
                )
                for m in matches
            ]


     # Combine filters
    combined_filters = []
    for field, filters in field_filters.items():
        if len(filters) == 1:
            combined_filters.append(filters[0])
        else:
            combined_filters.append(Filter.all_of(filters))

    if not combined_filters:
        return None
    elif len(combined_filters) == 1:
        return combined_filters[0]
    else:
        # Combine different fields with AND
        return Filter.all_of(combined_filters)
