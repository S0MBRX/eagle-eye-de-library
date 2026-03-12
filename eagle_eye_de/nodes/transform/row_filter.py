from eagle_eye_de.nodes  import NodeResult


class RowFilterNode:
    Name = "RowFilter"

    def __init__(self, Condition: str):
        self.Condition = Condition

    def Run(self, Data, Ctx=None):
        if Data is None:
            raise ValueError("RowFilterNode received no input data.")

        if Ctx:
            Ctx.Log("RowFilterStart", Condition=self.Condition)

        Data = Data.copy()
        RowsBefore = len(Data)

        Data = Data.query(self.Condition)

        RowsAfter = len(Data)
        RowsRemoved = RowsBefore - RowsAfter

        Metrics = {
            "Condition": self.Condition,
            "RowsBefore": RowsBefore,
            "RowsAfter": RowsAfter,
            "RowsRemoved": RowsRemoved,
        }

        if Ctx:
            Ctx.Log("RowFilterEnd", RowsAfter=RowsAfter, RowsRemoved=RowsRemoved)

        return NodeResult(
            Data=Data,
            Metrics=Metrics,
            Warnings=[]
        )