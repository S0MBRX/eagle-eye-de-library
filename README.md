# EagleEyeDE

EagleEyeDE is a Python data engineering framework for building CSV cleaning pipelines from reusable nodes.

<strong><span style="color: purple;">API HERE</span></strong> - TestPyPI project page: https://test.pypi.org/project/eagle-eye-de/

It is useful when you want a clear pipeline structure instead of one long cleaning script. You can use it through normal Python code, or launch the visualiser and build a pipeline interactively.

## Quick Start: Visualiser

The fastest way to try EagleEyeDE is to launch the visualiser:

```python
from eagle_eye_de import LaunchVisualizer

LaunchVisualizer()
```

This opens the UI, where you can:

- select a CSV file;
- preview the raw input;
- add cleaning nodes to the run order;
- configure node settings;
- run the pipeline;
- step through each processed stage;
- save the final cleaned CSV.

## Installation

Install the package with pip:

```bash
pip install eagle-eye-de
```

## Quick Start: Code Pipeline

Pipelines can also be created directly in Python. A pipeline is just a sequence of nodes. Each node receives the current table, changes it, and passes it to the next node.

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

## Recommended Use

For exploring a new messy CSV, start with the visualiser:

```python
from eagle_eye_de import LaunchVisualizer

LaunchVisualizer()
```

For repeatable workflows, write the pipeline in code:

```python
pipeline = Pipeline("Repeatable Cleaning Pipeline")
pipeline.Add(ExtractCsvNode("input.csv"))
pipeline.Add(NormalizeColumnsNode(Target="headers"))
pipeline.Add(WriteCsvNode("output.csv"))
pipeline.Run()
```

The visualiser is best for seeing what each node does. Code pipelines are best when you know the steps and want to run them again.

## How Pipelines Work

EagleEyeDE uses a simple node pipeline:

```text
CSV input -> Node 1 -> Node 2 -> Node 3 -> CSV output
```

Each node should do one job. For example:

```python
pipeline.Add(ExtractCsvNode("input.csv"))
pipeline.Add(NormalizeColumnsNode(Target="headers"))
pipeline.Add(TypeConsistencyNode(OutlierAction="highlight"))
pipeline.Add(WriteCsvNode("output.csv"))
```

The output of each node becomes the input for the next node.

## Built-In Nodes

The main built-in nodes are:

- `ExtractCsvNode`
- `ExtractTableNode`
- `NormalizeColumnsNode`
- `ReplaceValuesNode`
- `FilterNode`
- `GenerateColumnNode`
- `TypeConsistencyNode`
- `DropDuplicatesNode`
- `WriteCsvNode`

## ExtractCsvNode

Loads a CSV file into the pipeline.

### How it works

`ExtractCsvNode` reads a CSV file and returns a Pandas dataframe. By default, it loads the file as raw rows, which helps with messy CSV files that may contain metadata, blank rows, or multiple tables.

### Recommended use

Use this as the first node in most pipelines.

### Example

```python
from eagle_eye_de.nodes import ExtractCsvNode

pipeline.Add(ExtractCsvNode("shoppers_dirty.csv"))
```

You can also load a detected table directly:

```python
pipeline.Add(ExtractCsvNode("multi_table_report.csv", Table="1"))
```

## ExtractTableNode

Extracts one detected table from a messy CSV that has already been loaded.

### How it works

Some CSV files contain report titles, metadata rows, blank spacing, and several tables in the same file. `ExtractTableNode` scans the raw rows and extracts the selected table number.

### Recommended use

Use this after `ExtractCsvNode` when the input CSV contains more than one table or has metadata before the real table.

### Example

```python
from eagle_eye_de.nodes import ExtractCsvNode, ExtractTableNode

pipeline.Add(ExtractCsvNode("multi_table_report.csv"))
pipeline.Add(ExtractTableNode(Table="1"))
```

To extract later tables:

```python
pipeline.Add(ExtractTableNode(Table="2"))
pipeline.Add(ExtractTableNode(Table="3"))
```

## NormalizeColumnsNode

Normalises either column headers or all cell values.

### How it works

The node trims whitespace, lowercases text, and replaces spaces with underscores. It can target column headers or cell values.

### Recommended use

Use `Target="headers"` near the start of a pipeline so later nodes can work with cleaner column names. Use `Target="values"` when the table contains inconsistent text values.

### Examples

Normalise headers:

```python
from eagle_eye_de.nodes import NormalizeColumnsNode

pipeline.Add(NormalizeColumnsNode(Target="headers"))
```

Normalise all cell values:

```python
pipeline.Add(NormalizeColumnsNode(Target="values"))
```

Example header changes:

```text
Customer Name -> customer_name
Email Address -> email_address
Total Spent ($) -> total_spent_($)
```

## ReplaceValuesNode

Replaces matching values across the dataframe.

### How it works

`ReplaceValuesNode` accepts a dictionary. Keys are values to find. Values are replacements. It trims string values before matching, then performs replacements across the whole table.

### Recommended use

Use this for missing value markers, inconsistent labels, or repeated dirty values.

### Example

```python
from eagle_eye_de.nodes import ReplaceValuesNode

pipeline.Add(ReplaceValuesNode({
    "UNKNOWN": "",
    "N/A": "",
    "United States": "USA",
    "U.K.": "UK",
}))
```

