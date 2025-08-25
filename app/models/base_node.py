from typing import Any

class BaseNode:
    async def run(self, state: Any):
        """Each node must implement this async run method"""
        raise NotImplementedError("Subclasses must implement run()")
