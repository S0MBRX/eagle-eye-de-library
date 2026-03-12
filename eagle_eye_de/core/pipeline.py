from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class NodeRunRecord:
    NodeName: str
    Ok: bool
    DurationMs: float
    Metrics: Dict[str, Any] = field(default_factory=dict)
    Warnings: List[str] = field(default_factory=list)
    Error: Optional[str] = None


@dataclass
class RunReport:
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


@dataclass
class SimpleExecutionContext:
    RunId: str

    def Log(self, Message: str, **Fields: Any) -> None:
        if Fields:
            print(f"[{self.RunId}] {Message} | {Fields}")
        else:
            print(f"[{self.RunId}] {Message}")


def FormatRunReportForConsole(Report: RunReport) -> str:
    Lines = []
    Lines.append("=" * 60)
    Lines.append(Report.SummaryText())
    Lines.append("=" * 60)

    for R in Report.Records:
        Lines.append("")
        Lines.append("-" * 44)
        Lines.append(f"{R.NodeName}")
        Lines.append("-" * 44)
        Lines.append(f"Ok: {R.Ok}")
        Lines.append(f"TimeTakenMs: {R.DurationMs:.3f}")

        if R.Metrics:
            Lines.append("")
            Lines.append("Metrics:")
            for K, V in R.Metrics.items():
                Lines.append(f"  {K}: {V}")

        if R.Warnings:
            Lines.append("")
            Lines.append("Warnings:")
            for W in R.Warnings:
                Lines.append(f"  - {W}")

        if R.Error:
            Lines.append("")
            Lines.append("Error:")
            Lines.append(f"  {R.Error}")

    Lines.append("")
    return "\n".join(Lines)


@dataclass
class Pipeline:
    Name: str
    Nodes: List[Any] = field(default_factory=list)

    def Add(self, NewNode: Any) -> "Pipeline":
        self.Nodes.append(NewNode)
        return self

    def Run(self, InputData: Any = None, Ctx: Optional[Any] = None) -> RunReport:
        RunId = Ctx.RunId if Ctx is not None else str(uuid.uuid4())[:8]
        ExecCtx = Ctx if Ctx is not None else SimpleExecutionContext(RunId=RunId)

        Report = RunReport(PipelineName=self.Name, RunId=RunId)
        Data = InputData

        ExecCtx.Log("PipelineStart", Pipeline=self.Name, NodeCount=len(self.Nodes))

        for N in self.Nodes:
            Start = time.perf_counter()
            Ok = True
            Err: Optional[str] = None
            Metrics: Dict[str, Any] = {}
            Warnings: List[str] = []

            NodeName = getattr(N, "Name", N.__class__.__name__)

            try:
                ExecCtx.Log("NodeStart", Node=NodeName)

                if hasattr(N, "Run"):
                    Result = N.Run(Data, ExecCtx)
                else:
                    Result = N(Data)

                if hasattr(Result, "Data") and hasattr(Result, "Metrics") and hasattr(Result, "Warnings"):
                    Data = Result.Data
                    Metrics = Result.Metrics or {}
                    Warnings = Result.Warnings or []
                else:
                    Data = Result

            except Exception as E:
                Ok = False
                Err = f"{type(E).__name__}: {E}"
                ExecCtx.Log("NodeFail", Node=NodeName, Error=Err)

            End = time.perf_counter()
            DurationMs = (End - Start) * 1000.0

            Report.AddRecord(
                NodeRunRecord(
                    NodeName=NodeName,
                    Ok=Ok,
                    DurationMs=DurationMs,
                    Metrics=Metrics,
                    Warnings=Warnings,
                    Error=Err,
                )
            )

            ExecCtx.Log("NodeEnd", Node=NodeName, Ok=Ok, DurationMs=DurationMs)

            if not Ok:
                break

        ExecCtx.Log("PipelineEnd", Summary=Report.SummaryText())
        return Report