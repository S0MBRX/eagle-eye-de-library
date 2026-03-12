class GenerateColumnNode:
    Name = "GenerateColumn"

    def __init__(self, NewColumn, Operator, Columns):
        if len(Columns) < 2:
            raise ValueError("GenerateColumnNode requires at least two columns.")

        self.NewColumn = NewColumn
        self.Operator = Operator
        self.Columns = list(Columns)

        if Operator not in ["+", "-", "*", "/"]:
            raise ValueError("Operator must be one of: + - * /")

    def Run(self, Data, Ctx=None):
        if Data is None:
            raise ValueError("GenerateColumnNode received no input data.")

        if Ctx:
            Ctx.Log(
                "GenerateColumnStart",
                NewColumn=self.NewColumn,
                Operator=self.Operator,
                Columns=self.Columns,
            )

        MissingColumns = [c for c in self.Columns if c not in Data.columns]
        if MissingColumns:
            raise ValueError(f"GenerateColumnNode missing columns: {MissingColumns}")

        Data = Data.copy()

        Result = Data[self.Columns[0]]

        for Column in self.Columns[1:]:
            if self.Operator == "+":
                Result = Result + Data[Column]
            elif self.Operator == "-":
                Result = Result - Data[Column]
            elif self.Operator == "*":
                Result = Result * Data[Column]
            elif self.Operator == "/":
                Result = Result / Data[Column]

        Data[self.NewColumn] = Result

        if Ctx:
            Ctx.Log(
                "GenerateColumnEnd",
                NewColumn=self.NewColumn,
                SourceColumnCount=len(self.Columns),
            )

        return Data