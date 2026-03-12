# ValidateRequiredColumnsNode

# Description
Checks that all required columns exist in the dataset.
If any required columns are missing, the pipeline raises an error and stops.

# code Example
```python
from eagle_eye_de.nodes import ValidateRequiredColumnsNode

P.Add(ValidateRequiredColumnsNode([
    "id",
    "price",
    "quantity"
]))