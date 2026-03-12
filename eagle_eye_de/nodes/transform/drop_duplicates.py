from eagle_eye_de.nodes  import NodeResult


class DropDuplicatesNode:
    Name = "DropDuplicates"

    def __init__(self, Subset=None, Keep: str = "first"):
        self.Subset = Subset
        self.Keep = Keep

    def Run(self, Data, Ctx=None):
        if Data is None:
            raise ValueError("DropDuplicatesNode received no input data.")

        if Ctx:
            Ctx.Log("DropDuplicatesStart", Subset=self.Subset, Keep=self.Keep)

        Data = Data.copy()
        RowsBefore = len(Data)

        Data = Data.drop_duplicates(subset=self.Subset, keep=self.Keep)

        RowsAfter = len(Data)
        RowsRemoved = RowsBefore - RowsAfter

        Metrics = {
            "RowsBefore": RowsBefore,
            "RowsAfter": RowsAfter,
            "RowsRemoved": RowsRemoved,
        }

        if Ctx:
            Ctx.Log("DropDuplicatesEnd", RowsRemoved=RowsRemoved)

        return NodeResult(
            Data=Data,
            Metrics=Metrics,
            Warnings=[]
        )