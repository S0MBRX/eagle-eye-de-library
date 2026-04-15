def LaunchVisualizer():
    import ast
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    from eagle_eye_de import Pipeline
    from eagle_eye_de.nodes import (
        ExtractCsvNode,
        NormalizeColumnsNode,
        ReplaceValuesNode,
        DropDuplicatesNode,
        ColumnFilterNode,
        ValidateRequiredColumnsNode,
        WriteCsvNode,
    )

    root = tk.Tk()
    root.title("EagleEyeDE Visualizer")
    root.geometry("500x500")
    root.configure(bg="#5B6E8A")  # storm blue

    # STYLE
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    storm_blue = "#5B6E8A"
    panel_blue = "#6E82A1"
    green = "#3FA34D"
    green_active = "#4DB65B"

    style.configure("Storm.TFrame", background=storm_blue)
    style.configure("StormPanel.TFrame", background=panel_blue)
    style.configure("Storm.TLabelframe", background=panel_blue)
    style.configure("Storm.TLabelframe.Label", background=panel_blue, foreground="white")
    style.configure("Storm.TLabel", background=panel_blue, foreground="white")
    style.configure("StormTop.TLabel", background=storm_blue, foreground="white")
    style.configure("Storm.TCheckbutton", background=panel_blue, foreground="white")
    style.map("Storm.TCheckbutton", background=[("active", panel_blue)])

    style.configure(
        "Run.TButton",
        font=("Arial", 20, "bold"),
        padding=(20, 10),
        background=green,
        foreground="white",
        borderwidth=0,
    )
    style.map(
        "Run.TButton",
        background=[("active", green_active), ("pressed", green_active)],
        foreground=[("active", "white"), ("pressed", "white")],
    )

    style.configure(
        "Small.TButton",
        padding=(6, 3),
    )

    # STATE
    input_var = tk.StringVar()

    normalize_var = tk.BooleanVar(value=True)
    replace_var = tk.BooleanVar(value=False)
    dropdup_var = tk.BooleanVar(value=False)
    filter_var = tk.BooleanVar(value=False)
    validate_var = tk.BooleanVar(value=False)

    filter_mode_var = tk.StringVar(value="include")

    replace_rows = []
    filter_rows = []
    validate_rows = []

    preview_window = None
    preview_tree = None
    preview_info_var = tk.StringVar(value="No preview loaded.")

    # HELPERS
    def choose_input():
        path = filedialog.askopenfilename(
            title="Choose Input CSV",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if path:
            input_var.set(path)
            refresh_preview()

    def parse_literal_value(raw):
        raw = raw.strip()
        if raw == "":
            return ""

        try:
            return ast.literal_eval(raw)
        except Exception:
            return raw

    def show_section(section_frame, visible):
        if visible:
            section_frame.grid()
        else:
            section_frame.grid_remove()

    def toggle_section(var, section_frame):
        show_section(section_frame, var.get())
        if input_var.get().strip():
            refresh_preview()

    # PREVIEW HELPERS
    def ensure_preview_window():
        nonlocal preview_window, preview_tree

        if preview_window is not None and preview_window.winfo_exists():
            preview_window.lift()
            return

        preview_window = tk.Toplevel(root)
        preview_window.title("CSV Preview")
        preview_window.geometry("900x500")
        preview_window.configure(bg=storm_blue)

        preview_frame = ttk.Frame(preview_window, padding=10, style="Storm.TFrame")
        preview_frame.pack(fill="both", expand=True)

        ttk.Label(
            preview_frame,
            textvariable=preview_info_var,
            style="StormTop.TLabel"
        ).pack(anchor="w", pady=(0, 8))

        tree_frame = ttk.Frame(preview_frame)
        tree_frame.pack(fill="both", expand=True)

        preview_tree = ttk.Treeview(tree_frame, show="headings")
        preview_tree.grid(row=0, column=0, sticky="nsew")

        yscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=preview_tree.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        preview_tree.configure(yscrollcommand=yscroll.set)

        xscroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=preview_tree.xview)
        xscroll.grid(row=1, column=0, sticky="ew")
        preview_tree.configure(xscrollcommand=xscroll.set)

        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

    def build_preview_dataframe():
        import pandas as pd

        input_path = input_var.get().strip()
        if not input_path:
            return None

        df = pd.read_csv(input_path)

        # Normalize Columns
        if normalize_var.get():
            df.columns = [
                str(col).strip().lower().replace(" ", "_")
                for col in df.columns
            ]

        # Replace Values
        if replace_var.get():
            replace_map = build_replace_map()
            if replace_map:
                df = df.replace(replace_map)

        # Drop Duplicates
        if dropdup_var.get():
            df = df.drop_duplicates()

        # Column Filter
        if filter_var.get():
            filter_cols = build_filter_columns()
            if filter_cols:
                mode = filter_mode_var.get().strip().lower()
                if mode not in ("include", "exclude"):
                    mode = "include"

                if mode == "include":
                    missing = [col for col in filter_cols if col not in df.columns]
                    if missing:
                        raise ValueError(
                            "Column Filter preview failed. Missing columns: "
                            + ", ".join(missing)
                        )
                    df = df[filter_cols]
                else:
                    df = df.drop(columns=[col for col in filter_cols if col in df.columns])

        # Validate Required Columns
        if validate_var.get():
            validate_cols = build_validate_columns()
            if validate_cols:
                missing = [col for col in validate_cols if col not in df.columns]
                if missing:
                    raise ValueError(
                        "Validate Required Columns preview failed. Missing columns: "
                        + ", ".join(missing)
                    )

        return df.head(50)

    def show_dataframe_in_preview(df):
        if preview_tree is None:
            return

        preview_tree.delete(*preview_tree.get_children())

        columns = list(df.columns)
        preview_tree["columns"] = columns
        preview_tree["show"] = "headings"

        for col in columns:
            preview_tree.heading(col, text=str(col))
            preview_tree.column(col, width=120, anchor="w")

        for _, row in df.iterrows():
            preview_tree.insert("", "end", values=[str(v) for v in row.tolist()])

        preview_info_var.set(f"Previewing {len(df)} rows | {len(columns)} columns")

    def refresh_preview():
        try:
            ensure_preview_window()
            df = build_preview_dataframe()
            if df is None:
                preview_info_var.set("No preview loaded.")
                return
            show_dataframe_in_preview(df)
        except Exception as e:
            messagebox.showerror("Preview Error", str(e))

    def on_filter_mode_changed(event=None):
        if input_var.get().strip():
            refresh_preview()

    # REPLACE ROWS
    def refresh_replace_rows():
        for child in replace_rows_frame.winfo_children():
            child.destroy()

        for row_index, row_data in enumerate(replace_rows):
            row_frame = ttk.Frame(replace_rows_frame, style="StormPanel.TFrame")
            row_frame.grid(row=row_index, column=0, sticky="ew", pady=2)
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=1)

            from_entry = ttk.Entry(
                row_frame,
                textvariable=row_data["from_var"]
            )
            from_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
            from_entry.bind("<FocusOut>", lambda event: refresh_preview() if input_var.get().strip() else None)

            to_entry = ttk.Entry(
                row_frame,
                textvariable=row_data["to_var"]
            )
            to_entry.grid(row=0, column=1, sticky="ew", padx=(0, 6))
            to_entry.bind("<FocusOut>", lambda event: refresh_preview() if input_var.get().strip() else None)

            ttk.Button(
                row_frame,
                text="X",
                width=3,
                style="Small.TButton",
                command=lambda idx=row_index: delete_replace_row(idx)
            ).grid(row=0, column=2, sticky="e")

    def add_replace_row(from_value="", to_value=""):
        row_data = {
            "from_var": tk.StringVar(value=from_value),
            "to_var": tk.StringVar(value=to_value),
        }
        replace_rows.append(row_data)
        refresh_replace_rows()

        if input_var.get().strip():
            refresh_preview()

    def delete_replace_row(index):
        if 0 <= index < len(replace_rows):
            del replace_rows[index]

        if not replace_rows:
            add_replace_row()
        else:
            refresh_replace_rows()

        if input_var.get().strip():
            refresh_preview()

    def build_replace_map():
        replace_map = {}

        for row_data in replace_rows:
            left_raw = row_data["from_var"].get().strip()
            right_raw = row_data["to_var"].get().strip()

            if left_raw == "" and right_raw == "":
                continue

            if left_raw == "":
                raise ValueError("Each Replace Values row must have a value in the left input box.")

            left_val = parse_literal_value(left_raw)
            right_val = parse_literal_value(right_raw)
            replace_map[left_val] = right_val

        return replace_map

    # COLUMN FILTER ROWS
    def refresh_filter_rows():
        for child in filter_rows_frame.winfo_children():
            child.destroy()

        for row_index, row_data in enumerate(filter_rows):
            row_frame = ttk.Frame(filter_rows_frame, style="StormPanel.TFrame")
            row_frame.grid(row=row_index, column=0, sticky="ew", pady=2)
            row_frame.grid_columnconfigure(0, weight=1)

            value_entry = ttk.Entry(
                row_frame,
                textvariable=row_data["value_var"]
            )
            value_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
            value_entry.bind("<FocusOut>", lambda event: refresh_preview() if input_var.get().strip() else None)

            ttk.Button(
                row_frame,
                text="X",
                width=3,
                style="Small.TButton",
                command=lambda idx=row_index: delete_filter_row(idx)
            ).grid(row=0, column=1, sticky="e")

    def add_filter_row(value=""):
        row_data = {
            "value_var": tk.StringVar(value=value),
        }
        filter_rows.append(row_data)
        refresh_filter_rows()

        if input_var.get().strip():
            refresh_preview()

    def delete_filter_row(index):
        if 0 <= index < len(filter_rows):
            del filter_rows[index]

        if not filter_rows:
            add_filter_row()
        else:
            refresh_filter_rows()

        if input_var.get().strip():
            refresh_preview()

    def build_filter_columns():
        cols = []
        for row_data in filter_rows:
            value = row_data["value_var"].get().strip()
            if value:
                cols.append(value)
        return cols

    # VALIDATE REQUIRED COLUMNS ROWS
    def refresh_validate_rows():
        for child in validate_rows_frame.winfo_children():
            child.destroy()

        for row_index, row_data in enumerate(validate_rows):
            row_frame = ttk.Frame(validate_rows_frame, style="StormPanel.TFrame")
            row_frame.grid(row=row_index, column=0, sticky="ew", pady=2)
            row_frame.grid_columnconfigure(0, weight=1)

            value_entry = ttk.Entry(
                row_frame,
                textvariable=row_data["value_var"]
            )
            value_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
            value_entry.bind("<FocusOut>", lambda event: refresh_preview() if input_var.get().strip() else None)

            ttk.Button(
                row_frame,
                text="X",
                width=3,
                style="Small.TButton",
                command=lambda idx=row_index: delete_validate_row(idx)
            ).grid(row=0, column=1, sticky="e")

    def add_validate_row(value=""):
        row_data = {
            "value_var": tk.StringVar(value=value),
        }
        validate_rows.append(row_data)
        refresh_validate_rows()

        if input_var.get().strip():
            refresh_preview()

    def delete_validate_row(index):
        if 0 <= index < len(validate_rows):
            del validate_rows[index]

        if not validate_rows:
            add_validate_row()
        else:
            refresh_validate_rows()

        if input_var.get().strip():
            refresh_preview()

    def build_validate_columns():
        cols = []
        for row_data in validate_rows:
            value = row_data["value_var"].get().strip()
            if value:
                cols.append(value)
        return cols

    # RUN
    def run_pipeline():
        try:
            input_path = input_var.get().strip()

            if not input_path:
                messagebox.showerror("Missing Input", "Please choose an input CSV file.")
                return

            output_path = filedialog.asksaveasfilename(
                title="Save Output CSV As",
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
            )
            if not output_path:
                return

            P = Pipeline("UIRun")
            P.Add(ExtractCsvNode(input_path))

            if normalize_var.get():
                P.Add(NormalizeColumnsNode())

            if replace_var.get():
                replace_map = build_replace_map()
                if not replace_map:
                    messagebox.showerror(
                        "Missing Replace Values Settings",
                        "Replace Values is enabled, but no replace pairs were provided."
                    )
                    return
                P.Add(ReplaceValuesNode(replace_map))

            if dropdup_var.get():
                P.Add(DropDuplicatesNode())

            if filter_var.get():
                filter_cols = build_filter_columns()
                if not filter_cols:
                    messagebox.showerror(
                        "Missing Column Filter Settings",
                        "Column Filter is enabled, but no columns were provided."
                    )
                    return

                mode = filter_mode_var.get().strip().lower()
                if mode not in ("include", "exclude"):
                    mode = "include"

                P.Add(ColumnFilterNode(filter_cols, Mode=mode))

            if validate_var.get():
                validate_cols = build_validate_columns()
                if not validate_cols:
                    messagebox.showerror(
                        "Missing Validation Settings",
                        "Validate Required Columns is enabled, but no required columns were provided."
                    )
                    return

                P.Add(ValidateRequiredColumnsNode(validate_cols))

            P.Add(WriteCsvNode(output_path))

            root.update_idletasks()
            P.Run()

            messagebox.showinfo(
                "Pipeline Complete",
                f"Pipeline finished successfully.\n\nSaved output to:\n{output_path}"
            )

        except Exception as e:
            messagebox.showerror("Pipeline Error", str(e))

    # ROOT LAYOUT
    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # TOP BAR
    top = ttk.Frame(root, padding=10, style="Storm.TFrame")
    top.grid(row=0, column=0, sticky="ew")
    top.grid_columnconfigure(1, weight=1)

    ttk.Label(top, text="Input CSV", style="StormTop.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8))
    ttk.Entry(top, textvariable=input_var).grid(row=0, column=1, sticky="ew", padx=(0, 8))
    ttk.Button(top, text="Browse...", command=choose_input).grid(row=0, column=2, sticky="ew")
    ttk.Button(top, text="Refresh Preview", command=refresh_preview).grid(row=0, column=3, sticky="ew", padx=(8, 0))

    # MAIN CONTENT
    main = ttk.Frame(root, padding=(10, 0, 10, 10), style="Storm.TFrame")
    main.grid(row=1, column=0, sticky="nsew")
    main.grid_rowconfigure(0, weight=1)
    main.grid_columnconfigure(0, weight=1)

    nodes_box = ttk.LabelFrame(main, text="Pipeline Nodes", padding=10, style="Storm.TLabelframe")
    nodes_box.grid(row=0, column=0, sticky="nsew")
    nodes_box.grid_columnconfigure(0, weight=1)

    node_row = 0

    # NORMALIZE COLUMNS
    normalize_box = ttk.Frame(nodes_box, style="StormPanel.TFrame")
    normalize_box.grid(row=node_row, column=0, sticky="ew", pady=(0, 6))
    ttk.Checkbutton(
        normalize_box,
        text="Normalize Columns",
        variable=normalize_var,
        style="Storm.TCheckbutton",
        command=lambda: refresh_preview() if input_var.get().strip() else None
    ).grid(row=0, column=0, sticky="w")
    node_row += 1

    # REPLACE VALUES
    replace_box = ttk.Frame(nodes_box, style="StormPanel.TFrame")
    replace_box.grid(row=node_row, column=0, sticky="ew", pady=(0, 6))
    replace_box.grid_columnconfigure(0, weight=1)

    ttk.Checkbutton(
        replace_box,
        text="Replace Values",
        variable=replace_var,
        style="Storm.TCheckbutton",
        command=lambda: toggle_section(replace_var, replace_settings),
    ).grid(row=0, column=0, sticky="w")

    replace_settings = ttk.Frame(replace_box, padding=(24, 6, 0, 0), style="StormPanel.TFrame")
    replace_settings.grid(row=1, column=0, sticky="ew")
    replace_settings.grid_columnconfigure(0, weight=1)

    ttk.Label(replace_settings, text="Value To Find          Replace With", style="Storm.TLabel").grid(
        row=0, column=0, sticky="w", pady=(0, 4)
    )

    replace_rows_frame = ttk.Frame(replace_settings, style="StormPanel.TFrame")
    replace_rows_frame.grid(row=1, column=0, sticky="ew")
    replace_rows_frame.grid_columnconfigure(0, weight=1)

    ttk.Button(
        replace_settings,
        text="+ Add Row",
        style="Small.TButton",
        command=add_replace_row
    ).grid(row=2, column=0, sticky="w", pady=(6, 0))

    ttk.Label(
        replace_settings,
        text="Example: N/A        None",
        style="Storm.TLabel"
    ).grid(row=3, column=0, sticky="w", pady=(4, 0))

    node_row += 1

    # DROP DUPLICATES
    dropdup_box = ttk.Frame(nodes_box, style="StormPanel.TFrame")
    dropdup_box.grid(row=node_row, column=0, sticky="ew", pady=(0, 6))
    ttk.Checkbutton(
        dropdup_box,
        text="Drop Duplicates",
        variable=dropdup_var,
        style="Storm.TCheckbutton",
        command=lambda: refresh_preview() if input_var.get().strip() else None
    ).grid(row=0, column=0, sticky="w")
    node_row += 1

    # COLUMN FILTER
    filter_box = ttk.Frame(nodes_box, style="StormPanel.TFrame")
    filter_box.grid(row=node_row, column=0, sticky="ew", pady=(0, 6))
    filter_box.grid_columnconfigure(0, weight=1)

    ttk.Checkbutton(
        filter_box,
        text="Column Filter",
        variable=filter_var,
        style="Storm.TCheckbutton",
        command=lambda: toggle_section(filter_var, filter_settings),
    ).grid(row=0, column=0, sticky="w")

    filter_settings = ttk.Frame(filter_box, padding=(24, 6, 0, 0), style="StormPanel.TFrame")
    filter_settings.grid(row=1, column=0, sticky="ew")
    filter_settings.grid_columnconfigure(0, weight=1)

    ttk.Label(filter_settings, text="Mode", style="Storm.TLabel").grid(row=0, column=0, sticky="w")

    filter_mode_combo = ttk.Combobox(
        filter_settings,
        textvariable=filter_mode_var,
        values=["include", "exclude"],
        state="readonly",
        width=14
    )
    filter_mode_combo.grid(row=1, column=0, sticky="w", pady=(2, 6))
    filter_mode_combo.bind("<<ComboboxSelected>>", on_filter_mode_changed)

    ttk.Label(filter_settings, text="Columns", style="Storm.TLabel").grid(row=2, column=0, sticky="w")

    filter_rows_frame = ttk.Frame(filter_settings, style="StormPanel.TFrame")
    filter_rows_frame.grid(row=3, column=0, sticky="ew")
    filter_rows_frame.grid_columnconfigure(0, weight=1)

    ttk.Button(
        filter_settings,
        text="+ Add Row",
        style="Small.TButton",
        command=add_filter_row
    ).grid(row=4, column=0, sticky="w", pady=(6, 0))

    ttk.Label(
        filter_settings,
        text="Example: customer_name",
        style="Storm.TLabel"
    ).grid(row=5, column=0, sticky="w", pady=(4, 0))

    node_row += 1

    # VALIDATE REQUIRED COLUMNS
    validate_box = ttk.Frame(nodes_box, style="StormPanel.TFrame")
    validate_box.grid(row=node_row, column=0, sticky="ew", pady=(0, 6))
    validate_box.grid_columnconfigure(0, weight=1)

    ttk.Checkbutton(
        validate_box,
        text="Validate Required Columns",
        variable=validate_var,
        style="Storm.TCheckbutton",
        command=lambda: toggle_section(validate_var, validate_settings),
    ).grid(row=0, column=0, sticky="w")

    validate_settings = ttk.Frame(validate_box, padding=(24, 6, 0, 0), style="StormPanel.TFrame")
    validate_settings.grid(row=1, column=0, sticky="ew")
    validate_settings.grid_columnconfigure(0, weight=1)

    ttk.Label(validate_settings, text="Required Columns", style="Storm.TLabel").grid(row=0, column=0, sticky="w")

    validate_rows_frame = ttk.Frame(validate_settings, style="StormPanel.TFrame")
    validate_rows_frame.grid(row=1, column=0, sticky="ew")
    validate_rows_frame.grid_columnconfigure(0, weight=1)

    ttk.Button(
        validate_settings,
        text="+ Add Row",
        style="Small.TButton",
        command=add_validate_row
    ).grid(row=2, column=0, sticky="w", pady=(6, 0))

    ttk.Label(
        validate_settings,
        text="Example: email_address",
        style="Storm.TLabel"
    ).grid(row=3, column=0, sticky="w", pady=(4, 0))

    node_row += 1

    # INITIAL VISIBILITY
    show_section(replace_settings, replace_var.get())
    show_section(filter_settings, filter_var.get())
    show_section(validate_settings, validate_var.get())

    add_replace_row()
    add_filter_row()
    add_validate_row()

    # BOTTOM CONTROLS
    bottom = ttk.Frame(root, padding=(10, 0, 10, 14), style="Storm.TFrame")
    bottom.grid(row=2, column=0, sticky="ew")
    bottom.grid_columnconfigure(0, weight=1)
    bottom.grid_columnconfigure(1, weight=0)
    bottom.grid_columnconfigure(2, weight=1)

    ttk.Button(
        bottom,
        text="Run Pipeline",
        style="Run.TButton",
        command=run_pipeline
    ).grid(row=0, column=1, pady=(6, 0))

    root.mainloop()