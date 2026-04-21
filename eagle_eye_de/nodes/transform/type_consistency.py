import math
import re


class TypeConsistencyNode:
    Name = "TypeConsistency"

    Units = {
        "zero": 0,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "thirteen": 13,
        "fourteen": 14,
        "fifteen": 15,
        "sixteen": 16,
        "seventeen": 17,
        "eighteen": 18,
        "nineteen": 19,
    }
    Tens = {
        "twenty": 20,
        "thirty": 30,
        "forty": 40,
        "fifty": 50,
        "sixty": 60,
        "seventy": 70,
        "eighty": 80,
        "ninety": 90,
    }

    def __init__(self, OutlierAction="highlight", MinimumDominance=0.6):
        OutlierAction = str(OutlierAction).strip().lower()
        if OutlierAction not in ("highlight", "delete"):
            raise ValueError("TypeConsistencyNode OutlierAction must be 'highlight' or 'delete'.")

        self.OutlierAction = OutlierAction
        self.MinimumDominance = float(MinimumDominance)
        self.Report = {
            "dominant_types": {},
            "corrected": [],
            "outliers": [],
            "deleted_rows": [],
        }

    def _is_missing(self, Value):
        if Value is None:
            return True
        try:
            return bool(math.isnan(Value))
        except Exception:
            return False

    def _clean_text(self, Value):
        return str(Value).strip().lower().replace("-", " ")

    def _parse_compound_word_number(self, Word):
        if Word in self.Units:
            return self.Units[Word]
        if Word in self.Tens:
            return self.Tens[Word]

        for TensWord, TensValue in self.Tens.items():
            if Word.startswith(TensWord):
                UnitWord = Word[len(TensWord):]
                if UnitWord in self.Units:
                    return TensValue + self.Units[UnitWord]
        return None

    def _parse_word_int(self, Value):
        Text = self._clean_text(Value).replace(",", " ")
        Text = re.sub(r"\band\b", " ", Text)
        Parts = [Part for Part in Text.split() if Part]
        if not Parts:
            return None

        Total = 0
        Current = 0
        Matched = False
        for Part in Parts:
            Number = self._parse_compound_word_number(Part)
            if Number is not None:
                Current += Number
                Matched = True
            elif Part == "hundred":
                Current = max(Current, 1) * 100
                Matched = True
            elif Part == "thousand":
                Total += max(Current, 1) * 1000
                Current = 0
                Matched = True
            else:
                return None

        if not Matched:
            return None
        return Total + Current

    def _parse_int(self, Value):
        if self._is_missing(Value):
            return None
        if isinstance(Value, bool):
            return None
        if isinstance(Value, int):
            return Value
        if isinstance(Value, float):
            return int(Value) if Value.is_integer() else None

        Text = str(Value).strip().replace(",", "")
        if re.fullmatch(r"[-+]?\d+", Text):
            return int(Text)

        WordValue = self._parse_word_int(Text)
        if WordValue is not None:
            return WordValue
        return None

    def _parse_float(self, Value):
        if self._is_missing(Value) or isinstance(Value, bool):
            return None
        if isinstance(Value, (int, float)):
            return float(Value)

        Text = str(Value).strip().replace(",", "")
        try:
            return float(Text)
        except Exception:
            return None

    def _classify_value(self, Value):
        if self._is_missing(Value) or str(Value).strip() == "":
            return None
        if self._parse_int(Value) is not None:
            return "integer"
        if self._parse_float(Value) is not None:
            return "float"
        return "text"

    def _coerce_value(self, Value, TargetType):
        if TargetType == "integer":
            return self._parse_int(Value)
        if TargetType == "float":
            Parsed = self._parse_float(Value)
            return Parsed
        return Value

    def _dominant_type(self, Values):
        Counts = {}
        Total = 0
        for Value in Values:
            TypeName = self._classify_value(Value)
            if TypeName is None:
                continue
            Counts[TypeName] = Counts.get(TypeName, 0) + 1
            Total += 1

        if not Counts or Total == 0:
            return None

        TypeName, Count = max(Counts.items(), key=lambda Item: Item[1])
        if Count / Total < self.MinimumDominance:
            return None
        if TypeName == "integer" and Counts.get("float", 0):
            return "float"
        return TypeName

    def Run(self, Data, Ctx=None):
        if Data is None:
            raise ValueError("TypeConsistencyNode received no input data.")

        if Ctx:
            Ctx.Log("TypeConsistencyStart", OutlierAction=self.OutlierAction)

        Data = Data.copy()
        OutlierRows = set()
        Report = {
            "dominant_types": {},
            "corrected": [],
            "outliers": [],
            "deleted_rows": [],
        }

        for ColumnName in Data.columns:
            DominantType = self._dominant_type(Data[ColumnName].tolist())
            if DominantType is None or DominantType == "text":
                continue

            Report["dominant_types"][ColumnName] = DominantType
            for RowPosition, RowLabel in enumerate(Data.index):
                Value = Data.at[RowLabel, ColumnName]
                if self._is_missing(Value) or str(Value).strip() == "":
                    continue

                CoercedValue = self._coerce_value(Value, DominantType)
                if CoercedValue is None:
                    OutlierRows.add(RowLabel)
                    Report["outliers"].append({
                        "row": RowPosition,
                        "row_label": RowLabel,
                        "column": ColumnName,
                        "expected_type": DominantType,
                        "value": Value,
                    })
                    continue

                if str(Value) != str(CoercedValue) or type(Value) is not type(CoercedValue):
                    Data.at[RowLabel, ColumnName] = CoercedValue
                    Report["corrected"].append({
                        "row": RowPosition,
                        "row_label": RowLabel,
                        "column": ColumnName,
                        "expected_type": DominantType,
                        "old_value": Value,
                        "new_value": CoercedValue,
                    })

        if self.OutlierAction == "delete" and OutlierRows:
            Report["deleted_rows"] = [
                Position
                for Position, RowLabel in enumerate(Data.index)
                if RowLabel in OutlierRows
            ]
            Data = Data.drop(index=list(OutlierRows))

        self.Report = Report

        if Ctx:
            Ctx.Log(
                "TypeConsistencyEnd",
                CorrectedCount=len(Report["corrected"]),
                OutlierCount=len(Report["outliers"]),
                DeletedRowCount=len(Report["deleted_rows"]),
            )

        return Data
