# GenerateColumnNode

# Description
Creates a new column by applying a mathematical operation to two or more existing columns.
Supported operators include +, -, *, and /.

# code Example
```python
from eagle_eye_de.nodes import GenerateColumnNode

P.Add(GenerateColumnNode(
    NewColumn="revenue",
    Operator="*",
    Columns=["price", "quantity"]
))