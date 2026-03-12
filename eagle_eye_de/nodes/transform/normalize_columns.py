from eagle_eye_de.nodes  import NodeResult


class NormalizeColumnsNode:
    Name = "NormalizeColumns"

    def Run(self, Data, Ctx=None):
        if Data is None:
            raise ValueError("NormalizeColumnsNode received no input data.")

        if Ctx:
            Ctx.Log("NormalizeColumnsStart")

        Data = Data.copy()
        OriginalColumns = list(Data.columns)

        Data.columns = [
            str(Column).strip().lower().replace(" ", "_")
            for Column in Data.columns
        ]

        ChangedCount = sum(
            1 for Old, New in zip(OriginalColumns, Data.columns) if str(Old) != str(New)
        )

        Metrics = {
            "ColumnCount": len(Data.columns),
            "ColumnsChanged": ChangedCount,
        }

        if Ctx:
            Ctx.Log("NormalizeColumnsEnd", ColumnCount=len(Data.columns), ColumnsChanged=ChangedCount)

        return NodeResult(
            Data=Data,
            Metrics=Metrics,
            Warnings=[]
        )