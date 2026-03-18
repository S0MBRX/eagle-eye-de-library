# ShowRunReportViewer

# Description
Displays a simple interactive GUI to step through a pipeline run report.

Allows users to:
- Navigate node-by-node
- View execution time
- See metrics and warnings
- Inspect errors

Useful for debugging and understanding pipeline execution flow.

# Code Example
```python
from eagle_eye_de.visualize import ShowRunReportViewer

Report = P.Run()

ShowRunReportViewer(Report)