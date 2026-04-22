import re

import pandas as pd


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

    @staticmethod
    def _normalize_column_name(Column):
        Text = str(Column).strip().lower()
        Text = re.sub(r"\s+", "_", Text)
        return Text

    def _resolve_column(self, Data, RequestedColumn):
        if RequestedColumn in Data.columns:
            return RequestedColumn

        RequestedText = str(RequestedColumn).strip()
        RequestedLower = RequestedText.lower()
        RequestedNormalized = self._normalize_column_name(RequestedColumn)

        Matches = []
        for ExistingColumn in Data.columns:
            ExistingText = str(ExistingColumn).strip()
            ExistingLower = ExistingText.lower()
            ExistingNormalized = self._normalize_column_name(ExistingColumn)

            if RequestedText == ExistingText:
                return ExistingColumn
            if RequestedLower == ExistingLower:
                return ExistingColumn
            if RequestedNormalized == ExistingNormalized:
                Matches.append(ExistingColumn)

        if len(Matches) == 1:
            return Matches[0]
        return None

    def _resolve_columns(self, Data):
        ResolvedColumns = []
        MissingColumns = []

        for Column in self.Columns:
            ResolvedColumn = self._resolve_column(Data, Column)
            if ResolvedColumn is None:
                MissingColumns.append(Column)
            else:
                ResolvedColumns.append(ResolvedColumn)

        if MissingColumns:
            AvailableColumns = [str(Column) for Column in Data.columns]
            raise ValueError(
                "GenerateColumnNode missing columns: "
                f"{MissingColumns}. Available columns: {AvailableColumns}"
            )

        return ResolvedColumns

    @staticmethod
    def _as_number(Series):
        if Series.dtype == object:
            Series = Series.astype(str).str.strip().str.replace(",", "", regex=False)
        return pd.to_numeric(Series, errors="coerce")

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

        Data = Data.copy()
        ResolvedColumns = self._resolve_columns(Data)

        Result = self._as_number(Data[ResolvedColumns[0]])

        for Column in ResolvedColumns[1:]:
            ColumnData = self._as_number(Data[Column])
            if self.Operator == "+":
                Result = Result + ColumnData
            elif self.Operator == "-":
                Result = Result - ColumnData
            elif self.Operator == "*":
                Result = Result * ColumnData
            elif self.Operator == "/":
                Result = Result / ColumnData

        Data[self.NewColumn] = Result

        if Ctx:
            Ctx.Log(
                "GenerateColumnEnd",
                NewColumn=self.NewColumn,
                Columns=ResolvedColumns,
                SourceColumnCount=len(ResolvedColumns),
            )

        return Data
