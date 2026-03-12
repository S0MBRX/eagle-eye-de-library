# ReplaceValuesNode

# Description
Replaces values in the dataset according to a mapping dictionary.
Useful for cleaning placeholder values such as "N/A", "UNKNOWN", or other inconsistent values.

# code Example
```python
from eagle_eye_de.nodes import ReplaceValuesNode

P.Add(ReplaceValuesNode({
    "N/A": None,
    "UNKNOWN": None
}))