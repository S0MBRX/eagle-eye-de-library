class NormalizeColumnsNode:
    Name = "NormalizeColumns"

    def __init__(self, Target="headers"):
        Target = str(Target).strip().lower()
        if Target in ("column headers", "columns"):
            Target = "headers"
        if Target in ("all values", "cells"):
            Target = "values"
        if Target not in ("headers", "values"):
            raise ValueError("NormalizeColumnsNode Target must be 'headers' or 'values'.")
        self.Target = Target

    @staticmethod
    def NormalizeText(Value):
        return str(Value).strip().lower().replace(" ", "_")

    @staticmethod
    def HasAutoNumberedColumns(Data):
        Expected = list(range(1, len(Data.columns) + 1))
        Columns = list(Data.columns)
        return Columns == Expected or [str(Column) for Column in Columns] == [str(Column) for Column in Expected]

    def NormalizeValue(self, Value):
        if not isinstance(Value, str):
            return Value
        return self.NormalizeText(Value)

    def Run(self, Data, Ctx=None):
        if Data is None:
            raise ValueError("NormalizeColumnsNode received no input data.")

        if Ctx:
            Ctx.Log("NormalizeColumnsStart", Target=self.Target)

        Data = Data.copy()
        ChangedCount = 0

        if self.Target == "headers":
            OriginalColumns = list(Data.columns)
            PromotedFirstRow = False

            if self.HasAutoNumberedColumns(Data) and len(Data) > 0:
                OriginalColumns = Data.iloc[0].tolist()
                Data = Data.iloc[1:].reset_index(drop=True)
                Data.columns = OriginalColumns
                PromotedFirstRow = True

            Data.columns = [
                self.NormalizeText(Column)
                for Column in Data.columns
            ]

            ChangedCount = sum(
                1 for Old, New in zip(OriginalColumns, Data.columns) if str(Old) != str(New)
            )
            if PromotedFirstRow:
                ChangedCount += len(Data.columns)
        else:
            OriginalData = Data.copy()
            Data = Data.apply(lambda Column: Column.map(self.NormalizeValue))
            ChangedCells = OriginalData.ne(Data) & ~(OriginalData.isna() & Data.isna())
            ChangedCount = int(ChangedCells.sum().sum())

        if Ctx:
            Ctx.Log(
                "NormalizeColumnsEnd",
                Target=self.Target,
                ColumnCount=len(Data.columns),
                ValuesChanged=ChangedCount
            )

        return Data
