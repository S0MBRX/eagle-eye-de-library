class RowFilterNode:
    Name = "RowFilter"

    def __init__(self, Condition: str = None, Mode: str = "include", MatchValues=None):
        self.Condition = Condition
        self.MatchValues = list(MatchValues) if MatchValues is not None else None
        self.Mode = Mode.lower()

        if self.Mode not in ("include", "exclude"):
            raise ValueError("RowFilterNode Mode must be 'include' or 'exclude'.")

    def Run(self, Data, Ctx=None):
        if Data is None:
            raise ValueError("RowFilterNode received no input data.")

        if Ctx:
            Ctx.Log("RowFilterStart", Condition=self.Condition, MatchValues=self.MatchValues, Mode=self.Mode)

        Data = Data.copy()
        RowsBefore = len(Data)

        if self.MatchValues is not None:
            Wanted = {str(Value).strip().lower() for Value in self.MatchValues}

            MatchingIndex = Data[
                Data.apply(
                    lambda Row: bool(
                        {str(Value).strip().lower() for Value in Row.tolist()}.intersection(Wanted)
                    ),
                    axis=1
                )
            ].index
        else:
            MatchingIndex = Data.query(self.Condition).index

        if self.Mode == "include":
            Data = Data.loc[MatchingIndex]
        else:
            Data = Data.drop(index=MatchingIndex)

        RowsAfter = len(Data)
        RowsRemoved = RowsBefore - RowsAfter

        if Ctx:
            Ctx.Log("RowFilterEnd", Mode=self.Mode, RowsAfter=RowsAfter, RowsRemoved=RowsRemoved)

        return Data
