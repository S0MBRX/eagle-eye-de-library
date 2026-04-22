class WriteCsvNode:
    Name = "WriteCsv"

    def __init__(self, Path, Index=False, Header=None):
        self.Path = Path
        self.Index = Index
        self.Header = Header

    @staticmethod
    def HasAutoNumberedColumns(Data):
        Expected = list(range(1, len(Data.columns) + 1))
        Columns = list(Data.columns)
        return Columns == Expected or [str(Column) for Column in Columns] == [str(Column) for Column in Expected]

    def Run(self, Data, Ctx=None):
        if Data is None:
            raise ValueError("WriteCsvNode received no input data.")

        if Ctx:
            Ctx.Log("WriteCsvStart", Path=self.Path)

        Rows = len(Data)
        Columns = len(Data.columns)
        Header = self.Header
        if Header is None:
            Header = not self.HasAutoNumberedColumns(Data)

        Data.to_csv(self.Path, index=self.Index, header=Header)

        if Ctx:
            Ctx.Log(
                "WriteCsvEnd",
                Path=self.Path,
                RowsWritten=Rows,
                ColumnsWritten=Columns,
                HeaderWritten=Header,
            )

        return Data
