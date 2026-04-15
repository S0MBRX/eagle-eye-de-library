# LaunchVisualizer

# Description
Launches a Tkinter-based UI that allows users to build, run, and inspect data pipelines without writing code.

Users can:
- Select input/output CSV files
- Enable/disable nodes
- Configure node parameters
- Run the pipeline
- Step through execution results

# Code Example
```python
from eagle_eye_de.visualize import LaunchVisualizer

LaunchVisualizer()