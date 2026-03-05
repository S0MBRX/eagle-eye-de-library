from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from framework.node import Node


@dataclass
class Pipeline:
    # An ordered collection of nodes (MVP).
    Name: str
    Nodes: List[Node] = field(default_factory=list)

    def Add(self, NewNode: Node) -> "Pipeline":
        self.Nodes.append(NewNode)
        return self