class ColumnFilterNode:
    Name = "ColumnFilter"

    def __init__(self, Columns=None, Mode: str = "include", MatchValues=None, MatchHeaders: bool = True):
        self.Columns = list(Columns or [])
        self.MatchValues = list(MatchValues) if MatchValues is not None else None
        self.MatchHeaders = MatchHeaders
        self.Mode = Mode.lower()

        if self.Mode not in ("include", "exclude"):
            raise ValueError("ColumnFilterNode Mode must be 'include' or 'exclude'.")

    def Run(self, Data, Ctx=None):
        if Data is None:
            raise ValueError("ColumnFilterNode received no input data.")

        if Ctx:
            Ctx.Log(
                "ColumnFilterStart",
                Columns=self.Columns,
                MatchValues=self.MatchValues,
                Mode=self.Mode
            )

        Data = Data.copy()

        if self.MatchValues is not None:
            Wanted = {str(Value).strip().lower() for Value in self.MatchValues}
            MatchingColumns = []

            for Column in Data.columns:
                Values = set(Data[Column].map(lambda Value: str(Value).strip().lower()).tolist())
                if self.MatchHeaders:
                    Values.add(str(Column).strip().lower())

                if Values.intersection(Wanted):
                    MatchingColumns.append(Column)

            if self.Mode == "include":
                Data = Data[MatchingColumns]
            else:
                Data = Data.drop(columns=MatchingColumns)
        else:
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
