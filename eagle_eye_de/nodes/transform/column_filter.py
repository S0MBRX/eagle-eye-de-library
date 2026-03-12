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

        MissingColumns = [Column for Column in self.Columns if Column not in Data.columns]

        if self.Mode == "include":
            if MissingColumns:
                raise ValueError(f"ColumnFilterNode missing columns: {MissingColumns}")

            Data = Data[self.Columns]

        elif self.Mode == "exclude":
            ExistingColumns = [Column for Column in self.Columns if Column in Data.columns]
            Data = Data.drop(columns=ExistingColumns)

        if Ctx:
            Ctx.Log(
                "ColumnFilterEnd",
                Mode=self.Mode,
                ColumnCount=len(Data.columns),
                RowCount=len(Data),
            )

        return Data