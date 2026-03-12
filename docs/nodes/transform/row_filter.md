# RowFilterNode

# Description
Filters rows from the dataset based on a condition expression.
The condition uses pandas query syntax.

# code Example
```python
from eagle_eye_de.nodes import RowFilterNode

P.Add(RowFilterNode("age >= 18"))