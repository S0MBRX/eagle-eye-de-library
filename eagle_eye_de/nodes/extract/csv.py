import csv

import pandas as pd


def ReadCsvRawRows(Path):
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


def _NonEmptyCells(Row):
    return [Cell.strip() for Cell in Row if str(Cell).strip() != ""]


def _IsBlankRow(Row):
    return len(_NonEmptyCells(Row)) == 0


def _LooksLikeTableRow(Row, MinColumns=2):
    return len(_NonEmptyCells(Row)) >= MinColumns


def _TrimEmptyColumns(Rows):
    if not Rows:
        return Rows

    Width = max(len(Row) for Row in Rows)
    Padded = [Row + [""] * (Width - len(Row)) for Row in Rows]
    UsedIndexes = [
        Index
        for Index in range(Width)
        if any(str(Row[Index]).strip() != "" for Row in Padded)
    ]

    if not UsedIndexes:
        return []

    return [
        [Row[Index] for Index in UsedIndexes]
        for Row in Padded
    ]


def _UniqueHeaders(HeaderRow):
    Headers = []
    Seen = {}
    for Index, Header in enumerate(HeaderRow, start=1):
        Name = str(Header).strip()
        if not Name:
            Name = f"column_{Index}"

        Count = Seen.get(Name, 0)
        Seen[Name] = Count + 1
        if Count:
            Name = f"{Name}_{Count + 1}"

        Headers.append(Name)
    return Headers


def DetectCsvTablesFromRows(Rows, MinColumns=3, MinRows=2):
    Tables = []
    CurrentRows = []
    StartRow = None

    def flush_current(EndRow):
        nonlocal CurrentRows, StartRow
        if len(CurrentRows) >= MinRows:
            TrimmedRows = _TrimEmptyColumns(CurrentRows)
            if TrimmedRows and len(TrimmedRows[0]) >= MinColumns:
                Tables.append({
                    "index": len(Tables) + 1,
                    "start_row": StartRow,
                    "end_row": EndRow,
                    "rows": TrimmedRows,
                    "columns": _UniqueHeaders(TrimmedRows[0]),
                    "row_count": max(0, len(TrimmedRows) - 1),
                })

        CurrentRows = []
        StartRow = None

    for RowNumber, Row in enumerate(Rows, start=1):
        if _IsBlankRow(Row):
            flush_current(RowNumber - 1)
            continue

        if _LooksLikeTableRow(Row, MinColumns=MinColumns):
            if not CurrentRows:
                StartRow = RowNumber
            CurrentRows.append(Row)
        else:
            flush_current(RowNumber - 1)

    flush_current(len(Rows))
    return Tables


def DetectCsvTables(Path, MinColumns=3, MinRows=2):
    with open(Path, newline="", encoding="utf-8-sig") as File:
        Rows = list(csv.reader(File))

    return DetectCsvTablesFromRows(Rows, MinColumns=MinColumns, MinRows=MinRows)


def ReadCsvTableFromRows(Rows, Table=1):
    Tables = DetectCsvTablesFromRows(Rows)
    if not Tables:
        if not Rows:
            return pd.DataFrame()
        ColumnCount = max(len(Row) for Row in Rows)
        PaddedRows = [
            Row + [""] * (ColumnCount - len(Row))
            for Row in Rows
        ]
        return pd.DataFrame(PaddedRows, columns=list(range(1, ColumnCount + 1)))

    if isinstance(Table, str):
        Table = Table.strip().lower()
        if Table in ("auto", "first", ""):
            TableIndex = 1
        else:
            TableIndex = int(Table)
    else:
        TableIndex = int(Table)

    if TableIndex < 1 or TableIndex > len(Tables):
        raise ValueError(f"CSV table {TableIndex} not found. Detected {len(Tables)} table(s).")

    TableInfo = Tables[TableIndex - 1]
    Rows = TableInfo["rows"]
    Headers = _UniqueHeaders(Rows[0])
    DataRows = Rows[1:]
    return pd.DataFrame(DataRows, columns=Headers)


def ReadCsvTable(Path, Table=1):
    with open(Path, newline="", encoding="utf-8-sig") as File:
        Rows = list(csv.reader(File))
    return ReadCsvTableFromRows(Rows, Table=Table)


def ReadCsvRows(Path, Table=None):
    if Table is None or str(Table).strip().lower() == "raw":
        return ReadCsvRawRows(Path)
    return ReadCsvTable(Path, Table=Table)


class ExtractCsvNode:
    Name = "ExtractCsv"

    def __init__(self, Path, Table=None):
        self.Path = Path
        self.Table = Table

    def Run(self, Data=None, Ctx=None):
        if Ctx:
            Ctx.Log("ExtractCsvStart", Path=self.Path, Table=self.Table)

        df = ReadCsvRows(self.Path, Table=self.Table)

        if Ctx:
            Ctx.Log("ExtractCsvEnd", RowCount=len(df))

        return df
