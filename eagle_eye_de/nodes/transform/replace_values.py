class ReplaceValuesNode:
    Name = "ReplaceValues"

    def __init__(self, ReplaceMap):
        self.ReplaceMap = dict(ReplaceMap)

    def Run(self, Data, Ctx=None):
        if Data is None:
            raise ValueError("ReplaceValuesNode received no input data.")

        if Ctx:
            Ctx.Log("ReplaceValuesStart", ReplaceMap=self.ReplaceMap)

        Data = Data.copy()

        ReplacedEstimateBefore = Data.isin(list(self.ReplaceMap.keys())).sum().sum()
        Data = Data.replace(self.ReplaceMap)
        ReplacedEstimateAfter = Data.isin(list(self.ReplaceMap.keys())).sum().sum()

        if Ctx:
            Ctx.Log(
                "ReplaceValuesEnd",
                ReplaceRuleCount=len(self.ReplaceMap),
                ValuesReplacedEstimate=int(ReplacedEstimateBefore - ReplacedEstimateAfter),
            )

        return Data