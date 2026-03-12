from eagle_eye_de.nodes  import NodeResult


class ValidateRequiredColumnsNode:
    Name = "ValidateRequiredColumns"

    def __init__(self, Columns):
        self.Columns = list(Columns)

    def Run(self, Data, Ctx=None):
        if Data is None:
            raise ValueError("ValidateRequiredColumnsNode received no input data.")

        if Ctx:
            Ctx.Log("ValidateRequiredColumnsStart", Columns=self.Columns)

        MissingColumns = [Column for Column in self.Columns if Column not in Data.columns]

        if MissingColumns:
            raise ValueError(f"ValidateRequiredColumnsNode missing columns: {MissingColumns}")

        Metrics = {
            "RequiredColumnCount": len(self.Columns),
            "MissingColumnCount": 0,
        }

        if Ctx:
            Ctx.Log("ValidateRequiredColumnsEnd", RequiredColumnCount=len(self.Columns))

        return NodeResult(
            Data=Data,
            Metrics=Metrics,
            Warnings=[]
        )