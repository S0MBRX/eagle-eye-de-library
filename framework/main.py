from dataclasses import dataclass
from typing import Any, Optional

from framework.pipeline import Pipeline
from framework.runner import Runner
from framework.node import NodeResult, IExecutionContext

@dataclass
class AddOneNode:
    Name: str = "AddOne"

    def Run(self, Data: Any, Ctx: Optional[IExecutionContext] = None) -> NodeResult:
        Value = 0 if Data is None else int(Data)
        Value += 1
        return NodeResult(Data=Value, Metrics={"Value": Value}, Warnings=[])


if __name__ == "__main__":
    PipelineObj = Pipeline("QuickTest")
    PipelineObj.Add(AddOneNode()).Add(AddOneNode())

    Report = Runner().Run(PipelineObj, InputData=0)
    print(Report.SummaryText())