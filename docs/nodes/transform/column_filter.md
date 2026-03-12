# ColumnFilterNode

# Description
Filters columns from the dataset.
Supports two modes:
include – keeps only the specified columns
exclude – removes the specified columns

# code Example
```python
from eagle_eye_de.nodes import ColumnFilterNode

P.Add(ColumnFilterNode(
    ["id", "price", "quantity"],
    Mode="include"
))