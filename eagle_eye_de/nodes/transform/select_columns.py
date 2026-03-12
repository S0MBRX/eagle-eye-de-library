from eagle_eye_de.node import NodeResult


class ColumnFilterNode:
    Name = "ColumnFilter"

    def __init__(self, Columns, Mode: str = "include"):
        self.Columns = list(Columns)
        self.Mode = Mode.lower()

        if self.Mode not in ("include", "exclude"):
            raise ValueError("ColumnFilterNode Mode must be 'include' or 'exclude'.")

    def Run(self, Data, Ctx=None):
        if Data is None:
            raise ValueError("ColumnFilterNode received no input data.")

        if Ctx:
            Ctx.Log("ColumnFilterStart", Columns=self.Columns, Mode=self.Mode)

        Data = Data.copy()

        MissingColumns = [C for C in self.Columns if C not in Data.columns]

        if self.Mode == "include":
            if MissingColumns:
                raise ValueError(f"ColumnFilterNode missing columns: {MissingColumns}")

            Data = Data[self.Columns]

        elif self.Mode == "exclude":
            ExistingColumns = [C for C in self.Columns if C in Data.columns]
            Data = Data.drop(columns=ExistingColumns)

        Metrics = {
            "Mode": self.Mode,
            "ColumnCount": len(Data.columns),
            "RowCount": len(Data),
        }

        Warnings = []
        if MissingColumns and self.Mode == "exclude":
            Warnings.append(f"Columns not found and not excluded: {MissingColumns}")

        if Ctx:
            Ctx.Log("ColumnFilterEnd", Mode=self.Mode, ColumnCount=len(Data.columns))

        return NodeResult(
            Data=Data,
            Metrics=Metrics,
            Warnings=Warnings
        )