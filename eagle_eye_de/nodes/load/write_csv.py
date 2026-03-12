from eagle_eye_de.nodes  import NodeResult


class WriteCsvNode:
    Name = "WriteCsv"

    def __init__(self, Path, Index=False):
        self.Path = Path
        self.Index = Index

    def Run(self, Data, Ctx=None):
        if Data is None:
            raise ValueError("WriteCsvNode received no input data.")

        if Ctx:
            Ctx.Log("WriteCsvStart", Path=self.Path)

        Rows = len(Data)
        Columns = len(Data.columns)

        Data.to_csv(self.Path, index=self.Index)

        Metrics = {
            "OutputPath": self.Path,
            "RowsWritten": Rows,
            "ColumnsWritten": Columns,
        }

        if Ctx:
            Ctx.Log("WriteCsvEnd", Path=self.Path, RowsWritten=Rows)

        return NodeResult(
            Data=Data,
            Metrics=Metrics,
            Warnings=[]
        )