## FilterNode

Includes or excludes rows or columns.

### How it works

`FilterNode` can target either rows or columns. It can match by values or by index positions.

Main settings:

- `Target`: `"rows"` or `"columns"`
- `Mode`: `"include"` or `"exclude"`
- `MatchMode`: `"or"` or `"and"`
- `MatchValues`: values or indexes to match
- `MatchBy`: `"values"` or `"index"`

### Recommended use

Use this when you want to keep or remove rows/columns based on specific values, markers, or positions.

### Examples

Keep rows containing `UK` or `USA`:

```python
from eagle_eye_de.nodes import FilterNode

pipeline.Add(FilterNode(
    Target="rows",
    Mode="include",
    MatchMode="or",
    MatchValues=["UK", "USA"],
    MatchBy="values",
))
```

Remove columns containing a marker value:

```python
pipeline.Add(FilterNode(
    Target="columns",
    Mode="exclude",
    MatchMode="or",
    MatchValues=["DROP"],
    MatchBy="values",
))
```

Keep only columns 1 to 3:

```python
pipeline.Add(FilterNode(
    Target="columns",
    Mode="include",
    MatchMode="or",
    MatchValues=["1-3"],
    MatchBy="index",
))
```

## GenerateColumnNode

Creates a new numeric column from existing columns.

### How it works

`GenerateColumnNode` takes a new column name, an arithmetic operator, and at least two source columns. It resolves column names flexibly, so normalised column names can still match the requested names.

Supported operators:

- `+`
- `-`
- `*`
- `/`

### Recommended use

Use this when a dataset contains separate numeric fields that should be combined into a new calculated field.

### Example

```python
from eagle_eye_de.nodes import GenerateColumnNode

pipeline.Add(GenerateColumnNode(
    "total_cost",
    "*",
    ["unit_price", "quantity"],
))
```

## TypeConsistencyNode

Finds columns with a dominant data type and handles values that do not match.

### How it works

The node checks each column and looks for a dominant type such as integer or float. It then tries to coerce values that can be corrected. For example, text numbers such as `five` or `fifty-seven` can be converted where possible.

Values that cannot be safely corrected are treated as outliers.

### Recommended use

Use this after basic cleaning and normalisation. It is useful for catching values such as `burger` in a mostly numeric column.

### Examples

Flag unresolved outliers:

```python
from eagle_eye_de.nodes import TypeConsistencyNode

pipeline.Add(TypeConsistencyNode(OutlierAction="highlight"))
```

Delete rows containing unresolved outliers:

```python
pipeline.Add(TypeConsistencyNode(OutlierAction="delete"))
```

## DropDuplicatesNode

Removes duplicate rows.

### How it works

The node calls Pandas duplicate removal and returns the dataframe with repeated rows removed.

### Recommended use

Use this after normalising and replacing values, because dirty formatting can stop duplicates from matching.

### Example

```python
from eagle_eye_de.nodes import DropDuplicatesNode

pipeline.Add(DropDuplicatesNode())
```

You can also pass a subset of columns:

```python
pipeline.Add(DropDuplicatesNode(Subset=["customer_name", "email_address"]))
```

## WriteCsvNode

Writes the processed dataframe to a CSV file.

### How it works

`WriteCsvNode` saves the current dataframe to disk. By default, it does not write the dataframe index.

### Recommended use

Use this as the final node in a code pipeline.

### Example

```python
from eagle_eye_de.nodes import WriteCsvNode

pipeline.Add(WriteCsvNode("cleaned_output.csv"))
```

## Custom Nodes

Custom nodes let you add project-specific logic without changing the library source code.

### Basic custom node

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

### Use it in code

```python
pipeline.Add(CustomerTierNode(SpendThreshold=250))
```

### Use it in the visualiser

```python
from eagle_eye_de import LaunchVisualizer

LaunchVisualizer(CustomNodes=[CustomerTierNode])
```

Custom nodes passed into the visualiser appear before the built-in nodes.

## Full Example Pipeline

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

pipeline = Pipeline("Full Cleaning Pipeline")

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
pipeline.Add(WriteCsvNode("cleaned_output.csv"))

report = pipeline.Run()

print(FormatRunReportForConsole(report))
```

## Multi-Table CSV Example

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

## API Overview

Main imports:

```python
from eagle_eye_de import Pipeline, FormatRunReportForConsole, LaunchVisualizer
from eagle_eye_de.nodes import ExtractCsvNode, NormalizeColumnsNode, WriteCsvNode
```

Package areas:

- `eagle_eye_de.core` contains the pipeline and reporting classes.
- `eagle_eye_de.nodes.extract` contains CSV loading and table detection.
- `eagle_eye_de.nodes.transform` contains cleaning and transformation nodes.
- `eagle_eye_de.nodes.load` contains output/export nodes.
- `eagle_eye_de.visualize` contains the Tkinter visualiser.

## Links

- Source: https://github.com/S0MBRX/eagle-eye-de-library
- Documentation: https://github.com/S0MBRX/eagle-eye-de-library#eagleeyede
- API Reference: https://github.com/S0MBRX/eagle-eye-de-library#api-overview
- Issues: https://github.com/S0MBRX/eagle-eye-de-library/issues
