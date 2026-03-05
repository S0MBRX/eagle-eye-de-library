from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class NodeRunRecord:
    # One record per node execution.
    NodeName: str
    Ok: bool
    DurationMs: float
    Metrics: Dict[str, Any] = field(default_factory=dict)
    Warnings: List[str] = field(default_factory=list)
    Error: Optional[str] = None


@dataclass
class RunReport:
    # A run-level report for a pipeline execution.
    PipelineName: str
    RunId: str
    Records: List[NodeRunRecord] = field(default_factory=list)

    def AddRecord(self, Record: NodeRunRecord) -> None:
        self.Records.append(Record)

    def OkCount(self) -> int:
        return sum(1 for R in self.Records if R.Ok)

    def TotalCount(self) -> int:
        return len(self.Records)

    def SummaryText(self) -> str:
        return f"Run {self.RunId} - {self.PipelineName}: {self.OkCount()}/{self.TotalCount()} nodes OK"