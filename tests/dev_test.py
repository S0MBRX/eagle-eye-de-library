from pathlib import Path
import sys

RepoRoot = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RepoRoot))

from eagle_eye_de.visualize import LaunchVisualizer

LaunchVisualizer()

from eagle_eye_de.visualize import LaunchVisualizer
from eagle_eye_de import Pipeline, FormatRunReportForConsole
from eagle_eye_de.nodes import (
    ExtractCsvNode,
    NormalizeColumnsNode,
    ReplaceValuesNode,
    ColumnFilterNode,
    DropDuplicatesNode,
    ValidateRequiredColumnsNode,
    WriteCsvNode,
)

mode = input("Choose mode: (v)isual or (c)ode: ").strip().lower()

# visualizer
if mode == "v":
    LaunchVisualizer()

# pipeline test
elif mode == "c":
    P = Pipeline("ShoppersDirtyTest")

    P.Add(ExtractCsvNode("Data/shoppers_dirty.csv"))
    P.Add(NormalizeColumnsNode())
    P.Add(ReplaceValuesNode({
        "UNKNOWN": None,
        "N/A": None,
        "": None,
    }))
    P.Add(ColumnFilterNode(
        [
            "customer_name",
            "age",
            "email_address",
            "total_spent_($)",
            "member_since",
            "last_purchase",
            "country",
        ],
        Mode="include"
    ))
    P.Add(DropDuplicatesNode())
    P.Add(ValidateRequiredColumnsNode([
        "customer_name",
        "age",
        "email_address",
        "total_spent_($)",
        "country",
    ]))
    P.Add(WriteCsvNode("Data/shoppers_cleaned.csv"))

    Report = P.Run()
    print(FormatRunReportForConsole(Report))
