import csv

import pandas as pd


def ReadCsvRows(Path):
    with open(Path, newline="", encoding="utf-8-sig") as File:
        Rows = list(csv.reader(File))

    if not Rows:
        return pd.DataFrame()

    ColumnCount = max(len(Row) for Row in Rows)
    PaddedRows = [
        Row + [""] * (ColumnCount - len(Row))
        for Row in Rows
    ]

    return pd.DataFrame(PaddedRows, columns=list(range(1, ColumnCount + 1)))


class ExtractCsvNode:
    Name = "ExtractCsv"

    def __init__(self, Path):
        self.Path = Path

    def Run(self, Data=None, Ctx=None):
        if Ctx:
            Ctx.Log("ExtractCsvStart", Path=self.Path)

        df = ReadCsvRows(self.Path)

        if Ctx:
            Ctx.Log("ExtractCsvEnd", RowCount=len(df))

        return df
