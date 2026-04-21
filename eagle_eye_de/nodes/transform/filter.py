import ast


class FilterNode:
    Name = "Filter"

    def __init__(self, Target: str, Mode: str, MatchMode: str, MatchValues):
        self.Target = Target.lower()
        self.Mode = Mode.lower()
        self.MatchMode = MatchMode.lower()
        self.MatchValues = list(MatchValues)

        if self.Target not in ("rows", "columns"):
            raise ValueError("FilterNode Target must be 'rows' or 'columns'.")
        if self.Mode not in ("include", "exclude"):
            raise ValueError("FilterNode Mode must be 'include' or 'exclude'.")
        if self.MatchMode not in ("and", "or"):
            raise ValueError("FilterNode MatchMode must be 'and' or 'or'.")
        if not self.MatchValues:
            raise ValueError("FilterNode requires at least one value.")

    def _normalize(self, Value):
        return str(Value).strip().lower()

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

    def Run(self, Data, Ctx=None):
        if Data is None:
            raise ValueError("FilterNode received no input data.")

        if Ctx:
            Ctx.Log(
                "FilterStart",
                Target=self.Target,
                Mode=self.Mode,
                MatchMode=self.MatchMode,
                MatchValues=self.MatchValues,
            )

        Data = Data.copy()

        if self.Target == "columns":
            MatchingColumns = [
                Column
                for Column in Data.columns
                if self._matches(Data[Column].tolist())
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
