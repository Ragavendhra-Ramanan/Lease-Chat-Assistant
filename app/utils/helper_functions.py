# to get combined query
def inject_filters(query: str, filters: str, entity: str) -> str:
        """Turn natural-language filters into query modifiers."""
        if not filters:
            return query
        return f"{query}. Additionally filter {entity} records by: {filters}"

