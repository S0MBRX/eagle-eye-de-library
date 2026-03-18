def ShowRunReportViewer(Report):
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title(f"Pipeline Viewer - {Report.PipelineName}")
    root.geometry("900x600")

    current_index = {"i": 0}

    # UI elements
    title = tk.Label(root, text="", font=("Arial", 16))
    title.pack(pady=10)

    info = tk.Label(root, text="", font=("Arial", 10))
    info.pack()

    text = tk.Text(root, wrap="none")
    text.pack(expand=True, fill="both")

    def render():
        i = current_index["i"]
        record = Report.Records[i]

        title.config(text=f"Step {i+1}/{len(Report.Records)}: {record.NodeName}")

        info.config(
            text=f"OK: {record.Ok} | Time: {record.DurationMs:.2f}ms"
        )

        text.delete("1.0", tk.END)

        text.insert(tk.END, "Metrics:\n")
        for k, v in record.Metrics.items():
            text.insert(tk.END, f"  {k}: {v}\n")

        if record.Warnings:
            text.insert(tk.END, "\nWarnings:\n")
            for w in record.Warnings:
                text.insert(tk.END, f"  - {w}\n")

        if record.Error:
            text.insert(tk.END, "\nError:\n")
            text.insert(tk.END, f"  {record.Error}\n")

    def next_step():
        if current_index["i"] < len(Report.Records) - 1:
            current_index["i"] += 1
            render()

    def prev_step():
        if current_index["i"] > 0:
            current_index["i"] -= 1
            render()

    controls = tk.Frame(root)
    controls.pack(pady=10)

    tk.Button(controls, text="Previous", command=prev_step).pack(side="left", padx=10)
    tk.Button(controls, text="Next", command=next_step).pack(side="left", padx=10)

    render()
    root.mainloop()