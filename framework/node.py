from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol


class IExecutionContext(Protocol):
    # Minimal context passed into nodes (logging and run id).
    RunId: str

    def Log(self, Message: str, **Fields: Any) -> None: ...


@dataclass
class NodeResult:
    # Standard node output container.
    Data: Any
    Metrics: Dict[str, Any]
    Warnings: List[str]


class Node(Protocol):
    # Standard interface for all nodes.
    Name: str

    def Run(self, Data: Any, Ctx: Optional[IExecutionContext] = None) -> NodeResult: ...