import pandas as pd


class ExtractCsvNode:
    Name = "ExtractCsv"

    def __init__(self, Path):
        self.Path = Path

    def Run(self, Data=None, Ctx=None):
        if Ctx:
            Ctx.Log("ExtractCsvStart", Path=self.Path)

        df = pd.read_csv(self.Path)

        if Ctx:
            Ctx.Log("ExtractCsvEnd", RowCount=len(df))

        return df