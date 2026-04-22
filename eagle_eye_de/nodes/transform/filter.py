import ast


class FilterNode:
    Name = "Filter"

    def __init__(self, Target: str, Mode: str, MatchMode: str, MatchValues, MatchBy: str = "values"):
        self.Target = Target.lower()
        self.Mode = Mode.lower()
        self.MatchMode = MatchMode.lower()
        self.MatchValues = list(MatchValues)
        self.MatchBy = str(MatchBy).strip().lower()

        if self.Target not in ("rows", "columns"):
            raise ValueError("FilterNode Target must be 'rows' or 'columns'.")
        if self.Mode not in ("include", "exclude"):
            raise ValueError("FilterNode Mode must be 'include' or 'exclude'.")
        if self.MatchMode not in ("and", "or"):
            raise ValueError("FilterNode MatchMode must be 'and' or 'or'.")
        if self.MatchBy not in ("values", "index"):
            raise ValueError("FilterNode MatchBy must be 'values' or 'index'.")
        if not self.MatchValues:
            raise ValueError("FilterNode requires at least one value.")

    def _normalize(self, Value):
        return str(Value).strip().lower().replace(" ", "_")

    def _parsed(self, Value):
        if not isinstance(Value, str):
            return Value

        try:
            return ast.literal_eval(Value.strip())
        except Exception:
            return Value

    def _value_matches(self, ExistingValue, WantedValue):
        ExistingParsed = self._parsed(ExistingValue)
        WantedParsed = self._parsed(WantedValue)

        try:
            if ExistingParsed == WantedParsed:
                return True
        except Exception:
            pass

        ExistingText = self._normalize(ExistingValue)
        WantedText = self._normalize(WantedValue)
        return WantedText != "" and WantedText in ExistingText

    def _matches(self, Values):
        Wanted = [Value for Value in self.MatchValues if str(Value).strip()]

        if self.MatchMode == "and":
            return all(
                any(self._value_matches(ExistingValue, WantedValue) for ExistingValue in Values)
                for WantedValue in Wanted
            )
        return any(
            self._value_matches(ExistingValue, WantedValue)
            for ExistingValue in Values
            for WantedValue in Wanted
        )

    def _parse_index_values(self, Count):
        Positions = set()

        for Value in self.MatchValues:
            Text = str(Value).strip()
            if not Text:
                continue

            Text = Text.replace(":", "-")
            Parts = [Part.strip() for Part in Text.split("-") if Part.strip()]

            try:
                if len(Parts) == 1:
                    Index = int(Parts[0])
                    if 1 <= Index <= Count:
                        Positions.add(Index - 1)
                elif len(Parts) == 2:
                    Start = int(Parts[0])
                    End = int(Parts[1])
                    if End < Start:
                        Start, End = End, Start

                    Start = max(1, Start)
                    End = min(Count, End)
                    for Index in range(Start, End + 1):
                        Positions.add(Index - 1)
            except ValueError:
                continue

        return Positions

    def Run(self, Data, Ctx=None):
        if Data is None:
            raise ValueError("FilterNode received no input data.")

        if Ctx:
            Ctx.Log(
                "FilterStart",
                Target=self.Target,
                Mode=self.Mode,
                MatchMode=self.MatchMode,
                MatchBy=self.MatchBy,
                MatchValues=self.MatchValues,
            )

        Data = Data.copy()

        if self.MatchBy == "index":
            if self.Target == "columns":
                MatchingPositions = self._parse_index_values(len(Data.columns))
                MatchingColumns = [
                    Column
                    for Position, Column in enumerate(Data.columns)
                    if Position in MatchingPositions
                ]

                if self.Mode == "include":
                    Data = Data[MatchingColumns]
                else:
                    Data = Data.drop(columns=MatchingColumns)
            else:
                MatchingPositions = self._parse_index_values(len(Data))
                MatchingIndex = [
                    RowLabel
                    for Position, RowLabel in enumerate(Data.index)
                    if Position in MatchingPositions
                ]

                if self.Mode == "include":
                    Data = Data.loc[MatchingIndex]
                else:
                    Data = Data.drop(index=MatchingIndex)

            if Ctx:
                Ctx.Log(
                    "FilterEnd",
                    Target=self.Target,
                    Mode=self.Mode,
                    MatchBy=self.MatchBy,
                    RowCount=len(Data),
                    ColumnCount=len(Data.columns),
                )

            return Data

        if self.Target == "columns":
            MatchingColumns = [
                Column
                for Column in Data.columns
                if self._matches([Column])
            ]

            if self.Mode == "include":
                Data = Data[MatchingColumns]
            else:
                Data = Data.drop(columns=MatchingColumns)

        else:
            MatchingIndex = Data[
                Data.apply(lambda Row: self._matches(Row.tolist()), axis=1)
            ].index

            if self.Mode == "include":
                Data = Data.loc[MatchingIndex]
            else:
                Data = Data.drop(index=MatchingIndex)

        if Ctx:
            Ctx.Log(
                "FilterEnd",
                Target=self.Target,
                Mode=self.Mode,
                MatchMode=self.MatchMode,
                RowCount=len(Data),
                ColumnCount=len(Data.columns),
            )

        return Data
