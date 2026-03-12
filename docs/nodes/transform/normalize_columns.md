# NormalizeColumnsNode

# Description
Standardizes column names by converting them to lowercase, trimming whitespace, and replacing spaces with underscores.
This helps ensure consistent column naming across datasets.

# code Example
```python
from eagle_eye_de.nodes import NormalizeColumnsNode

P.Add(NormalizeColumnsNode())