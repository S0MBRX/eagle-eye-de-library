import pandas as pd
from eagle_eye_de.nodes  import NodeResult


class ExtractCsvNode:

    Name = "ExtractCsv"

    def __init__(self, Path: str):
        self.Path = Path

    def Run(self, Data, Ctx=None):

        if Ctx:
            Ctx.Log("ExtractCsvStart", Path=self.Path)

        df = pd.read_csv(self.Path)

        Metrics = {
            "RowsRead": len(df),
            "Columns": len(df.columns),
        }

        if Ctx:
            Ctx.Log("ExtractCsvEnd", Rows=Metrics["RowsRead"])

        return NodeResult(
            Data=df,
            Metrics=Metrics,
            Warnings=[]
        )