from eagle_eye_de.nodes.extract.csv import ReadCsvTableFromRows


class ExtractTableNode:
    Name = "ExtractTable"

    def __init__(self, Table="1"):
        self.Table = Table

    def Run(self, Data, Ctx=None):
        if Data is None:
            raise ValueError("ExtractTableNode received no input data.")

        if Ctx:
            Ctx.Log("ExtractTableStart", Table=self.Table)

        Rows = []
        for Row in Data.fillna("").astype(str).values.tolist():
            Rows.append([str(Cell) for Cell in Row])

        Result = ReadCsvTableFromRows(Rows, Table=self.Table)

        if Ctx:
            Ctx.Log(
                "ExtractTableEnd",
                Table=self.Table,
                RowCount=len(Result),
                ColumnCount=len(Result.columns),
            )

        return Result
