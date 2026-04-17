class ReplaceValuesNode:
    Name = "ReplaceValues"

    def __init__(self, ReplaceMap):
        self.ReplaceMap = dict(ReplaceMap)

    def Run(self, Data, Ctx=None):
        # Validate input
        if Data is None:
            raise ValueError("ReplaceValuesNode received no input data.")

        if Ctx:
            Ctx.Log("ReplaceValuesStart", ReplaceMap=self.ReplaceMap)

        Data = Data.copy()

        # Clean string values
        # # Trim leading/trailing whitespace from all string cells
        def clean_value(v):
            if isinstance(v, str):
                return v.strip()
            return v

        Data = Data.applymap(clean_value)

        # Prepare replace map
        # # Normalize keys to match cleaned data
        CleanMap = {}
        for k, v in self.ReplaceMap.items():
            if isinstance(k, str):
                k = k.strip()
            CleanMap[k] = v

        # Perform replacement
        # # Try exact replace first
        Keys = list(CleanMap.keys())
        ReplacedEstimateBefore = int(Data.isin(Keys).sum().sum())
        Data = Data.replace(CleanMap)
        ReplacedEstimateAfter = int(Data.isin(Keys).sum().sum())

        # # Fallback loose replace
        # # Match string forms so 34 can match "34" and vice versa
        if ReplacedEstimateBefore == ReplacedEstimateAfter and CleanMap:
            LooseMap = {str(k).strip(): v for k, v in CleanMap.items()}

            def replace_loose(v):
                if isinstance(v, str):
                    key = v.strip()
                else:
                    key = str(v).strip()

                if key in LooseMap:
                    return LooseMap[key]
                return v

            Data = Data.applymap(replace_loose)

        # Estimate remaining matches after loose replace
        FinalKeys = [str(k).strip() for k in CleanMap.keys()]
        RemainingEstimate = int(
            Data.applymap(lambda v: str(v).strip() if v is not None else v).isin(FinalKeys).sum().sum()
        )

        if Ctx:
            Ctx.Log(
                "ReplaceValuesEnd",
                ReplaceRuleCount=len(CleanMap),
                ValuesReplacedEstimate=int(ReplacedEstimateBefore - RemainingEstimate),
            )

        return Data