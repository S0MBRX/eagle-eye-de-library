# EagleEyeDE

EagleEyeDE is a lightweight Python data engineering framework for building CSV cleaning pipelines from reusable nodes.

<strong><span style="color: purple;">API HERE</span></strong> - TestPyPI project page: https://test.pypi.org/project/eagle-eye-de/

It is designed for small to medium local ETL workflows where a full orchestration platform would be too heavy, but plain scripts would become difficult to maintain.

## Features

- Build data cleaning pipelines in Python code.
- Run reusable extract, transform, and load nodes.
- Add custom nodes for project-specific logic.
- View execution reports with node timings and errors.
- Launch a Tkinter visualiser for interactive pipeline building.
- Inspect raw CSV input and processed output stages.
- Extract tables from messy CSV files containing metadata or multiple tables.

## Installation

Install from PyPI or TestPyPI:

```bash
pip install eagle-eye-de
```

## Quick Start

Create a pipeline, add nodes, and run it:

```python
from eagle_eye_de import FormatRunReportForConsole, Pipeline
from eagle_eye_de.nodes import (
    ExtractCsvNode,
    NormalizeColumnsNode,
    ReplaceValuesNode,
    DropDuplicatesNode,
    WriteCsvNode,
)

pipeline = Pipeline("Customer Cleaning Pipeline")

pipeline.Add(ExtractCsvNode("shoppers_dirty.csv"))
pipeline.Add(NormalizeColumnsNode(Target="headers"))
pipeline.Add(ReplaceValuesNode({
    "UNKNOWN": "",
    "N/A": "",
    "United States": "USA",
}))
pipeline.Add(DropDuplicatesNode())
pipeline.Add(WriteCsvNode("shoppers_cleaned.csv"))

report = pipeline.Run()

print(FormatRunReportForConsole(report))
```

## Using the Visualiser

The visualiser can be launched from Python:

```python
from eagle_eye_de import LaunchVisualizer

LaunchVisualizer()
```

The visualiser lets you:

- select an input CSV file;
- preview the raw table;
- add nodes to a run order;
- configure node settings;
- run the pipeline;
- step through each processed stage;
- save the final processed CSV manually.

## Built-In Nodes

EagleEyeDE includes nodes for common CSV data cleaning tasks:

| Node | Purpose |
| --- | --- |
| `ExtractCsvNode` | Loads CSV data into a pipeline. |
| `ExtractTableNode` | Extracts one detected table from a messy multi-table CSV. |
| `NormalizeColumnsNode` | Normalises headers or cell values. |
| `ReplaceValuesNode` | Replaces matching values across the dataset. |
| `FilterNode` | Includes or excludes rows or columns by values or indexes. |
| `GenerateColumnNode` | Creates a new column from existing columns. |
| `TypeConsistencyNode` | Detects dominant data types and handles outliers. |
| `DropDuplicatesNode` | Removes duplicate rows. |
| `WriteCsvNode` | Writes processed data to a CSV file. |

## Extracting Tables From a Messy CSV

Some CSV files contain metadata, blank rows, or several tables in one file. `ExtractTableNode` can extract one detected table by number:

```python
from eagle_eye_de import Pipeline
from eagle_eye_de.nodes import ExtractCsvNode, ExtractTableNode, NormalizeColumnsNode, WriteCsvNode

pipeline = Pipeline("Extract Table Example")

pipeline.Add(ExtractCsvNode("multi_table_report.csv"))
pipeline.Add(ExtractTableNode(Table="1"))
pipeline.Add(NormalizeColumnsNode(Target="headers"))
pipeline.Add(WriteCsvNode("table_1_cleaned.csv"))

pipeline.Run()
```

Use `Table="2"` or `Table="3"` to extract later detected tables.

## Custom Nodes

Custom nodes can be added by creating a class with a `Run` method:

```python
class CustomerTierNode:
    Name = "CustomerTier"

    def __init__(self, SpendThreshold=250):
        self.SpendThreshold = SpendThreshold

    def Run(self, Data, Ctx=None):
        Data = Data.copy()
        Data["customer_tier"] = Data["total_spent"].apply(
            lambda value: "vip" if float(value) >= self.SpendThreshold else "standard"
        )
        return Data
```

Then add it to a pipeline:

```python
pipeline.Add(CustomerTierNode(SpendThreshold=250))
```

Custom nodes can also be passed to the visualiser:

```python
from eagle_eye_de import LaunchVisualizer

LaunchVisualizer(CustomNodes=[CustomerTierNode])
```

## API Overview

Main imports:

```python
from eagle_eye_de import Pipeline, FormatRunReportForConsole, LaunchVisualizer
from eagle_eye_de.nodes import ExtractCsvNode, NormalizeColumnsNode, WriteCsvNode
```

Core package areas:

- `eagle_eye_de.core` contains the pipeline and reporting classes.
- `eagle_eye_de.nodes.extract` contains CSV loading and table detection.
- `eagle_eye_de.nodes.transform` contains cleaning and transformation nodes.
- `eagle_eye_de.nodes.load` contains output/export nodes.
- `eagle_eye_de.visualize` contains the Tkinter visualiser.

## Examples

A code-only cleaning pipeline:

```python
from eagle_eye_de import FormatRunReportForConsole, Pipeline
from eagle_eye_de.nodes import (
    DropDuplicatesNode,
    ExtractCsvNode,
    FilterNode,
    NormalizeColumnsNode,
    ReplaceValuesNode,
    TypeConsistencyNode,
    WriteCsvNode,
)

pipeline = Pipeline("Normal Code Method No UI")

pipeline.Add(ExtractCsvNode("shoppers_dirty.csv"))
pipeline.Add(NormalizeColumnsNode(Target="headers"))
pipeline.Add(NormalizeColumnsNode(Target="values"))
pipeline.Add(ReplaceValuesNode({
    "unknown": None,
    "n/a": None,
    "": None,
    "united_states": "usa",
}))
pipeline.Add(TypeConsistencyNode(OutlierAction="highlight"))
pipeline.Add(FilterNode(
    Target="rows",
    Mode="exclude",
    MatchMode="or",
    MatchValues=["drop"],
))
pipeline.Add(DropDuplicatesNode())
pipeline.Add(WriteCsvNode("code_only_cleaned.csv"))

report = pipeline.Run()
print(FormatRunReportForConsole(report))
```

Extract multiple tables from one messy CSV:

```python
from eagle_eye_de import Pipeline
from eagle_eye_de.nodes import ExtractCsvNode, ExtractTableNode, NormalizeColumnsNode, WriteCsvNode

for table_number in (1, 2, 3):
    pipeline = Pipeline(f"Extract Table {table_number}")

    pipeline.Add(ExtractCsvNode("multi_table_report.csv"))
    pipeline.Add(ExtractTableNode(Table=str(table_number)))
    pipeline.Add(NormalizeColumnsNode(Target="headers"))
    pipeline.Add(WriteCsvNode(f"table_{table_number}_cleaned.csv"))

    pipeline.Run()
```

Launch the visualiser for normal UI use:

```python
from eagle_eye_de import LaunchVisualizer

LaunchVisualizer()
```

## Links

- Source: https://github.com/S0MBRX/eagle-eye-de-library
- Documentation: https://github.com/S0MBRX/eagle-eye-de-library#eagleeyede
- API Reference: https://github.com/S0MBRX/eagle-eye-de-library#api-overview
- Issues: https://github.com/S0MBRX/eagle-eye-de-library/issues
