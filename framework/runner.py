from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

from framework.node import IExecutionContext, NodeResult
from framework.pipeline import Pipeline
from framework.reporting import NodeRunRecord, RunReport


@dataclass
class SimpleExecutionContext:
    # Minimal context implementation for logging and run tracking.
    RunId: str

    def Log(self, Message: str, **Fields: Any) -> None:
        # Simple console logger for MVP.
        if Fields:
            print(f"[{self.RunId}] {Message} | {Fields}")
        else:
            print(f"[{self.RunId}] {Message}")


class Runner:
    # Executes a Pipeline and produces a RunReport.
    def Run(self, PipelineObj: Pipeline, InputData: Any = None, Ctx: Optional[IExecutionContext] = None) -> RunReport:
        RunId = (Ctx.RunId if Ctx is not None else str(uuid.uuid4())[:8])
        ExecCtx = (Ctx if Ctx is not None else SimpleExecutionContext(RunId=RunId))

        Report = RunReport(PipelineName=PipelineObj.Name, RunId=RunId)
        Data = InputData

        ExecCtx.Log("PipelineStart", Pipeline=PipelineObj.Name, NodeCount=len(PipelineObj.Nodes))

        for N in PipelineObj.Nodes:
            Start = time.perf_counter()
            Ok = True
            Err: Optional[str] = None
            Metrics: Dict[str, Any] = {}
            Warnings = []

            try:
                ExecCtx.Log("NodeStart", Node=N.Name)
                Result: NodeResult = N.Run(Data, ExecCtx)
                Data = Result.Data
                Metrics = Result.Metrics or {}
                Warnings = Result.Warnings or []
            except Exception as E:
                Ok = False
                Err = f"{type(E).__name__}: {E}"
                ExecCtx.Log("NodeFail", Node=N.Name, Error=Err)

            End = time.perf_counter()
            DurationMs = (End - Start) * 1000.0

            Report.AddRecord(
                NodeRunRecord(
                    NodeName=N.Name,
                    Ok=Ok,
                    DurationMs=DurationMs,
                    Metrics=Metrics,
                    Warnings=Warnings,
                    Error=Err,
                )
            )

            ExecCtx.Log("NodeEnd", Node=N.Name, Ok=Ok, DurationMs=DurationMs)

            # MVP: stop on first failure.
            if not Ok:
                break

        ExecCtx.Log("PipelineEnd", Summary=Report.SummaryText())
        return Report