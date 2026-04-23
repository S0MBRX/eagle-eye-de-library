def LaunchVisualizer(CustomNodes=None):
    import ast
    import os
    import time
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    from eagle_eye_de.nodes import (
        ExtractCsvNode,
        ExtractTableNode,
        NormalizeColumnsNode,
        ReplaceValuesNode,
        DropDuplicatesNode,
        FilterNode,
        GenerateColumnNode,
        TypeConsistencyNode,
        ValidateRequiredColumnsNode,
    )
    from eagle_eye_de.nodes.extract.csv import DetectCsvTables, ReadCsvRows

    root = tk.Tk()
    root.title("EagleEyeDE Visualizer")
    root.geometry("594x775")
    root.configure(bg="#5B6E8A")

    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    storm_blue = "#5B6E8A"
    panel_blue = "#6E82A1"
    green = "#3FA34D"
    green_active = "#4DB65B"
    red = "#B64242"
    red_active = "#C75252"
    custom_purple = "#D7B6FF"

    def blend_hex(left, right, amount):
        left = left.lstrip("#")
        right = right.lstrip("#")
        channels = []
        for index in range(0, 6, 2):
            left_value = int(left[index:index + 2], 16)
            right_value = int(right[index:index + 2], 16)
            channels.append(round(left_value + (right_value - left_value) * amount))
        return "#" + "".join(f"{value:02X}" for value in channels)

    style.configure("Storm.TFrame", background=storm_blue)
    style.configure("StormPanel.TFrame", background=panel_blue)
    style.configure("Storm.TLabelframe", background=panel_blue)
    style.configure("Storm.TLabelframe.Label", background=panel_blue, foreground="white")
    style.configure("Storm.TLabel", background=panel_blue, foreground="white")
    style.configure("CustomStorm.TLabel", background=panel_blue, foreground=custom_purple)
    style.configure("StormTop.TLabel", background=storm_blue, foreground="white")
    style.configure("ProcessedTitle.TLabel", background=storm_blue, foreground="white", font=("Arial", 30, "bold"))
    style.configure("ProcessedFinalTitle.TLabel", background=storm_blue, foreground=green, font=("Arial", 30, "bold"))
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
        "RunDisabled.TButton",
        font=("Arial", 18, "bold"),
        padding=(20, 10),
        background=red,
        foreground="white",
        borderwidth=0,
    )
    style.map(
        "RunDisabled.TButton",
        background=[("disabled", red), ("active", red), ("pressed", red)],
        foreground=[("disabled", "white"), ("active", "white"), ("pressed", "white")],
    )

    style.configure("Small.TButton", padding=(6, 3))
    style.configure(
        "NodeToggle.TButton",
        padding=(6, 3),
        background=panel_blue,
        foreground="white",
        borderwidth=0,
        anchor="w",
    )
    style.map(
        "NodeToggle.TButton",
        background=[("active", panel_blue), ("pressed", panel_blue)],
        foreground=[("active", "white"), ("pressed", "white")],
    )
    style.configure(
        "CustomNodeToggle.TButton",
        padding=(6, 3),
        background=panel_blue,
        foreground=custom_purple,
        borderwidth=0,
        anchor="w",
    )
    style.map(
        "CustomNodeToggle.TButton",
        background=[("active", panel_blue), ("pressed", panel_blue)],
        foreground=[("active", custom_purple), ("pressed", custom_purple)],
    )
    style.configure(
        "Add.TButton",
        font=("Arial", 13, "bold"),
        padding=(8, 3),
        background=green,
        foreground="white",
        borderwidth=0,
    )
    style.map(
        "Add.TButton",
        background=[("active", green_active), ("pressed", green_active)],
        foreground=[("active", "white"), ("pressed", "white")],
    )
    style.configure("Save.TButton", background=green, foreground="white", padding=(6, 3), borderwidth=0)
    style.map("Save.TButton", background=[("active", green_active), ("pressed", green_active)])
    style.configure("Danger.TButton", background=red, foreground="white", padding=(6, 3), borderwidth=0)
    style.map("Danger.TButton", background=[("active", red_active), ("pressed", red_active)])
    style.configure("BrowsePulse.TButton", padding=(6, 3), background=green, foreground="white", borderwidth=0)
    style.map("BrowsePulse.TButton", background=[("active", green_active), ("pressed", green_active)])
    style.configure("Flash.TEntry", fieldbackground="#FFB6B6")
    browse_pulse_styles = []
    add_pulse_styles = []
    order_pulse_styles = []
    browse_pulse_positions = [
        0.0, 0.04, 0.09, 0.15, 0.22, 0.3, 0.39, 0.49, 0.6, 0.72, 0.84, 0.94,
        1.0, 0.94, 0.84, 0.72, 0.6, 0.49, 0.39, 0.3, 0.22, 0.15, 0.09, 0.04,
    ]
    for pulse_index, pulse_position in enumerate(browse_pulse_positions):
        pulse_color = blend_hex(green, "#D9D9D9", pulse_position)
        order_pulse_color = blend_hex(red, panel_blue, pulse_position)
        style_name = f"BrowsePulse{pulse_index}.TButton"
        text_color = "white" if pulse_position < 0.6 else "black"
        style.configure(style_name, padding=(6, 3), background=pulse_color, foreground=text_color, borderwidth=0)
        style.map(style_name, background=[("active", pulse_color), ("pressed", pulse_color)])
        browse_pulse_styles.append(style_name)
        add_style_name = f"AddPulse{pulse_index}.TButton"
        style.configure(
            add_style_name,
            font=("Arial", 13, "bold"),
            padding=(8, 3),
            background=pulse_color,
            foreground=text_color,
            borderwidth=0,
        )
        style.map(add_style_name, background=[("active", pulse_color), ("pressed", pulse_color)])
        add_pulse_styles.append(add_style_name)
        order_style_name = f"OrderPulse{pulse_index}.TLabelframe"
        style.configure(
            order_style_name,
            background=panel_blue,
            bordercolor=order_pulse_color,
            lightcolor=order_pulse_color,
            darkcolor=order_pulse_color,
            borderwidth=3,
            relief="solid",
        )
        style.configure(f"{order_style_name}.Label", background=panel_blue, foreground="white")
        order_pulse_styles.append(order_style_name)

    input_var = tk.StringVar()
    browse_button = None
    browse_pulse_index = 0
    run_pipeline_button = None

    normalize_var = tk.BooleanVar(value=True)
    replace_var = tk.BooleanVar(value=False)
    dropdup_var = tk.BooleanVar(value=False)
    filter_var = tk.BooleanVar(value=False)
    generate_var = tk.BooleanVar(value=False)
    validate_var = tk.BooleanVar(value=False)

    extract_table_var = tk.StringVar(value="1")
    extract_table_recommendation_var = tk.StringVar(value="Example inputs: 1, 2, 3 or 4 etc.")
    extract_table_entry = None
    normalize_target_var = tk.StringVar(value="all cells")
    type_outlier_action_var = tk.StringVar(value="highlight")
    filter_target_var = tk.StringVar(value="rows")
    filter_mode_var = tk.StringVar(value="include")
    filter_match_mode_var = tk.StringVar(value="or")
    filter_match_by_var = tk.StringVar(value="values")
    filter_description_var = tk.StringVar(value="")
    generate_column_name_var = tk.StringVar(value="")
    generate_operator_var = tk.StringVar(value="+")

    replace_rows = []
    filter_rows = []
    generate_rows = []
    validate_rows = []
    operation_order = []
    customizing_order_index = None
    order_section_box = None
    order_pulse_job = None
    order_pulse_index = 0
    tunable_nodes = {
        "Extract Table",
        "Normalize",
        "Replace Values",
        "Coerce Data Types",
        "Filter",
        "Generate Column",
        "Validate Required Columns",
    }
    tunable_add_buttons = {}
    tunable_reset_buttons = {}
    tunable_pulse_jobs = {}
    tunable_pulse_index = {}
    initializing_tunables = False

    preview_window = None
    preview_table_state = {}
    preview_info_var = tk.StringVar(value="No preview loaded.")

    processed_window = None
    processed_table_state = {}
    processed_title_label = None
    processed_title_var = tk.StringVar(value="")
    processed_diag_var = tk.StringVar(value="")

    processed_steps = []
    processed_step_index = 0
    processed_play_job = None
    processed_is_playing = False
    processed_play_button = None

    def get_custom_node_label(node_source):
        if isinstance(node_source, dict):
            label = node_source.get("label") or node_source.get("name")
            node_source = node_source.get("node") or node_source.get("class") or node_source.get("factory")
            if label:
                return str(label)

        return str(getattr(node_source, "Name", getattr(node_source, "__name__", node_source.__class__.__name__)))

    custom_node_specs = {}
    for custom_node in (CustomNodes or []):
        node_source = custom_node
        label = get_custom_node_label(custom_node)
        if isinstance(custom_node, dict):
            node_source = custom_node.get("node") or custom_node.get("class") or custom_node.get("factory")

        if node_source is None:
            continue

        display_name = f"{label} (custom)"
        custom_node_specs[display_name] = {
            "label": label,
            "source": node_source,
        }

    custom_node_names = set(custom_node_specs)

    def create_custom_node(spec):
        source = spec["source"]
        if isinstance(source, type):
            return source()
        if callable(source) and not hasattr(source, "Run"):
            return source()
        return source

    def choose_input():
        path = filedialog.askopenfilename(
            title="Choose Input CSV",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if path:
            input_var.set(path)
            update_extract_table_recommendation(path)
            refresh_preview()

    def update_extract_table_recommendation(path=None):
        path = path or input_var.get().strip()
        if not path:
            extract_table_recommendation_var.set("Example inputs: 1, 2, 3 or 4 etc.")
            return

        try:
            tables = DetectCsvTables(path)
        except Exception:
            extract_table_recommendation_var.set("Example inputs: 1, 2, 3 or 4 etc.")
            return

        if not tables:
            extract_table_recommendation_var.set("Example inputs: 1, 2, 3 or 4 etc.")
            return

        table_numbers = ", ".join(str(table["index"]) for table in tables)
        extract_table_recommendation_var.set(f"Example inputs: {table_numbers}")
        if not extract_table_var.get().strip():
            extract_table_var.set("1")

    def pulse_browse_button():
        nonlocal browse_pulse_index

        if browse_button is None:
            return

        if input_var.get().strip():
            browse_button.configure(style="Small.TButton")
            return

        browse_button.configure(style=browse_pulse_styles[browse_pulse_index])
        browse_pulse_index = (browse_pulse_index + 1) % len(browse_pulse_styles)
        root.after(90, pulse_browse_button)

    def update_run_pipeline_state(*args):
        if run_pipeline_button is None:
            return

        if input_var.get().strip():
            run_pipeline_button.configure(text="Run Pipeline", style="Run.TButton", state="normal")
        else:
            run_pipeline_button.configure(text="No File Selected", style="RunDisabled.TButton", state="disabled")

    input_var.trace_add("write", update_run_pipeline_state)

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

    def format_node_toggle_text(label, visible):
        symbol = "^" if visible else "v"
        cog = " ⚙" if label in tunable_nodes else ""
        return f"{label} {symbol}{cog}"

    def toggle_settings(section_frame, button, label=None):
        visible = not section_frame.winfo_ismapped()
        show_section(section_frame, visible)
        symbol = "^" if visible else "v"
        if label is None:
            button.configure(text=symbol)
        else:
            button.configure(text=format_node_toggle_text(label, visible))

    def normalize_target_key(target):
        target = str(target).strip().lower()
        if target in ("all values", "all cells", "values", "cells"):
            return "values"
        return "headers"

    def normalize_target_label(target):
        if normalize_target_key(target) == "values":
            return "all cells"
        return "column headers"

    def get_operation_summary(operation):
        name = operation["name"]
        meta = operation["meta"]

        if name in ("Normalize", "Normalize Columns"):
            return normalize_target_label(meta.get("normalize_target", "headers"))
        if name == "Extract Table":
            return f"table {meta.get('extract_table', '1')}"
        if name == "Replace Values":
            return f"{len(meta.get('replace_map', {}))} pairs"
        if name == "Coerce Data Types":
            return f"{meta.get('outlier_action', 'highlight')} outliers"
        if name == "Filter":
            values = meta.get("filter_values", [])
            match_by = "index" if meta.get("filter_match_by", "values") == "index" else "values"
            return f"{meta.get('filter_mode', 'include')} {meta.get('filter_target', 'rows')} by {match_by}: {len(values)}"
        if name == "Generate Column":
            sources = ", ".join(meta.get("source_columns", []))
            return f"{meta.get('new_column', '')} = {sources}"
        if name == "Validate Required Columns":
            return f"{len(meta.get('validate_columns', []))} required"
        return ""

    def get_operation_config_lines(operation):
        name = operation["name"]
        meta = operation["meta"]

        if name in ("Normalize", "Normalize Columns"):
            return [f"target: {normalize_target_label(meta.get('normalize_target', 'headers'))}"]
        if name == "Extract Table":
            return [f"table: {meta.get('extract_table', '1')}"]
        if name == "Replace Values":
            return [f"{old} -> {new}" for old, new in meta.get("replace_map", {}).items()]
        if name == "Coerce Data Types":
            return [f"outliers: {meta.get('outlier_action', 'highlight')}"]
        if name == "Filter":
            values = meta.get("filter_values", [])
            return [
                f"target: {meta.get('filter_target', 'rows')}",
                f"mode: {meta.get('filter_mode', 'include')}",
                f"match by: {meta.get('filter_match_by', 'values')}",
                f"logic: {meta.get('filter_match_mode', 'or')}",
                f"values: {', '.join(values)}",
            ]
        if name == "Generate Column":
            return [
                f"new column: {meta.get('new_column', '')}",
                f"operator: {meta.get('operator', '')}",
                f"sources: {', '.join(meta.get('source_columns', []))}",
            ]
        if name == "Validate Required Columns":
            return [f"required: {', '.join(meta.get('validate_columns', []))}"]
        return []

    def is_configurable_operation(name):
        return name in (
            "Extract Table",
            "Normalize",
            "Normalize Columns",
            "Replace Values",
            "Coerce Data Types",
            "Filter",
            "Generate Column",
            "Validate Required Columns",
        )

    def split_entry_list(raw):
        return [part.strip() for part in raw.split(",") if part.strip()]

    def save_order_item_meta(index, meta):
        nonlocal customizing_order_index

        if index < 0 or index >= len(operation_order):
            return

        operation_order[index]["meta"] = meta
        customizing_order_index = None
        refresh_order_rows()

    def cancel_order_customize():
        nonlocal customizing_order_index

        customizing_order_index = None
        refresh_order_rows()

    def flash_widget_red(widget, flashes=3):
        original_style = None
        try:
            default_bg = widget.cget("background")
        except tk.TclError:
            default_bg = "white"
        try:
            original_style = widget.cget("style")
        except tk.TclError:
            original_style = None

        def apply_flash(step=0):
            if not widget.winfo_exists():
                return
            is_red = step % 2 == 0
            if widget.winfo_class() == "TEntry":
                try:
                    widget.configure(style="Flash.TEntry" if is_red else original_style)
                except tk.TclError:
                    return
            else:
                try:
                    widget.configure(background="#FFB6B6" if is_red else default_bg)
                except tk.TclError:
                    return
            if step < flashes * 2 - 1:
                widget.after(130, lambda: apply_flash(step + 1))

        apply_flash()

    def flash_row_widgets(rows, *keys):
        flashed = False
        for row_data in rows:
            for key in keys:
                widget = row_data.get(key)
                if widget is not None:
                    flash_widget_red(widget)
                    flashed = True
        return flashed

    def flash_missing_inputs(name):
        set_settings_visible(name, True)

        if name == "Extract Table":
            if extract_table_entry is not None:
                flash_widget_red(extract_table_entry)
                return True
            return False
        if name == "Replace Values":
            return flash_row_widgets(replace_rows, "from_entry", "to_entry")
        if name == "Coerce Data Types":
            return False
        if name == "Filter":
            return flash_row_widgets(filter_rows, "entry")
        if name == "Generate Column":
            flash_widget_red(generate_column_name_entry)
            flash_row_widgets(generate_rows, "entry")
            return True
        if name == "Validate Required Columns":
            return flash_row_widgets(validate_rows, "entry")

        return False

    def render_order_editor(row_frame, row_index, operation):
        name = operation["name"]
        meta = operation["meta"]

        editor = ttk.Frame(row_frame, style="StormPanel.TFrame")
        editor.grid(row=1, column=0, columnspan=5, sticky="ew", padx=(18, 0), pady=(4, 0))
        editor.grid_columnconfigure(1, weight=1, uniform="replace_editor")
        editor.grid_columnconfigure(3, weight=1, uniform="replace_editor")

        if name in ("Normalize", "Normalize Columns"):
            target_var = tk.StringVar(value=normalize_target_label(meta.get("normalize_target", "headers")))
            ttk.Label(editor, text="target", style="Storm.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=1)
            ttk.Combobox(
                editor,
                textvariable=target_var,
                values=("column headers", "all cells"),
                state="readonly",
                width=15
            ).grid(row=0, column=1, sticky="w", pady=1)

            def save_normalize():
                save_order_item_meta(row_index, {"normalize_target": normalize_target_key(target_var.get())})

            return save_normalize

        if name == "Extract Table":
            table_var = tk.StringVar(value=str(meta.get("extract_table", "1")))
            ttk.Label(editor, text="table", style="Storm.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=1)
            ttk.Entry(editor, textvariable=table_var, width=10).grid(row=0, column=1, sticky="w", pady=1)

            def save_extract_table():
                table = table_var.get().strip()
                if not table:
                    messagebox.showerror("Missing Extract Table Config", "Extract Table needs a table number.")
                    return
                save_order_item_meta(row_index, {"extract_table": table})

            return save_extract_table

        if name == "Replace Values":
            replace_vars = []
            replace_map = meta.get("replace_map", {})
            for pair_index, (old_value, new_value) in enumerate(replace_map.items()):
                old_var = tk.StringVar(value=str(old_value))
                new_var = tk.StringVar(value=str(new_value))
                replace_vars.append((old_var, new_var))

                ttk.Label(editor, text="val", style="Storm.TLabel").grid(row=pair_index, column=0, sticky="w", padx=(0, 4), pady=1)
                ttk.Entry(editor, textvariable=old_var, width=13).grid(row=pair_index, column=1, sticky="ew", padx=(0, 6), pady=1)
                ttk.Label(editor, text="replacement", style="Storm.TLabel").grid(row=pair_index, column=2, sticky="w", padx=(0, 4), pady=1)
                ttk.Entry(editor, textvariable=new_var, width=13).grid(row=pair_index, column=3, sticky="ew", pady=1)

            def save_replace_values():
                replace_map = {}
                for old_var, new_var in replace_vars:
                    old_raw = old_var.get().strip()
                    if old_raw == "":
                        continue
                    replace_map[parse_literal_value(old_raw)] = parse_literal_value(new_var.get())

                if not replace_map:
                    messagebox.showerror("Missing Replace Values Config", "Replace Values needs at least one old value.")
                    return

                save_order_item_meta(row_index, {"replace_map": replace_map})

            return save_replace_values

        if name == "Coerce Data Types":
            action_var = tk.StringVar(value=meta.get("outlier_action", "highlight"))
            ttk.Label(editor, text="outliers", style="Storm.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=1)
            ttk.Combobox(
                editor,
                textvariable=action_var,
                values=("highlight", "delete"),
                state="readonly",
                width=10
            ).grid(row=0, column=1, sticky="w", pady=1)

            def save_type_consistency():
                action = action_var.get().strip().lower()
                if action not in ("highlight", "delete"):
                    action = "highlight"
                save_order_item_meta(row_index, {"outlier_action": action})

            return save_type_consistency

        if name == "Filter":
            target_var = tk.StringVar(value=meta.get("filter_target", "rows"))
            mode_var = tk.StringVar(value=meta.get("filter_mode", "include"))
            match_var = tk.StringVar(value=meta.get("filter_match_mode", "or"))
            match_by_var = tk.StringVar(value=meta.get("filter_match_by", "values"))
            values_var = tk.StringVar(value=", ".join(meta.get("filter_values", [])))

            ttk.Label(editor, text="target", style="Storm.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=1)
            ttk.Combobox(editor, textvariable=target_var, values=("rows", "columns"), state="readonly", width=10).grid(row=0, column=1, sticky="w", pady=1)
            ttk.Label(editor, text="mode", style="Storm.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=1)
            ttk.Combobox(editor, textvariable=mode_var, values=("include", "exclude"), state="readonly", width=10).grid(row=1, column=1, sticky="w", pady=1)
            ttk.Label(editor, text="match", style="Storm.TLabel").grid(row=2, column=0, sticky="w", padx=(0, 6), pady=1)
            ttk.Combobox(editor, textvariable=match_by_var, values=("values", "index"), state="readonly", width=10).grid(row=2, column=1, sticky="w", pady=1)
            ttk.Label(editor, text="logic", style="Storm.TLabel").grid(row=3, column=0, sticky="w", padx=(0, 6), pady=1)
            ttk.Combobox(editor, textvariable=match_var, values=("or", "and"), state="readonly", width=10).grid(row=3, column=1, sticky="w", pady=1)
            ttk.Label(editor, text="values/indexes", style="Storm.TLabel").grid(row=4, column=0, sticky="w", padx=(0, 6), pady=1)
            ttk.Entry(editor, textvariable=values_var, width=28).grid(row=4, column=1, columnspan=3, sticky="ew", pady=1)

            def save_filter():
                values = split_entry_list(values_var.get())
                if not values:
                    messagebox.showerror("Missing Filter Config", "Filter needs at least one value.")
                    return

                target = target_var.get().strip().lower()
                if target not in ("rows", "columns"):
                    target = "rows"
                mode = mode_var.get().strip().lower()
                if mode not in ("include", "exclude"):
                    mode = "include"
                match_by = match_by_var.get().strip().lower()
                if match_by not in ("values", "index"):
                    match_by = "values"
                match_mode = match_var.get().strip().lower()
                if match_mode not in ("and", "or"):
                    match_mode = "or"

                save_order_item_meta(
                    row_index,
                    {
                        "filter_target": target,
                        "filter_mode": mode,
                        "filter_match_by": match_by,
                        "filter_match_mode": match_mode,
                        "filter_values": values,
                    }
                )

            return save_filter

        if name == "Generate Column":
            new_column_var = tk.StringVar(value=meta.get("new_column", ""))
            operator_var = tk.StringVar(value=meta.get("operator", "+"))
            sources_var = tk.StringVar(value=", ".join(meta.get("source_columns", [])))

            ttk.Label(editor, text="new column", style="Storm.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=1)
            ttk.Entry(editor, textvariable=new_column_var, width=20).grid(row=0, column=1, sticky="ew", pady=1)
            ttk.Label(editor, text="operator", style="Storm.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=1)
            ttk.Combobox(editor, textvariable=operator_var, values=("+", "-", "*", "/"), state="readonly", width=6).grid(row=1, column=1, sticky="w", pady=1)
            ttk.Label(editor, text="sources", style="Storm.TLabel").grid(row=2, column=0, sticky="w", padx=(0, 6), pady=1)
            ttk.Entry(editor, textvariable=sources_var, width=28).grid(row=2, column=1, columnspan=3, sticky="ew", pady=1)

            def save_generate_column():
                new_column = new_column_var.get().strip()
                source_columns = split_entry_list(sources_var.get())
                operator = operator_var.get().strip()

                if not new_column:
                    messagebox.showerror("Missing Generate Column Config", "Generate Column needs a new column name.")
                    return
                if len(source_columns) < 2:
                    messagebox.showerror("Missing Generate Column Config", "Generate Column needs at least two source columns.")
                    return

                save_order_item_meta(
                    row_index,
                    {"new_column": new_column, "operator": operator, "source_columns": source_columns}
                )

            return save_generate_column

        if name == "Validate Required Columns":
            columns_var = tk.StringVar(value=", ".join(meta.get("validate_columns", [])))

            ttk.Label(editor, text="required", style="Storm.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=1)
            ttk.Entry(editor, textvariable=columns_var, width=28).grid(row=0, column=1, columnspan=3, sticky="ew", pady=1)

            def save_validate_columns():
                columns = split_entry_list(columns_var.get())
                if not columns:
                    messagebox.showerror("Missing Validate Config", "Validate Required Columns needs at least one column.")
                    return

                save_order_item_meta(row_index, {"validate_columns": columns})

            return save_validate_columns

        return None

    def update_order_empty_border():
        nonlocal order_pulse_job, order_pulse_index

        if order_section_box is None:
            return

        if operation_order:
            if order_pulse_job is not None:
                try:
                    root.after_cancel(order_pulse_job)
                except Exception:
                    pass
                order_pulse_job = None
            order_section_box.configure(style="Storm.TLabelframe")
            return

        if not order_section_box.winfo_exists():
            order_pulse_job = None
            return

        order_section_box.configure(style=order_pulse_styles[order_pulse_index])
        order_pulse_index = (order_pulse_index + 1) % len(order_pulse_styles)
        order_pulse_job = root.after(90, update_order_empty_border)

    def refresh_order_rows():
        for child in order_rows_frame.winfo_children():
            child.destroy()

        if not operation_order:
            ttk.Label(
                order_rows_frame,
                text="No nodes added.",
                style="Storm.TLabel"
            ).grid(row=0, column=0, sticky="w")
            if order_pulse_job is None:
                update_order_empty_border()
            return

        update_order_empty_border()

        for row_index, operation in enumerate(operation_order):
            row_frame = ttk.Frame(order_rows_frame, style="StormPanel.TFrame")
            row_frame.grid(row=row_index, column=0, sticky="ew", pady=2)
            row_frame.grid_columnconfigure(0, weight=1)

            summary = get_operation_summary(operation)
            text = f"{row_index + 1}. {operation['name']}"
            if summary:
                text = f"{text} - {summary}"

            title_label = ttk.Label(
                row_frame,
                text=text,
                style="CustomStorm.TLabel" if operation["name"] in custom_node_names else "Storm.TLabel"
            )
            title_label.grid(row=0, column=0, sticky="w", padx=(0, 6))

            is_customizing = row_index == customizing_order_index
            save_command = None
            if is_customizing:
                save_command = render_order_editor(row_frame, row_index, operation)

            config_lines = get_operation_config_lines(operation)
            if config_lines and not is_customizing:
                config_text = "\n".join(f"  {line}" for line in config_lines)
                ttk.Label(
                    row_frame,
                    text=config_text,
                    style="CustomStorm.TLabel" if operation["name"] in custom_node_names else "Storm.TLabel",
                    justify="left",
                    wraplength=260
                ).grid(row=1, column=0, sticky="w", padx=(18, 6), pady=(2, 0))

            control_col = 1
            if is_configurable_operation(operation["name"]):
                if is_customizing:
                    ttk.Button(
                        row_frame,
                        text="Save",
                        style="Save.TButton",
                        command=save_command
                    ).grid(row=0, column=control_col, padx=(0, 4))
                    control_col += 1
                    ttk.Button(
                        row_frame,
                        text="Cancel",
                        style="Danger.TButton",
                        command=cancel_order_customize
                    ).grid(row=0, column=control_col, padx=(0, 4))
                    control_col += 1
                else:
                    ttk.Button(
                        row_frame,
                        text="Customize",
                        style="Small.TButton",
                        command=lambda idx=row_index: customize_order_item(idx)
                    ).grid(row=0, column=control_col, padx=(0, 4))
                    control_col += 1

            ttk.Button(
                row_frame,
                text="^",
                width=3,
                style="Small.TButton",
                command=lambda idx=row_index: move_order_item(idx, -1)
            ).grid(row=0, column=control_col, padx=(0, 4))
            control_col += 1

            ttk.Button(
                row_frame,
                text="v",
                width=6,
                style="Small.TButton",
                command=lambda idx=row_index: move_order_item(idx, 1)
            ).grid(row=0, column=control_col, padx=(0, 4))
            control_col += 1

            ttk.Button(
                row_frame,
                text="X",
                width=3,
                style="Danger.TButton",
                command=lambda idx=row_index: delete_order_item(idx)
            ).grid(row=0, column=control_col)

    def move_order_item(index, direction):
        nonlocal customizing_order_index

        new_index = index + direction
        if new_index < 0 or new_index >= len(operation_order):
            return

        operation_order[index], operation_order[new_index] = operation_order[new_index], operation_order[index]
        if customizing_order_index == index:
            customizing_order_index = new_index
        elif customizing_order_index == new_index:
            customizing_order_index = index
        refresh_order_rows()

    def delete_order_item(index):
        nonlocal customizing_order_index

        if 0 <= index < len(operation_order):
            del operation_order[index]
            if customizing_order_index == index:
                customizing_order_index = None
            elif customizing_order_index is not None and customizing_order_index > index:
                customizing_order_index -= 1
            refresh_order_rows()

    def add_order_item(name):
        try:
            operation_order.append(build_operation_snapshot(name))
            refresh_order_rows()
            if name in tunable_nodes:
                reset_tuneables(name)
        except ValueError as error:
            set_settings_visible(name, True)
            root.update_idletasks()
            flash_missing_inputs(name)

    def set_settings_visible(name, visible):
        mapping = {
            "Extract Table": (lambda: extract_table_settings, lambda: extract_table_toggle),
            "Normalize": (lambda: normalize_info, lambda: normalize_toggle),
            "Normalize Columns": (lambda: normalize_info, lambda: normalize_toggle),
            "Replace Values": (lambda: replace_settings, lambda: replace_toggle),
            "Coerce Data Types": (lambda: type_settings, lambda: type_toggle),
            "Drop Duplicates": (lambda: dropdup_info, lambda: dropdup_toggle),
            "Filter": (lambda: filter_settings, lambda: filter_toggle),
            "Generate Column": (lambda: generate_settings, lambda: generate_toggle),
            "Validate Required Columns": (lambda: validate_settings, lambda: validate_toggle),
        }

        if name not in mapping:
            return

        section_getter, button_getter = mapping[name]
        show_section(section_getter(), visible)
        button_getter().configure(text=format_node_toggle_text(name, visible))

    def clear_dynamic_rows(rows, refresh_callback):
        rows.clear()
        refresh_callback()

    def row_values(rows, key="value_var"):
        return [row_data[key].get().strip() for row_data in rows]

    def tuneables_are_default(name):
        if name == "Extract Table":
            return extract_table_var.get().strip() == "1"
        if name in ("Normalize", "Normalize Columns"):
            return normalize_target_key(normalize_target_var.get()) == "values"
        if name == "Replace Values":
            return len(replace_rows) == 1 and replace_rows[0]["from_var"].get().strip() == "" and replace_rows[0]["to_var"].get().strip() == ""
        if name == "Coerce Data Types":
            return type_outlier_action_var.get() == "highlight"
        if name == "Filter":
            return (
                filter_target_var.get() == "rows"
                and filter_mode_var.get() == "include"
                and filter_match_mode_var.get() == "or"
                and filter_match_by_var.get() == "values"
                and len(filter_rows) == 1
                and row_values(filter_rows) == [""]
            )
        if name == "Generate Column":
            return (
                generate_column_name_var.get().strip() == ""
                and generate_operator_var.get() == "+"
                and len(generate_rows) == 2
                and row_values(generate_rows) == ["", ""]
            )
        if name == "Validate Required Columns":
            return len(validate_rows) == 1 and row_values(validate_rows) == [""]
        return True

    def pulse_tunable_add_button(name):
        if name not in tunable_add_buttons:
            return
        button = tunable_add_buttons[name]
        if not button.winfo_exists():
            return
        if tuneables_are_default(name):
            button.configure(style="Add.TButton")
            tunable_pulse_jobs.pop(name, None)
            return

        index = tunable_pulse_index.get(name, 0)
        button.configure(style=add_pulse_styles[index])
        tunable_pulse_index[name] = (index + 1) % len(add_pulse_styles)
        tunable_pulse_jobs[name] = root.after(90, lambda node_name=name: pulse_tunable_add_button(node_name))

    def refresh_tunable_add_state(name):
        if initializing_tunables or name not in tunable_nodes:
            return

        existing_job = tunable_pulse_jobs.pop(name, None)
        if existing_job is not None:
            try:
                root.after_cancel(existing_job)
            except Exception:
                pass

        if tuneables_are_default(name):
            if name in tunable_add_buttons:
                tunable_add_buttons[name].configure(style="Add.TButton")
            if name in tunable_reset_buttons:
                tunable_reset_buttons[name].grid_remove()
            return

        if name in tunable_reset_buttons:
            tunable_reset_buttons[name].grid()
        tunable_pulse_index[name] = 0
        pulse_tunable_add_button(name)

    def reset_tuneables(name):
        nonlocal initializing_tunables

        initializing_tunables = True
        try:
            if name == "Extract Table":
                extract_table_var.set("1")
            elif name in ("Normalize", "Normalize Columns"):
                normalize_target_var.set("all cells")
            elif name == "Replace Values":
                replace_rows.clear()
                add_replace_row()
            elif name == "Coerce Data Types":
                type_outlier_action_var.set("highlight")
            elif name == "Filter":
                filter_target_var.set("rows")
                filter_mode_var.set("include")
                filter_match_mode_var.set("or")
                filter_match_by_var.set("values")
                filter_rows.clear()
                add_filter_row()
                on_filter_mode_changed()
            elif name == "Generate Column":
                generate_column_name_var.set("")
                generate_operator_var.set("+")
                generate_rows.clear()
                add_generate_row()
                add_generate_row()
            elif name == "Validate Required Columns":
                validate_rows.clear()
                add_validate_row()
        finally:
            initializing_tunables = False

        refresh_tunable_add_state(name)

    def mark_tuneables_changed(name):
        refresh_tunable_add_state(name)

    extract_table_var.trace_add("write", lambda *args: mark_tuneables_changed("Extract Table"))
    normalize_target_var.trace_add("write", lambda *args: mark_tuneables_changed("Normalize"))
    type_outlier_action_var.trace_add("write", lambda *args: mark_tuneables_changed("Coerce Data Types"))
    filter_target_var.trace_add("write", lambda *args: mark_tuneables_changed("Filter"))
    filter_mode_var.trace_add("write", lambda *args: mark_tuneables_changed("Filter"))
    filter_match_mode_var.trace_add("write", lambda *args: mark_tuneables_changed("Filter"))
    filter_match_by_var.trace_add("write", lambda *args: mark_tuneables_changed("Filter"))
    generate_column_name_var.trace_add("write", lambda *args: mark_tuneables_changed("Generate Column"))
    generate_operator_var.trace_add("write", lambda *args: mark_tuneables_changed("Generate Column"))

    def customize_order_item(index):
        nonlocal customizing_order_index

        if index < 0 or index >= len(operation_order):
            return

        if not is_configurable_operation(operation_order[index]["name"]):
            return

        customizing_order_index = index
        refresh_order_rows()

    def get_input_filename():
        input_path = input_var.get().strip()
        if not input_path:
            return "CSV Preview"
        return os.path.basename(input_path)

    def get_default_save_folder():
        input_path = input_var.get().strip()
        if not input_path:
            return None

        return os.path.dirname(input_path)

    def get_default_save_filename():
        input_path = input_var.get().strip()
        if not input_path:
            return "Processed_Table.csv"

        filename = os.path.basename(input_path)
        stem, ext = os.path.splitext(filename)
        if not ext:
            ext = ".csv"
        return f"Processed_{stem}{ext}"

    def get_processed_window_title():
        return "Processed Preview"

    def place_window_right_of(window, anchor_window, width, height):
        anchor_window.update_idletasks()
        window.update_idletasks()

        x = anchor_window.winfo_rootx() + anchor_window.winfo_width() + 12
        y = anchor_window.winfo_rooty()

        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        if x + width > screen_width:
            x = max(0, screen_width - width - 20)
            y = anchor_window.winfo_rooty() + anchor_window.winfo_height() + 32
        if y + height > screen_height:
            y = max(0, screen_height - height - 60)

        window.geometry(f"{width}x{height}+{x}+{y}")

    def create_canvas_table(parent, selected_value_var=None, selected_entry_getter=None):
        outer = ttk.Frame(parent, style="Storm.TFrame")
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(
            outer,
            bg="white",
            highlightthickness=0,
            bd=0
        )
        canvas.grid(row=0, column=0, sticky="nsew")

        yscroll = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=yscroll.set)

        xscroll = ttk.Scrollbar(outer, orient="horizontal", command=canvas.xview)
        xscroll.grid(row=1, column=0, sticky="ew")
        canvas.configure(xscrollcommand=xscroll.set)

        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        inner = tk.Frame(canvas, bg="white")
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        table_state = {
            "outer": outer,
            "canvas": canvas,
            "inner": inner,
            "window_id": window_id,
            "tooltip": None,
            "last_render": None,
            "last_canvas_width": 0,
            "resize_job": None,
            "table_width_px": 0,
            "column_count": 0,
        }

        def on_inner_configure(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event):
            table_width = max(1, table_state.get("table_width_px", 0))
            canvas.itemconfigure(window_id, width=table_width)

            last_render = table_state.get("last_render")
            last_width = table_state.get("last_canvas_width", 0)
            if last_render is None or abs(event.width - last_width) < 24:
                return

            if table_state["resize_job"] is not None:
                canvas.after_cancel(table_state["resize_job"])

            def rerender_after_resize():
                table_state["resize_job"] = None
                render_canvas_table(table_state, *last_render)

            table_state["resize_job"] = canvas.after(80, rerender_after_resize)

        inner.bind("<Configure>", on_inner_configure)
        canvas.bind("<Configure>", on_canvas_configure)

        return table_state

    def render_canvas_table(table_state, df, cell_colors=None, hover_old_values=None):
        inner = table_state["inner"]
        canvas = table_state["canvas"]
        table_state["last_render"] = (df, cell_colors, hover_old_values)

        for child in inner.winfo_children():
            child.destroy()

        previous_column_count = table_state.get("column_count", 0)
        for col_index in range(previous_column_count):
            inner.grid_columnconfigure(col_index, weight=0, minsize=0)

        if table_state["tooltip"] is not None:
            try:
                table_state["tooltip"].destroy()
            except Exception:
                pass
            table_state["tooltip"] = None

        if df is None or df.empty:
            tk.Label(
                inner,
                text="No rows to display.",
                bg="white",
                fg="black",
                anchor="w",
                padx=6,
                pady=4,
            ).grid(row=0, column=0, sticky="w")
            canvas.configure(scrollregion=canvas.bbox("all"))
            return

        display_df = df.copy()

        for column_name in display_df.columns:
            display_df[column_name] = display_df[column_name].map(
                lambda v: "" if v is None else str(v)
            )

        columns = list(display_df.columns)
        table_state["column_count"] = len(columns) + 1

        canvas.update_idletasks()
        available_width = canvas.winfo_width()
        if available_width <= 1:
            available_width = canvas.winfo_reqwidth()
        if available_width <= 1:
            available_width = 900

        min_column_width_px = 90
        char_width_px = 8
        usable_width_px = max(1, available_width - 4)
        max_column_width_px = max(min_column_width_px, int(usable_width_px / 5))

        column_widths_px = {}
        for column_name in columns:
            values = [str(column_name)]
            values.extend(display_df[column_name].astype(str).tolist())

            lengths = [max((len(part) for part in value.splitlines()), default=0) for value in values]
            longest_length = max(lengths, default=1)
            average_length = sum(lengths) / max(1, len(lengths))
            desired_length = min(longest_length, max(average_length * 1.1, len(str(column_name))))

            desired_width_px = int(desired_length * char_width_px) + 24
            column_widths_px[column_name] = max(
                min_column_width_px,
                min(max_column_width_px, desired_width_px)
            )

        index_column_width_px = 46
        table_width_px = max(1, index_column_width_px + sum(column_widths_px.values()))
        table_state["last_canvas_width"] = available_width
        table_state["table_width_px"] = table_width_px
        canvas.itemconfigure(table_state["window_id"], width=table_width_px)

        index_bg = "#e9f1ff"
        index_border = "#2f64c8"
        header_bg = "#d7e3f0"
        default_bg = "white"
        added_bg = "#d9f5d9"
        modified_bg = "#ffe7c2"
        deleted_bg = "#ffd6d6"
        
        def hide_tooltip():
            if table_state["tooltip"] is not None:
                try:
                    table_state["tooltip"].destroy()
                except Exception:
                    pass
                table_state["tooltip"] = None

        def show_tooltip(widget, text):
            hide_tooltip()

            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.configure(bg="#fff4d6")

            label = tk.Label(
                tooltip,
                text=text,
                bg="#fff4d6",
                fg="black",
                relief="solid",
                bd=1,
                padx=6,
                pady=4,
                justify="left",
                wraplength=320,
            )
            label.pack()

            x = widget.winfo_rootx() + 16
            y = widget.winfo_rooty() + 24
            tooltip.wm_geometry(f"+{x}+{y}")

            table_state["tooltip"] = tooltip

        def make_read_only_text(widget):
            def block_edit_keys(event):
                ctrl_pressed = bool(event.state & 0x4)
                if ctrl_pressed and event.keysym.lower() in ("c", "a"):
                    return None
                if event.keysym in ("Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next"):
                    return None
                return "break"

            def select_all(event):
                widget.tag_add("sel", "1.0", "end-1c")
                return "break"

            widget.bind("<Key>", block_edit_keys)
            widget.bind("<Control-a>", select_all)
            widget.bind("<Control-A>", select_all)
            widget.bind("<<Paste>>", lambda event: "break")
            widget.bind("<<Cut>>", lambda event: "break")
            widget.bind("<Button-2>", lambda event: "break")

        def estimate_text_height(value):
            text = str(value)
            chars_per_line = max(8, int(current_column_width_px / char_width_px))
            line_count = 0
            for line in text.splitlines() or [""]:
                line_count += max(1, int((len(line) + chars_per_line - 1) / chars_per_line))
            return max(1, min(5, line_count))

        def is_auto_numbered_columns(column_names):
            expected = list(range(1, len(column_names) + 1))
            return list(column_names) == expected or [str(column) for column in column_names] == [str(column) for column in expected]

        show_dataframe_headers = not is_auto_numbered_columns(columns)
        first_data_grid_row = 2 if show_dataframe_headers else 1

        corner = tk.Label(
            inner,
            text="#",
            bg=index_bg,
            fg="#163a7a",
            relief="solid",
            bd=1,
            highlightbackground=index_border,
            highlightcolor=index_border,
            highlightthickness=1,
            padx=6,
            pady=4,
            font=("Arial", 9, "bold"),
        )
        corner.grid(row=0, column=0, rowspan=first_data_grid_row, sticky="nsew")
        inner.grid_columnconfigure(0, weight=0, minsize=index_column_width_px)

        for col_index, column_name in enumerate(columns):
            indexed_col = col_index + 1
            current_column_width_px = column_widths_px[column_name]
            column_index = tk.Label(
                inner,
                text=str(indexed_col),
                bg=index_bg,
                fg="#163a7a",
                relief="solid",
                bd=1,
                highlightbackground=index_border,
                highlightcolor=index_border,
                highlightthickness=1,
                padx=6,
                pady=3,
                font=("Arial", 9, "bold"),
            )
            column_index.grid(row=0, column=indexed_col, sticky="nsew")

            inner.grid_columnconfigure(indexed_col, weight=0, minsize=current_column_width_px)

            if show_dataframe_headers:
                header_color = header_bg
                if cell_colors is not None and (-1, column_name) in cell_colors:
                    if cell_colors[(-1, column_name)] == "added":
                        header_color = added_bg
                    elif cell_colors[(-1, column_name)] == "modified":
                        header_color = modified_bg
                    elif cell_colors[(-1, column_name)] == "deleted":
                        header_color = deleted_bg

                header = tk.Text(
                    inner,
                    bg=header_color,
                    fg="black",
                    relief="solid",
                    bd=1,
                    padx=6,
                    pady=4,
                    font=("Arial", 9, "bold"),
                    width=1,
                    height=1,
                    wrap="word",
                    cursor="xterm",
                    takefocus=True,
                )
                header.insert("1.0", str(column_name))
                make_read_only_text(header)
                header.grid(row=1, column=indexed_col, sticky="nsew")

                if hover_old_values is not None and (-1, column_name) in hover_old_values:
                    old_value = hover_old_values[(-1, column_name)]
                    tip_text = f"Previous header: {old_value}"
                    header.bind("<Enter>", lambda event, widget=header, text=tip_text: show_tooltip(widget, text))
                    header.bind("<Leave>", lambda event: hide_tooltip())

        for row_index, (_, row) in enumerate(display_df.iterrows(), start=1):
            table_row = row_index + first_data_grid_row - 1
            row_index_label = tk.Label(
                inner,
                text=str(row_index),
                bg=index_bg,
                fg="#163a7a",
                relief="solid",
                bd=1,
                highlightbackground=index_border,
                highlightcolor=index_border,
                highlightthickness=1,
                padx=6,
                pady=4,
                font=("Arial", 9, "bold"),
            )
            row_index_label.grid(row=table_row, column=0, sticky="nsew")

            for col_index, column_name in enumerate(columns):
                current_column_width_px = column_widths_px[column_name]
                cell_value = row[column_name]
                bg = default_bg

                if cell_colors is not None:
                    color_key = (row_index - 1, column_name)
                    if color_key in cell_colors:
                        if cell_colors[color_key] == "added":
                            bg = added_bg
                        elif cell_colors[color_key] == "modified":
                            bg = modified_bg
                        elif cell_colors[color_key] == "deleted":
                            bg = deleted_bg
                        elif cell_colors[color_key] == "outlier":
                            bg = "#e3d4ff"

                line_count = estimate_text_height(cell_value)
                cell = tk.Text(
                    inner,
                    bg=bg,
                    fg="black",
                    relief="solid",
                    bd=1,
                    padx=6,
                    pady=4,
                    width=1,
                    height=line_count,
                    wrap="word",
                    cursor="xterm",
                    takefocus=True,
                )
                cell.insert("1.0", cell_value)
                make_read_only_text(cell)
                cell.grid(row=table_row, column=col_index + 1, sticky="nsew")

                hover_key = (row_index - 1, column_name)
                if hover_old_values is not None and hover_key in hover_old_values:
                    old_value = hover_old_values[hover_key]
                    tip_text = f"Previous value: {old_value}"
                    cell.bind("<Enter>", lambda event, widget=cell, text=tip_text: show_tooltip(widget, text))
                    cell.bind("<Leave>", lambda event: hide_tooltip())

        canvas.configure(scrollregion=canvas.bbox("all"))

    def ensure_preview_window():
        nonlocal preview_window, preview_table_state

        if preview_window is not None and preview_window.winfo_exists():
            preview_window.title(get_input_filename())
            preview_window.lift()
            return

        preview_window = tk.Toplevel(root)
        preview_window.title(get_input_filename())
        place_window_right_of(preview_window, root, 900, 560)
        preview_window.configure(bg=storm_blue)

        preview_frame = ttk.Frame(preview_window, padding=10, style="Storm.TFrame")
        preview_frame.pack(fill="both", expand=True)

        ttk.Label(
            preview_frame,
            textvariable=preview_info_var,
            style="StormTop.TLabel"
        ).pack(anchor="w", pady=(0, 4))

        table_holder = ttk.Frame(preview_frame, style="Storm.TFrame")
        table_holder.pack(fill="both", expand=True)

        preview_table_state = create_canvas_table(table_holder)

    def save_processed_output():
        if not processed_steps:
            return

        initial_dir = get_default_save_folder()
        save_options = {
            "parent": processed_window if processed_window is not None and processed_window.winfo_exists() else root,
            "title": "Save processed CSV",
            "initialfile": get_default_save_filename(),
            "defaultextension": ".csv",
            "filetypes": [("CSV files", "*.csv"), ("All files", "*.*")],
        }
        if initial_dir:
            save_options["initialdir"] = initial_dir

        save_path = filedialog.asksaveasfilename(**save_options)
        if not save_path:
            return

        try:
            output_data = processed_steps[-1]["data"]
            expected_columns = list(range(1, len(output_data.columns) + 1))
            has_auto_columns = (
                list(output_data.columns) == expected_columns
                or [str(column) for column in output_data.columns] == [str(column) for column in expected_columns]
            )
            output_data.to_csv(save_path, index=False, header=not has_auto_columns)
            if processed_window is not None and processed_window.winfo_exists():
                processed_window.title(os.path.basename(save_path))
        except Exception as error:
            messagebox.showerror("Save Error", str(error))

    def ensure_processed_window():
        nonlocal processed_window, processed_table_state, processed_play_button, processed_title_label

        if processed_window is not None and processed_window.winfo_exists():
            processed_window.title(get_processed_window_title())
            processed_window.lift()
            return

        if preview_window is None or not preview_window.winfo_exists():
            ensure_preview_window()

        processed_window = tk.Toplevel(root)
        processed_window.title(get_processed_window_title())
        anchor_window = preview_window if preview_window is not None and preview_window.winfo_exists() else root
        place_window_right_of(processed_window, anchor_window, 1050, 700)
        processed_window.configure(bg=storm_blue)

        processed_frame = ttk.Frame(processed_window, padding=10, style="Storm.TFrame")
        processed_frame.pack(fill="both", expand=True)

        processed_title_label = ttk.Label(
            processed_frame,
            textvariable=processed_title_var,
            style="ProcessedTitle.TLabel"
        )
        processed_title_label.pack(anchor="w", pady=(0, 6))

        ttk.Label(
            processed_frame,
            textvariable=processed_diag_var,
            style="StormTop.TLabel",
            justify="left",
            wraplength=980
        ).pack(anchor="w", pady=(0, 6))

        legend_frame = ttk.Frame(processed_frame, style="Storm.TFrame")
        legend_frame.pack(fill="x", pady=(0, 8))

        def add_legend_item(color, label):
            swatch = tk.Label(
                legend_frame,
                bg=color,
                width=2,
                height=1,
                relief="solid",
                bd=1,
            )
            swatch.pack(side="left", padx=(0, 4))
            ttk.Label(
                legend_frame,
                text=label,
                style="StormTop.TLabel"
            ).pack(side="left", padx=(0, 14))

        add_legend_item("#d9f5d9", "added")
        add_legend_item("#ffe7c2", "modified")
        add_legend_item("#ffd6d6", "deleted")
        add_legend_item("#e3d4ff", "outlier")

        controls_frame = ttk.Frame(processed_frame, style="Storm.TFrame")
        controls_frame.pack(fill="x", pady=(0, 8))

        ttk.Button(
            controls_frame,
            text="\u2190",
            width=3,
            style="Small.TButton",
            command=show_previous_processed_step
        ).pack(side="left", padx=(0, 6))

        processed_play_button = ttk.Button(
            controls_frame,
            text="\u23f8" if processed_is_playing else "\u25b6",
            width=3,
            style="Small.TButton",
            command=toggle_processed_playback
        )
        processed_play_button.pack(side="left", padx=(0, 6))

        ttk.Button(
            controls_frame,
            text="\u2192",
            width=3,
            style="Small.TButton",
            command=show_next_processed_step
        ).pack(side="left", padx=(0, 6))

        ttk.Button(
            controls_frame,
            text="💾",
            width=3,
            style="Small.TButton",
            command=save_processed_output
        ).pack(side="left", padx=(8, 6))

        table_holder = ttk.Frame(processed_frame, style="Storm.TFrame")
        table_holder.pack(fill="both", expand=True)

        processed_table_state = create_canvas_table(table_holder)

    def build_raw_preview_dataframe():
        import pandas as pd

        input_path = input_var.get().strip()
        if not input_path:
            return None

        return ReadCsvRows(input_path).head(50)

    def build_operation_snapshot(name):
        if name in custom_node_specs:
            return {
                "name": name,
                "meta": {
                    "custom_node": True,
                },
            }

        if name in ("Normalize", "Normalize Columns"):
            target = normalize_target_key(normalize_target_var.get())
            return {
                "name": "Normalize",
                "meta": {
                    "normalize_target": target,
                },
            }

        if name == "Extract Table":
            table = extract_table_var.get().strip()
            if not table:
                raise ValueError("Extract Table needs a table number before it can be added.")
            return {
                "name": name,
                "meta": {
                    "extract_table": table,
                },
            }

        if name == "Replace Values":
            replace_map = build_replace_map()
            if not replace_map:
                raise ValueError("Replace Values needs at least one replace pair before it can be added.")
            return {
                "name": name,
                "meta": {
                    "replace_map": dict(replace_map),
                },
            }

        if name == "Coerce Data Types":
            action = type_outlier_action_var.get().strip().lower()
            if action not in ("highlight", "delete"):
                action = "highlight"
            return {
                "name": name,
                "meta": {
                    "outlier_action": action,
                },
            }

        if name == "Drop Duplicates":
            return {
                "name": name,
                "meta": {},
            }

        if name == "Filter":
            filter_values = build_filter_columns()
            if not filter_values:
                raise ValueError("Filter needs at least one value before it can be added.")

            target = filter_target_var.get().strip().lower()
            if target not in ("rows", "columns"):
                target = "rows"
            mode = filter_mode_var.get().strip().lower()
            if mode not in ("include", "exclude"):
                mode = "include"
            match_by = filter_match_by_var.get().strip().lower()
            if match_by not in ("values", "index"):
                match_by = "values"
            match_mode = filter_match_mode_var.get().strip().lower()
            if match_mode not in ("and", "or"):
                match_mode = "or"

            return {
                "name": name,
                "meta": {
                    "filter_target": target,
                    "filter_mode": mode,
                    "filter_match_by": match_by,
                    "filter_match_mode": match_mode,
                    "filter_values": list(filter_values),
                },
            }

        if name == "Generate Column":
            new_column = generate_column_name_var.get().strip()
            operator = generate_operator_var.get().strip()
            source_columns = build_generate_columns()

            if not new_column:
                raise ValueError("Generate Column needs a new column name before it can be added.")
            if len(source_columns) < 2:
                raise ValueError("Generate Column needs at least two source columns before it can be added.")

            return {
                "name": name,
                "meta": {
                    "new_column": new_column,
                    "operator": operator,
                    "source_columns": list(source_columns),
                },
            }

        if name == "Validate Required Columns":
            validate_cols = build_validate_columns()
            if not validate_cols:
                raise ValueError("Validate Required Columns needs at least one column before it can be added.")

            return {
                "name": name,
                "meta": {
                    "validate_columns": list(validate_cols),
                },
            }

        raise ValueError(f"Unknown node: {name}")

    def build_node_from_operation(operation):
        name = operation["name"]
        meta = operation["meta"]

        if name in custom_node_specs:
            node = create_custom_node(custom_node_specs[name])
        elif name == "Extract Table":
            node = ExtractTableNode(Table=meta.get("extract_table", "1"))
        elif name in ("Normalize", "Normalize Columns"):
            node = NormalizeColumnsNode(Target=meta.get("normalize_target", "headers"))
        elif name == "Replace Values":
            node = ReplaceValuesNode(meta["replace_map"])
        elif name == "Coerce Data Types":
            node = TypeConsistencyNode(OutlierAction=meta.get("outlier_action", "highlight"))
        elif name == "Drop Duplicates":
            node = DropDuplicatesNode()
        elif name == "Filter":
            node = FilterNode(
                Target=meta.get("filter_target", "rows"),
                Mode=meta["filter_mode"],
                MatchMode=meta.get("filter_match_mode", "or"),
                MatchValues=meta.get("filter_values", []),
                MatchBy=meta.get("filter_match_by", "values"),
            )
        elif name == "Generate Column":
            node = GenerateColumnNode(meta["new_column"], meta["operator"], meta["source_columns"])
        elif name == "Validate Required Columns":
            node = ValidateRequiredColumnsNode(meta["validate_columns"])
        else:
            raise ValueError(f"Unknown node: {name}")

        return {
            "name": name,
            "node": node,
            "meta": dict(meta),
        }

    def build_enabled_nodes():
        return [build_node_from_operation(operation) for operation in operation_order]

    def build_step_diff(step_name, previous_df, current_df, meta=None):
        if meta is None:
            meta = {}

        prev = previous_df.reset_index(drop=True).copy()
        curr = current_df.reset_index(drop=True).copy()

        prev_columns = list(prev.columns)
        curr_columns = list(curr.columns)

        def values_equal(left, right):
            try:
                if left != left and right != right:
                    return True
            except Exception:
                pass
            return left == right

        diff = {
            "added_columns": [],
            "deleted_columns": [],
            "added_rows": set(),
            "deleted_rows": set(),
            "modified_cells": set(),
            "modified_old_values": {},
            "modified_header_columns": set(),
            "added_column_cells": set(),
            "outlier_cells": set(),
            "outlier_values": [],
        }

        def has_auto_numbered_columns(df):
            expected = list(range(1, len(df.columns) + 1))
            columns = list(df.columns)
            return columns == expected or [str(column) for column in columns] == [str(column) for column in expected]

        if step_name == "Extract Table":
            diff["added_columns"] = list(curr_columns)
            diff["added_column_cells"] = set(curr_columns)
            diff["added_rows"] = set(range(len(curr)))
            return diff

        if step_name in ("Normalize", "Normalize Columns"):
            target = normalize_target_key(meta.get("normalize_target", "headers"))
            if target == "values":
                shared_columns = [column for column in curr_columns if column in prev_columns]
                for row_index in range(min(len(prev), len(curr))):
                    for col in shared_columns:
                        old_value = prev.at[row_index, col]
                        new_value = curr.at[row_index, col]
                        if not values_equal(old_value, new_value):
                            diff["modified_cells"].add((row_index, col))
                            diff["modified_old_values"][(row_index, col)] = old_value
                return diff

            if has_auto_numbered_columns(prev) and len(prev) > 0:
                diff["deleted_rows"].add(0)
                for col_index, curr_col in enumerate(curr_columns):
                    if col_index < len(prev_columns):
                        old_value = prev.iloc[0, col_index]
                        diff["modified_header_columns"].add(curr_col)
                        diff["modified_old_values"][(-1, curr_col)] = str(old_value)
                return diff

            for col_index, prev_col in enumerate(prev_columns):
                if col_index >= len(curr_columns):
                    break

                prev_col = prev_columns[col_index]
                curr_col = curr_columns[col_index]
                normalized_col = str(prev_col).strip().lower().replace(" ", "_")

                if str(prev_col) != normalized_col:
                    diff["modified_header_columns"].add(curr_col)
                    diff["modified_old_values"][(-1, curr_col)] = str(prev_col)

            return diff

        if step_name == "Replace Values":
            replace_map = dict(meta.get("replace_map", {}))
            clean_map = {}
            for old_value, new_value in replace_map.items():
                if isinstance(old_value, str):
                    old_value = old_value.strip()
                clean_map[old_value] = new_value

            exact_keys = set(clean_map.keys())
            loose_map = {str(old_value).strip(): new_value for old_value, new_value in clean_map.items()}
            has_exact_matches = False

            for row_index in range(len(prev)):
                for column_name in prev_columns:
                    prev_value = prev.iloc[row_index][column_name]
                    cleaned_value = prev_value.strip() if isinstance(prev_value, str) else prev_value
                    if cleaned_value in exact_keys:
                        has_exact_matches = True

            for row_index in range(len(prev)):
                for column_name in prev_columns:
                    prev_value = prev.iloc[row_index][column_name]
                    cleaned_value = prev_value.strip() if isinstance(prev_value, str) else prev_value
                    operation_changes_value = False

                    if cleaned_value in exact_keys:
                        replacement_value = clean_map[cleaned_value]
                        operation_changes_value = not values_equal(replacement_value, cleaned_value)
                    else:
                        loose_key = str(cleaned_value).strip()
                        if not has_exact_matches and loose_key in loose_map:
                            replacement_value = loose_map[loose_key]
                            operation_changes_value = not values_equal(replacement_value, cleaned_value)

                    if operation_changes_value and column_name in curr_columns:
                        color_key = (row_index, column_name)
                        diff["modified_cells"].add(color_key)
                        diff["modified_old_values"][color_key] = "" if prev_value is None else str(prev_value)

            return diff

        if step_name == "Coerce Data Types":
            report = meta.get("type_report", {})
            current_index_positions = {
                row_label: row_position
                for row_position, row_label in enumerate(current_df.index)
            }
            for item in report.get("corrected", []):
                row_index = current_index_positions.get(item.get("row_label"), item.get("row"))
                column_name = item.get("column")
                if row_index is None or column_name not in curr_columns:
                    continue
                color_key = (row_index, column_name)
                diff["modified_cells"].add(color_key)
                diff["modified_old_values"][color_key] = item.get("old_value", "")

            if meta.get("outlier_action", "highlight") == "delete":
                diff["deleted_rows"] = set(report.get("deleted_rows", []))
            else:
                for item in report.get("outliers", []):
                    row_index = item.get("row")
                    column_name = item.get("column")
                    if row_index is None or column_name not in curr_columns:
                        continue
                    color_key = (row_index, column_name)
                    diff["outlier_cells"].add(color_key)
                    diff["modified_old_values"][color_key] = item.get("value", "")

            diff["outlier_values"] = list(report.get("outliers", []))
            return diff

        if step_name == "Drop Duplicates":
            if len(prev) > len(curr):
                diff["deleted_rows"] = set(
                    prev.index[prev.duplicated(keep="first")].tolist()
                )
            elif len(curr) > len(prev):
                diff["added_rows"] = set(range(len(prev), len(curr)))
            return diff

        if step_name == "Filter":
            target = meta.get("filter_target", "rows")
            mode = meta.get("filter_mode", "include")
            match_mode = meta.get("filter_match_mode", "or")
            match_by = meta.get("filter_match_by", "values")
            raw_filter_values = meta.get("filter_values", meta.get("filter_columns", []))
            filter_values = {str(value).strip().lower() for value in raw_filter_values}

            def parse_index_values(count):
                positions = set()
                for value in raw_filter_values:
                    text = str(value).strip().replace(":", "-")
                    parts = [part.strip() for part in text.split("-") if part.strip()]
                    try:
                        if len(parts) == 1:
                            index = int(parts[0])
                            if 1 <= index <= count:
                                positions.add(index - 1)
                        elif len(parts) == 2:
                            start = int(parts[0])
                            end = int(parts[1])
                            if end < start:
                                start, end = end, start
                            start = max(1, start)
                            end = min(count, end)
                            for index in range(start, end + 1):
                                positions.add(index - 1)
                    except ValueError:
                        continue
                return positions

            def value_matches(existing_value, wanted_value):
                existing_parsed = parse_literal_value(str(existing_value))
                wanted_parsed = parse_literal_value(str(wanted_value))
                try:
                    if existing_parsed == wanted_parsed:
                        return True
                except Exception:
                    pass

                existing_text = str(existing_value).strip().lower().replace(" ", "_")
                wanted_text = str(wanted_value).strip().lower().replace(" ", "_")
                return wanted_text != "" and wanted_text in existing_text

            def values_match(values):
                if match_mode == "and":
                    return all(
                        any(value_matches(existing_value, wanted_value) for existing_value in values)
                        for wanted_value in filter_values
                    )
                return any(
                    value_matches(existing_value, wanted_value)
                    for existing_value in values
                    for wanted_value in filter_values
                )

            if match_by == "index" and target == "columns":
                matching_positions = parse_index_values(len(prev_columns))
                matching_columns = [
                    column_name
                    for position, column_name in enumerate(prev_columns)
                    if position in matching_positions
                ]
                if mode == "include":
                    diff["deleted_columns"] = [col for col in prev_columns if col not in matching_columns]
                else:
                    diff["deleted_columns"] = matching_columns
            elif match_by == "index":
                matching_positions = parse_index_values(len(previous_df))
                if mode == "include":
                    diff["deleted_rows"] = [
                        row_index
                        for row_index in range(len(previous_df))
                        if row_index not in matching_positions
                    ]
                else:
                    diff["deleted_rows"] = sorted(matching_positions)
            elif target == "columns":
                matching_columns = [
                    column_name
                    for column_name in prev_columns
                    if values_match([column_name])
                ]
                if mode == "include":
                    diff["deleted_columns"] = [col for col in prev_columns if col not in matching_columns]
                else:
                    diff["deleted_columns"] = matching_columns
            else:
                matching_labels = set(
                    previous_df[
                        previous_df.apply(
                            lambda row: values_match(row.tolist()),
                            axis=1
                        )
                    ].index.tolist()
                )
                diff["deleted_rows"] = {
                    row_position
                    for row_position, row_label in enumerate(previous_df.index)
                    if (row_label not in matching_labels if mode == "include" else row_label in matching_labels)
                }
            return diff

        if step_name == "Validate Required Columns":
            return diff

        if step_name == "Generate Column":
            new_column = meta.get("new_column")
            if new_column:
                diff["added_columns"] = [new_column]
            else:
                diff["added_columns"] = []
            diff["added_column_cells"] = set(diff["added_columns"])
            return diff

        if meta.get("custom_node"):
            diff["added_columns"] = [col for col in curr_columns if col not in prev_columns]
            diff["deleted_columns"] = [col for col in prev_columns if col not in curr_columns]
            diff["added_column_cells"] = set(diff["added_columns"])

            shared_columns = [col for col in curr_columns if col in prev_columns]
            for row_index in range(min(len(prev), len(curr))):
                for column_name in shared_columns:
                    old_value = prev.at[row_index, column_name]
                    new_value = curr.at[row_index, column_name]
                    if not values_equal(old_value, new_value):
                        color_key = (row_index, column_name)
                        diff["modified_cells"].add(color_key)
                        diff["modified_old_values"][color_key] = old_value
            if len(prev) > len(curr):
                diff["deleted_rows"] = set(range(len(curr), len(prev)))
            elif len(curr) > len(prev):
                diff["added_rows"] = set(range(len(prev), len(curr)))
            return diff

        return diff

    def build_final_step_cell_colors(current_df, diff, max_rows=100):
        colors = {}
        display_df = current_df.reset_index(drop=True).head(max_rows).copy()

        for column_name in display_df.columns:
            if column_name in diff["modified_header_columns"]:
                colors[(-1, column_name)] = "modified"
            elif column_name in diff["added_columns"]:
                colors[(-1, column_name)] = "added"

        for row_index in range(len(display_df)):
            for column_name in display_df.columns:
                if row_index in diff["added_rows"]:
                    colors[(row_index, column_name)] = "added"
                elif column_name in diff["added_column_cells"]:
                    colors[(row_index, column_name)] = "added"
                elif (row_index, column_name) in diff["outlier_cells"]:
                    colors[(row_index, column_name)] = "outlier"
                elif (row_index, column_name) in diff["modified_cells"]:
                    colors[(row_index, column_name)] = "modified"

        return colors

    def build_deletion_preview_step(step_name, previous_df, diff, duration_seconds):
        display_df = previous_df.reset_index(drop=True).head(100).copy()
        cell_colors = {}

        for column_name in display_df.columns:
            if column_name in diff["deleted_columns"]:
                cell_colors[(-1, column_name)] = "deleted"

        for row_index in range(len(display_df)):
            for column_name in display_df.columns:
                if row_index in diff["deleted_rows"]:
                    cell_colors[(row_index, column_name)] = "deleted"
                elif column_name in diff["deleted_columns"]:
                    cell_colors[(row_index, column_name)] = "deleted"

        diagnostics = (
            f"Time: {duration_seconds:.3f}s\n"
            f"Rows: {len(previous_df)} -> {len(previous_df)}\n"
            f"Columns: {len(previous_df.columns)} -> {len(previous_df.columns)}"
        )

        return {
            "name": f"{step_name} - Deletions",
            "data": previous_df.copy(),
            "display_df": display_df,
            "cell_colors": cell_colors,
            "hover_old_values": {},
            "diagnostics": diagnostics,
        }

    def build_step_diagnostics(step_name, previous_df, current_df, duration_seconds):
        return (
            f"Time: {duration_seconds:.3f}s\n"
            f"Rows: {len(previous_df)} -> {len(current_df)}\n"
            f"Columns: {len(previous_df.columns)} -> {len(current_df.columns)}"
        )

    def build_type_consistency_diagnostics(previous_df, current_df, duration_seconds, report):
        lines = [
            f"Time: {duration_seconds:.3f}s",
            f"Rows: {len(previous_df)} -> {len(current_df)}",
            f"Columns: {len(previous_df.columns)} -> {len(current_df.columns)}",
            f"Corrected values: {len(report.get('corrected', []))}",
            f"Outliers flagged: {len(report.get('outliers', []))}",
        ]

        outliers = report.get("outliers", [])
        if outliers:
            lines.append("Outliers:")
            for item in outliers[:8]:
                lines.append(
                    f"- {item.get('column')} | {item.get('expected_type')} | {item.get('value')}"
                )
            if len(outliers) > 8:
                lines.append(f"- ... {len(outliers) - 8} more")

        return "\n".join(lines)

    def build_total_diagnostics(start_df, final_df, duration_seconds):
        return (
            f"Total time: {duration_seconds:.3f}s\n"
            f"Total rows: {len(start_df)} -> {len(final_df)}\n"
            f"Total columns: {len(start_df.columns)} -> {len(final_df.columns)}"
        )

    def refresh_preview():
        try:
            ensure_preview_window()
            df = build_raw_preview_dataframe()
            if df is None:
                preview_info_var.set("No preview loaded.")
                processed_title_var.set("")
                processed_diag_var.set("")
                return

            preview_window.title(get_input_filename())
            preview_info_var.set(f"Previewing {len(df)} rows | {len(df.columns)} columns")
            processed_title_var.set("Dirty Input")
            processed_diag_var.set("")
            render_canvas_table(preview_table_state, df)
        except Exception as e:
            messagebox.showerror("Preview Error", str(e))

    def render_processed_step():
        if not processed_steps:
            return

        ensure_processed_window()

        step = processed_steps[processed_step_index]
        processed_window.title(get_processed_window_title())
        processed_title_var.set(f"{step['name']} ({processed_step_index + 1}/{len(processed_steps)})")
        if processed_title_label is not None and processed_title_label.winfo_exists():
            title_style = "ProcessedFinalTitle.TLabel" if step["name"] == "Processed" else "ProcessedTitle.TLabel"
            processed_title_label.configure(style=title_style)
        processed_diag_var.set(step["diagnostics"])

        render_canvas_table(
            processed_table_state,
            step["display_df"],
            cell_colors=step["cell_colors"],
            hover_old_values=step.get("hover_old_values", {})
        )

    def stop_processed_playback():
        nonlocal processed_play_job, processed_is_playing

        processed_is_playing = False
        if processed_play_job is not None and processed_window is not None and processed_window.winfo_exists():
            processed_window.after_cancel(processed_play_job)
        processed_play_job = None
        update_processed_play_button()

    def update_processed_play_button():
        if processed_play_button is not None and processed_play_button.winfo_exists():
            processed_play_button.configure(text="\u23f8" if processed_is_playing else "\u25b6")

    def play_processed_step():
        nonlocal processed_play_job, processed_is_playing, processed_step_index

        if not processed_is_playing or not processed_steps:
            return

        update_processed_play_button()
        render_processed_step()
        processed_step_index = (processed_step_index + 1) % len(processed_steps)
        step_delay = 1000 if processed_steps and processed_steps[processed_step_index - 1]["name"] == "Processed" else 500
        processed_play_job = processed_window.after(step_delay, play_processed_step)

    def toggle_processed_playback():
        nonlocal processed_is_playing

        if not processed_steps:
            return

        if processed_is_playing:
            stop_processed_playback()
            return

        processed_is_playing = True
        update_processed_play_button()
        play_processed_step()

    def autoplay_processed_steps():
        nonlocal processed_is_playing, processed_step_index

        if not processed_steps:
            return

        stop_processed_playback()
        processed_step_index = 0
        processed_is_playing = True
        update_processed_play_button()
        play_processed_step()

    def show_previous_processed_step():
        nonlocal processed_step_index

        if not processed_steps:
            return

        stop_processed_playback()
        processed_step_index = (processed_step_index - 1) % len(processed_steps)
        render_processed_step()

    def show_next_processed_step():
        nonlocal processed_step_index

        if not processed_steps:
            return

        stop_processed_playback()
        processed_step_index = (processed_step_index + 1) % len(processed_steps)
        render_processed_step()

    def on_filter_mode_changed(event=None):
        target = filter_target_var.get().strip().lower()
        mode = filter_mode_var.get().strip().lower()
        match_mode = filter_match_mode_var.get().strip().lower()
        match_by = filter_match_by_var.get().strip().lower()

        subject = "rows" if target == "rows" else "columns"
        action = "keep" if mode == "include" else "remove"
        joiner = "all listed values" if match_mode == "and" else "any listed value"
        if match_by == "index":
            filter_description_var.set(f"{mode}: {action} {subject} by 1-based index. Use 3 or 3-8.")
        else:
            filter_description_var.set(f"{mode}: {action} {subject} with {joiner}.")

    def refresh_replace_rows():
        for child in replace_rows_frame.winfo_children():
            child.destroy()

        for row_index, row_data in enumerate(replace_rows):
            row_frame = ttk.Frame(replace_rows_frame, style="StormPanel.TFrame")
            row_frame.grid(row=row_index, column=0, sticky="ew", pady=2)
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=1)

            from_entry = ttk.Entry(row_frame, textvariable=row_data["from_var"])
            from_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
            row_data["from_entry"] = from_entry

            to_entry = ttk.Entry(row_frame, textvariable=row_data["to_var"])
            to_entry.grid(row=0, column=1, sticky="ew", padx=(0, 6))
            row_data["to_entry"] = to_entry

            ttk.Button(
                row_frame,
                text="X",
                width=3,
                style="Small.TButton",
                command=lambda idx=row_index: delete_replace_row(idx)
            ).grid(row=0, column=2, sticky="e")

    def add_replace_row(from_value="", to_value=""):
        from_var = tk.StringVar(value=from_value)
        to_var = tk.StringVar(value=to_value)
        from_var.trace_add("write", lambda *args: mark_tuneables_changed("Replace Values"))
        to_var.trace_add("write", lambda *args: mark_tuneables_changed("Replace Values"))
        row_data = {
            "from_var": from_var,
            "to_var": to_var,
        }
        replace_rows.append(row_data)
        refresh_replace_rows()
        mark_tuneables_changed("Replace Values")

    def delete_replace_row(index):
        if 0 <= index < len(replace_rows):
            del replace_rows[index]

        if not replace_rows:
            add_replace_row()
        else:
            refresh_replace_rows()
            mark_tuneables_changed("Replace Values")

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

    def refresh_filter_rows():
        for child in filter_rows_frame.winfo_children():
            child.destroy()

        for row_index, row_data in enumerate(filter_rows):
            row_frame = ttk.Frame(filter_rows_frame, style="StormPanel.TFrame")
            row_frame.grid(row=row_index, column=0, sticky="ew", pady=2)
            row_frame.grid_columnconfigure(0, weight=1)

            entry = ttk.Entry(row_frame, textvariable=row_data["value_var"])
            entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
            row_data["entry"] = entry

            ttk.Button(
                row_frame,
                text="X",
                width=3,
                style="Small.TButton",
                command=lambda idx=row_index: delete_filter_row(idx)
            ).grid(row=0, column=1, sticky="e")

    def add_filter_row(value=""):
        value_var = tk.StringVar(value=value)
        value_var.trace_add("write", lambda *args: mark_tuneables_changed("Filter"))
        row_data = {
            "value_var": value_var,
        }
        filter_rows.append(row_data)
        refresh_filter_rows()
        mark_tuneables_changed("Filter")

    def delete_filter_row(index):
        if 0 <= index < len(filter_rows):
            del filter_rows[index]

        if not filter_rows:
            add_filter_row()
        else:
            refresh_filter_rows()
            mark_tuneables_changed("Filter")

    def build_filter_columns():
        cols = []
        for row_data in filter_rows:
            value = row_data["value_var"].get().strip()
            if value:
                cols.append(value)
        return cols

    def refresh_generate_rows():
        for child in generate_rows_frame.winfo_children():
            child.destroy()

        for row_index, row_data in enumerate(generate_rows):
            row_frame = ttk.Frame(generate_rows_frame, style="StormPanel.TFrame")
            row_frame.grid(row=row_index, column=0, sticky="ew", pady=2)
            row_frame.grid_columnconfigure(0, weight=1)

            entry = ttk.Entry(row_frame, textvariable=row_data["value_var"])
            entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
            row_data["entry"] = entry

            ttk.Button(
                row_frame,
                text="X",
                width=3,
                style="Small.TButton",
                command=lambda idx=row_index: delete_generate_row(idx)
            ).grid(row=0, column=1, sticky="e")

    def add_generate_row(value=""):
        value_var = tk.StringVar(value=value)
        value_var.trace_add("write", lambda *args: mark_tuneables_changed("Generate Column"))
        row_data = {
            "value_var": value_var,
        }
        generate_rows.append(row_data)
        refresh_generate_rows()
        mark_tuneables_changed("Generate Column")

    def delete_generate_row(index):
        if 0 <= index < len(generate_rows):
            del generate_rows[index]

        if not generate_rows:
            add_generate_row()
        else:
            refresh_generate_rows()
            mark_tuneables_changed("Generate Column")

    def build_generate_columns():
        cols = []
        for row_data in generate_rows:
            value = row_data["value_var"].get().strip()
            if value:
                cols.append(value)
        return cols

    def refresh_validate_rows():
        for child in validate_rows_frame.winfo_children():
            child.destroy()

        for row_index, row_data in enumerate(validate_rows):
            row_frame = ttk.Frame(validate_rows_frame, style="StormPanel.TFrame")
            row_frame.grid(row=row_index, column=0, sticky="ew", pady=2)
            row_frame.grid_columnconfigure(0, weight=1)

            entry = ttk.Entry(row_frame, textvariable=row_data["value_var"])
            entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
            row_data["entry"] = entry

            ttk.Button(
                row_frame,
                text="X",
                width=3,
                style="Small.TButton",
                command=lambda idx=row_index: delete_validate_row(idx)
            ).grid(row=0, column=1, sticky="e")

    def add_validate_row(value=""):
        value_var = tk.StringVar(value=value)
        value_var.trace_add("write", lambda *args: mark_tuneables_changed("Validate Required Columns"))
        row_data = {
            "value_var": value_var,
        }
        validate_rows.append(row_data)
        refresh_validate_rows()
        mark_tuneables_changed("Validate Required Columns")

    def delete_validate_row(index):
        if 0 <= index < len(validate_rows):
            del validate_rows[index]

        if not validate_rows:
            add_validate_row()
        else:
            refresh_validate_rows()
            mark_tuneables_changed("Validate Required Columns")

    def build_validate_columns():
        cols = []
        for row_data in validate_rows:
            value = row_data["value_var"].get().strip()
            if value:
                cols.append(value)
        return cols

    def run_pipeline():
        nonlocal processed_steps, processed_step_index

        try:
            import pandas as pd

            input_path = input_var.get().strip()

            if not input_path:
                messagebox.showerror("Missing Input", "Please choose an input CSV file.")
                return

            Data = ReadCsvRows(input_path)
            start_data = Data.copy()
            pipeline_started_at = time.perf_counter()

            steps = []
            raw_display = Data.reset_index(drop=True).head(100).copy()
            steps.append({
                "name": "Raw Input",
                "data": Data.copy(),
                "display_df": raw_display,
                "cell_colors": {},
                "hover_old_values": {},
                "diagnostics": f"Time: 0.000s\nRows: {len(Data)} -> {len(Data)}\nColumns: {len(Data.columns)} -> {len(Data.columns)}"
            })

            enabled_nodes = build_enabled_nodes()

            for step in enabled_nodes:
                step_name = step["name"]
                node = step["node"]
                meta = step["meta"]

                previous_df = Data.copy()

                started_at = time.perf_counter()
                Data = node.Run(Data)
                duration_seconds = time.perf_counter() - started_at
                if step_name == "Coerce Data Types":
                    meta = dict(meta)
                    meta["type_report"] = getattr(node, "Report", {})

                current_df = Data.copy()
                diff = build_step_diff(step_name, previous_df, current_df, meta)

                if diff["deleted_rows"] or diff["deleted_columns"]:
                    steps.append(
                        build_deletion_preview_step(step_name, previous_df, diff, duration_seconds)
                    )

                cell_colors = build_final_step_cell_colors(current_df, diff, max_rows=100)
                if step_name == "Coerce Data Types":
                    diagnostics = build_type_consistency_diagnostics(
                        previous_df,
                        current_df,
                        duration_seconds,
                        meta.get("type_report", {})
                    )
                else:
                    diagnostics = build_step_diagnostics(step_name, previous_df, current_df, duration_seconds)

                steps.append({
                    "name": step_name,
                    "data": current_df,
                    "display_df": current_df.reset_index(drop=True).head(100).copy(),
                    "cell_colors": cell_colors,
                    "hover_old_values": diff["modified_old_values"],
                    "diagnostics": diagnostics,
                })

            total_duration_seconds = time.perf_counter() - pipeline_started_at
            steps.append({
                "name": "Processed",
                "data": Data.copy(),
                "display_df": Data.reset_index(drop=True).head(100).copy(),
                "cell_colors": {},
                "hover_old_values": {},
                "diagnostics": build_total_diagnostics(start_data, Data, total_duration_seconds),
            })

            processed_steps = steps
            processed_step_index = 0
            stop_processed_playback()
            render_processed_step()
            autoplay_processed_steps()

        except Exception as e:
            messagebox.showerror("Pipeline Error", str(e))

    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(0, weight=1)

    top = ttk.Frame(root, padding=10, style="Storm.TFrame")
    top.grid(row=0, column=0, sticky="ew")
    top.grid_columnconfigure(1, weight=1)

    ttk.Label(top, text="Input CSV", style="StormTop.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8))
    ttk.Entry(top, textvariable=input_var).grid(row=0, column=1, sticky="ew", padx=(0, 8))
    browse_button = ttk.Button(top, text="Select File", style=browse_pulse_styles[0], command=choose_input)
    browse_button.grid(row=0, column=2, sticky="ew")
    pulse_browse_button()

    main = ttk.Frame(root, padding=(10, 0, 10, 10), style="Storm.TFrame")
    main.grid(row=1, column=0, sticky="nsew")
    main.grid_rowconfigure(0, weight=1)
    main.grid_columnconfigure(0, weight=1)
    main.grid_columnconfigure(1, weight=0)
    main.grid_columnconfigure(2, weight=1)

    global_content = ttk.Frame(main, style="Storm.TFrame", width=520)
    global_content.grid(row=0, column=1, sticky="nsew")
    global_content.grid_propagate(False)
    global_content.grid_columnconfigure(0, weight=1)
    global_content.grid_rowconfigure(1, weight=1)

    scroll_targets = {}
    scroll_regions = []
    scroll_sections = []

    def register_scroll_target(canvas, *widgets):
        for widget in (canvas, *widgets):
            scroll_targets[widget] = canvas
            scroll_regions.append((widget, canvas))

    def contains_screen_point(widget, x_root, y_root):
        if not widget.winfo_ismapped():
            return False

        x = widget.winfo_rootx()
        y = widget.winfo_rooty()
        return (
            x <= x_root < x + widget.winfo_width()
            and y <= y_root < y + widget.winfo_height()
        )

    def find_scroll_canvas(widget, x_root, y_root):
        for region_widget, canvas in reversed(scroll_sections):
            if contains_screen_point(region_widget, x_root, y_root):
                return canvas

        for region_widget, canvas in reversed(scroll_regions):
            if contains_screen_point(region_widget, x_root, y_root):
                return canvas

        while widget is not None:
            if widget in scroll_targets:
                return scroll_targets[widget]
            widget = getattr(widget, "master", None)
        return None

    def can_scroll_canvas(canvas, units):
        if canvas is None:
            return False

        top, bottom = canvas.yview()
        if units < 0:
            return top > 0.0
        return bottom < 1.0

    def scroll_canvas_from_wheel(event):
        widget = root.winfo_containing(event.x_root, event.y_root)
        canvas = find_scroll_canvas(widget, event.x_root, event.y_root)
        if canvas is None:
            return None

        if event.num == 4:
            units = -1
        elif event.num == 5:
            units = 1
        else:
            units = -1 if event.delta > 0 else 1

        if can_scroll_canvas(canvas, units):
            canvas.yview_scroll(units, "units")
        return "break"

    root.bind_all("<MouseWheel>", scroll_canvas_from_wheel)
    root.bind_all("<Button-4>", scroll_canvas_from_wheel)
    root.bind_all("<Button-5>", scroll_canvas_from_wheel)

    def create_scrollable_section(parent, title, row, height, row_weight=0):
        section_box = ttk.LabelFrame(parent, text=title, padding=10, style="Storm.TLabelframe")
        section_box.grid(row=row, column=0, sticky="nsew" if row_weight else "ew", pady=(0, 8))
        section_box.grid_columnconfigure(0, weight=1)
        section_box.grid_rowconfigure(0, weight=1)

        section_canvas = tk.Canvas(section_box, bg=storm_blue, highlightthickness=0, bd=0, height=height)
        section_canvas.grid(row=0, column=0, sticky="nsew")
        section_scrollbar = ttk.Scrollbar(section_box, orient="vertical", command=section_canvas.yview)
        section_scrollbar.grid(row=0, column=1, sticky="ns")
        section_canvas.configure(yscrollcommand=section_scrollbar.set)

        section_content = ttk.Frame(section_canvas, style="StormPanel.TFrame")
        section_window_id = section_canvas.create_window((0, 0), window=section_content, anchor="nw")
        section_content.grid_columnconfigure(0, weight=1)

        def on_section_content_configure(event=None):
            section_canvas.configure(scrollregion=section_canvas.bbox("all"))

        def on_section_canvas_configure(event):
            section_canvas.itemconfigure(section_window_id, width=event.width)

        section_content.bind("<Configure>", on_section_content_configure)
        section_canvas.bind("<Configure>", on_section_canvas_configure)
        register_scroll_target(section_canvas, section_box, section_content, section_scrollbar)
        scroll_sections.append((section_box, section_canvas))
        scroll_sections.append((section_canvas, section_canvas))

        return section_content, section_box

    order_rows_frame, order_section_box = create_scrollable_section(global_content, "Run Order", 0, 169)
    nodes_box, nodes_section_box = create_scrollable_section(global_content, "Pipeline Nodes", 1, 325, row_weight=1)

    node_row = 0

    def add_custom_node_card(display_name, spec, row):
        custom_box = ttk.Frame(nodes_box, style="StormPanel.TFrame")
        custom_box.grid(row=row, column=0, sticky="ew", pady=(0, 6))
        custom_box.grid_columnconfigure(0, weight=1)

        custom_header = ttk.Frame(custom_box, style="StormPanel.TFrame")
        custom_header.grid(row=0, column=0, sticky="ew")
        custom_header.grid_columnconfigure(1, weight=1)

        ttk.Button(
            custom_header,
            text="+ add",
            width=5,
            style="Add.TButton",
            command=lambda node_name=display_name: add_order_item(node_name)
        ).grid(row=0, column=0, sticky="w", padx=(0, 6))

        custom_toggle = ttk.Button(
            custom_header,
            text=f"{display_name} v",
            style="CustomNodeToggle.TButton"
        )
        custom_toggle.grid(row=0, column=1, sticky="ew")

        custom_info = ttk.Frame(custom_box, padding=(24, 6, 0, 0), style="StormPanel.TFrame")
        custom_info.grid(row=1, column=0, sticky="ew")
        ttk.Label(
            custom_info,
            text="Custom node supplied by this project. It runs with its default constructor settings.",
            style="CustomStorm.TLabel",
            wraplength=360,
            justify="left"
        ).grid(row=0, column=0, sticky="w")
        custom_toggle.configure(
            command=lambda frame=custom_info, button=custom_toggle, label=display_name: toggle_settings(frame, button, label)
        )
        show_section(custom_info, False)

    for custom_display_name, custom_spec in custom_node_specs.items():
        add_custom_node_card(custom_display_name, custom_spec, node_row)
        node_row += 1

    extract_table_box = ttk.Frame(nodes_box, style="StormPanel.TFrame")
    extract_table_box.grid(row=node_row, column=0, sticky="ew", pady=(0, 6))
    extract_table_box.grid_columnconfigure(0, weight=1)

    extract_table_header = ttk.Frame(extract_table_box, style="StormPanel.TFrame")
    extract_table_header.grid(row=0, column=0, sticky="ew")
    extract_table_header.grid_columnconfigure(1, weight=1)
    extract_table_add_button = ttk.Button(
        extract_table_header,
        text="+ add",
        width=5,
        style="Add.TButton",
        command=lambda: add_order_item("Extract Table")
    )
    extract_table_add_button.grid(row=0, column=0, sticky="w", padx=(0, 6))
    tunable_add_buttons["Extract Table"] = extract_table_add_button
    extract_table_toggle = ttk.Button(
        extract_table_header,
        text=format_node_toggle_text("Extract Table", False),
        style="NodeToggle.TButton"
    )
    extract_table_toggle.grid(row=0, column=1, sticky="ew")
    extract_table_toggle.configure(command=lambda: toggle_settings(extract_table_settings, extract_table_toggle, "Extract Table"))
    extract_table_reset_button = ttk.Button(
        extract_table_header,
        text="\u21b6",
        width=3,
        style="Small.TButton",
        command=lambda: reset_tuneables("Extract Table")
    )
    extract_table_reset_button.grid(row=0, column=2, sticky="e", padx=(6, 0))
    extract_table_reset_button.grid_remove()
    tunable_reset_buttons["Extract Table"] = extract_table_reset_button

    extract_table_settings = ttk.Frame(extract_table_box, padding=(24, 6, 0, 0), style="StormPanel.TFrame")
    extract_table_settings.grid(row=1, column=0, sticky="ew")
    extract_table_settings.grid_columnconfigure(0, weight=0)
    extract_table_settings.grid_columnconfigure(1, weight=1)
    ttk.Label(
        extract_table_settings,
        text="Pulls one detected table out of a report-style CSV that has metadata, spacer rows, or multiple tables.",
        style="Storm.TLabel",
        wraplength=360,
        justify="left"
    ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
    ttk.Label(extract_table_settings, text="Table", style="Storm.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8))
    extract_table_entry = ttk.Entry(
        extract_table_settings,
        textvariable=extract_table_var,
        width=10
    )
    extract_table_entry.grid(row=1, column=1, sticky="w")
    ttk.Label(
        extract_table_settings,
        textvariable=extract_table_recommendation_var,
        style="Storm.TLabel",
        wraplength=360,
        justify="left"
    ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(5, 0))

    node_row += 1

    normalize_box = ttk.Frame(nodes_box, style="StormPanel.TFrame")
    normalize_box.grid(row=node_row, column=0, sticky="ew", pady=(0, 6))
    normalize_box.grid_columnconfigure(0, weight=1)

    normalize_header = ttk.Frame(normalize_box, style="StormPanel.TFrame")
    normalize_header.grid(row=0, column=0, sticky="ew")
    normalize_header.grid_columnconfigure(1, weight=1)
    normalize_add_button = ttk.Button(
        normalize_header,
        text="+ add",
        width=5,
        style="Add.TButton",
        command=lambda: add_order_item("Normalize")
    )
    normalize_add_button.grid(row=0, column=0, sticky="w", padx=(0, 6))
    tunable_add_buttons["Normalize"] = normalize_add_button
    normalize_toggle = ttk.Button(normalize_header, text=format_node_toggle_text("Normalize", False), style="NodeToggle.TButton")
    normalize_toggle.grid(row=0, column=1, sticky="ew")
    normalize_toggle.configure(command=lambda: toggle_settings(normalize_info, normalize_toggle, "Normalize"))
    normalize_reset_button = ttk.Button(
        normalize_header,
        text="\u21b6",
        width=3,
        style="Small.TButton",
        command=lambda: reset_tuneables("Normalize")
    )
    normalize_reset_button.grid(row=0, column=2, sticky="e", padx=(6, 0))
    normalize_reset_button.grid_remove()
    tunable_reset_buttons["Normalize"] = normalize_reset_button

    normalize_info = ttk.Frame(normalize_box, padding=(24, 6, 0, 0), style="StormPanel.TFrame")
    normalize_info.grid(row=1, column=0, sticky="ew")
    normalize_info.grid_columnconfigure(0, weight=0)
    normalize_info.grid_columnconfigure(1, weight=1)
    ttk.Label(
        normalize_info,
        text="Cleans text by: Trimming (Whitespace), lowercasing, space to underscore.",
        style="Storm.TLabel",
        wraplength=360,
        justify="left"
    ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

    ttk.Label(normalize_info, text="Target", style="Storm.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8))
    ttk.Combobox(
        normalize_info,
        textvariable=normalize_target_var,
        values=["column headers", "all cells"],
        state="readonly",
        width=16
    ).grid(row=1, column=1, sticky="w")

    node_row += 1

    replace_box = ttk.Frame(nodes_box, style="StormPanel.TFrame")
    replace_box.grid(row=node_row, column=0, sticky="ew", pady=(0, 6))
    replace_box.grid_columnconfigure(0, weight=1)

    replace_header = ttk.Frame(replace_box, style="StormPanel.TFrame")
    replace_header.grid(row=0, column=0, sticky="ew")
    replace_header.grid_columnconfigure(1, weight=1)
    replace_add_button = ttk.Button(
        replace_header,
        text="+ add",
        width=5,
        style="Add.TButton",
        command=lambda: add_order_item("Replace Values"),
    )
    replace_add_button.grid(row=0, column=0, sticky="w", padx=(0, 6))
    tunable_add_buttons["Replace Values"] = replace_add_button
    replace_toggle = ttk.Button(replace_header, text=format_node_toggle_text("Replace Values", False), style="NodeToggle.TButton")
    replace_toggle.grid(row=0, column=1, sticky="ew")
    replace_toggle.configure(command=lambda: toggle_settings(replace_settings, replace_toggle, "Replace Values"))
    replace_reset_button = ttk.Button(
        replace_header,
        text="\u21b6",
        width=3,
        style="Small.TButton",
        command=lambda: reset_tuneables("Replace Values")
    )
    replace_reset_button.grid(row=0, column=2, sticky="e", padx=(6, 0))
    replace_reset_button.grid_remove()
    tunable_reset_buttons["Replace Values"] = replace_reset_button

    replace_settings = ttk.Frame(replace_box, padding=(24, 6, 0, 0), style="StormPanel.TFrame")
    replace_settings.grid(row=1, column=0, sticky="ew")
    replace_settings.grid_columnconfigure(0, weight=1)

    ttk.Label(
        replace_settings,
        text="Finds matching cell values anywhere in the table and swaps them for the replacement value.",
        style="Storm.TLabel",
        wraplength=360,
        justify="left"
    ).grid(row=0, column=0, sticky="w", pady=(0, 6))

    replace_header_labels = ttk.Frame(replace_settings, style="StormPanel.TFrame")
    replace_header_labels.grid(row=1, column=0, sticky="ew", pady=(0, 4))
    replace_header_labels.grid_columnconfigure(0, weight=1)
    replace_header_labels.grid_columnconfigure(1, weight=1)
    ttk.Label(replace_header_labels, text="Value", style="Storm.TLabel").grid(
        row=0, column=0, sticky="w", padx=(0, 6)
    )
    ttk.Label(replace_header_labels, text="Replacement", style="Storm.TLabel").grid(
        row=0, column=1, sticky="w", padx=(0, 6)
    )

    replace_rows_frame = ttk.Frame(replace_settings, style="StormPanel.TFrame")
    replace_rows_frame.grid(row=2, column=0, sticky="ew")
    replace_rows_frame.grid_columnconfigure(0, weight=1)

    ttk.Button(
        replace_settings,
        text="+ Add Row",
        style="Small.TButton",
        command=add_replace_row
    ).grid(row=3, column=0, sticky="w", pady=(6, 0))

    node_row += 1

    type_box = ttk.Frame(nodes_box, style="StormPanel.TFrame")
    type_box.grid(row=node_row, column=0, sticky="ew", pady=(0, 6))
    type_box.grid_columnconfigure(0, weight=1)

    type_header = ttk.Frame(type_box, style="StormPanel.TFrame")
    type_header.grid(row=0, column=0, sticky="ew")
    type_header.grid_columnconfigure(1, weight=1)
    type_add_button = ttk.Button(
        type_header,
        text="+ add",
        width=5,
        style="Add.TButton",
        command=lambda: add_order_item("Coerce Data Types"),
    )
    type_add_button.grid(row=0, column=0, sticky="w", padx=(0, 6))
    tunable_add_buttons["Coerce Data Types"] = type_add_button
    type_toggle = ttk.Button(type_header, text=format_node_toggle_text("Coerce Data Types", False), style="NodeToggle.TButton")
    type_toggle.grid(row=0, column=1, sticky="ew")
    type_toggle.configure(command=lambda: toggle_settings(type_settings, type_toggle, "Coerce Data Types"))
    type_reset_button = ttk.Button(
        type_header,
        text="\u21b6",
        width=3,
        style="Small.TButton",
        command=lambda: reset_tuneables("Coerce Data Types")
    )
    type_reset_button.grid(row=0, column=2, sticky="e", padx=(6, 0))
    type_reset_button.grid_remove()
    tunable_reset_buttons["Coerce Data Types"] = type_reset_button

    type_settings = ttk.Frame(type_box, padding=(24, 6, 0, 0), style="StormPanel.TFrame")
    type_settings.grid(row=1, column=0, sticky="ew")
    type_settings.grid_columnconfigure(0, weight=0)
    type_settings.grid_columnconfigure(1, weight=1)
    ttk.Label(
        type_settings,
        text="Finds the dominant type in each column, fixes values it can coerce, and flags values that do not fit.",
        style="Storm.TLabel",
        wraplength=360,
        justify="left"
    ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

    ttk.Label(type_settings, text="Outliers", style="Storm.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8))
    ttk.Combobox(
        type_settings,
        textvariable=type_outlier_action_var,
        values=["highlight", "delete"],
        state="readonly",
        width=14
    ).grid(row=1, column=1, sticky="w")

    node_row += 1

    dropdup_box = ttk.Frame(nodes_box, style="StormPanel.TFrame")
    dropdup_box.grid(row=node_row, column=0, sticky="ew", pady=(0, 6))
    dropdup_box.grid_columnconfigure(0, weight=1)

    dropdup_header = ttk.Frame(dropdup_box, style="StormPanel.TFrame")
    dropdup_header.grid(row=0, column=0, sticky="ew")
    dropdup_header.grid_columnconfigure(1, weight=1)
    ttk.Button(
        dropdup_header,
        text="+ add",
        width=5,
        style="Add.TButton",
        command=lambda: add_order_item("Drop Duplicates")
    ).grid(row=0, column=0, sticky="w", padx=(0, 6))
    dropdup_toggle = ttk.Button(dropdup_header, text=format_node_toggle_text("Drop Duplicates", False), style="NodeToggle.TButton")
    dropdup_toggle.grid(row=0, column=1, sticky="ew")
    dropdup_toggle.configure(command=lambda: toggle_settings(dropdup_info, dropdup_toggle, "Drop Duplicates"))

    dropdup_info = ttk.Frame(dropdup_box, padding=(24, 6, 0, 0), style="StormPanel.TFrame")
    dropdup_info.grid(row=1, column=0, sticky="ew")
    ttk.Label(
        dropdup_info,
        text="Removes repeated rows. If two rows are identical, the first one is kept and later copies are removed.",
        style="Storm.TLabel",
        wraplength=360,
        justify="left"
    ).grid(row=0, column=0, sticky="w")

    node_row += 1

    filter_box = ttk.Frame(nodes_box, style="StormPanel.TFrame")
    filter_box.grid(row=node_row, column=0, sticky="ew", pady=(0, 6))
    filter_box.grid_columnconfigure(0, weight=1)

    filter_header = ttk.Frame(filter_box, style="StormPanel.TFrame")
    filter_header.grid(row=0, column=0, sticky="ew")
    filter_header.grid_columnconfigure(1, weight=1)
    filter_add_button = ttk.Button(
        filter_header,
        text="+ add",
        width=5,
        style="Add.TButton",
        command=lambda: add_order_item("Filter"),
    )
    filter_add_button.grid(row=0, column=0, sticky="w", padx=(0, 6))
    tunable_add_buttons["Filter"] = filter_add_button
    filter_toggle = ttk.Button(filter_header, text=format_node_toggle_text("Filter", False), style="NodeToggle.TButton")
    filter_toggle.grid(row=0, column=1, sticky="ew")
    filter_toggle.configure(command=lambda: toggle_settings(filter_settings, filter_toggle, "Filter"))
    filter_reset_button = ttk.Button(
        filter_header,
        text="\u21b6",
        width=3,
        style="Small.TButton",
        command=lambda: reset_tuneables("Filter")
    )
    filter_reset_button.grid(row=0, column=2, sticky="e", padx=(6, 0))
    filter_reset_button.grid_remove()
    tunable_reset_buttons["Filter"] = filter_reset_button

    filter_settings = ttk.Frame(filter_box, padding=(24, 6, 0, 0), style="StormPanel.TFrame")
    filter_settings.grid(row=1, column=0, sticky="ew")
    filter_settings.grid_columnconfigure(0, weight=1)
    filter_settings.grid_columnconfigure(1, weight=0)

    ttk.Label(
        filter_settings,
        textvariable=filter_description_var,
        style="Storm.TLabel",
        wraplength=360,
        justify="left"
    ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

    ttk.Label(filter_settings, text="Target", style="Storm.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 6))

    filter_target_combo = ttk.Combobox(
        filter_settings,
        textvariable=filter_target_var,
        values=["rows", "columns"],
        state="readonly",
        width=14
    )
    filter_target_combo.grid(row=1, column=1, sticky="e", pady=(0, 6))
    filter_target_combo.bind("<<ComboboxSelected>>", on_filter_mode_changed)

    ttk.Label(filter_settings, text="Mode", style="Storm.TLabel").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(0, 6))

    filter_mode_combo = ttk.Combobox(
        filter_settings,
        textvariable=filter_mode_var,
        values=["include", "exclude"],
        state="readonly",
        width=14
    )
    filter_mode_combo.grid(row=2, column=1, sticky="e", pady=(0, 6))
    filter_mode_combo.bind("<<ComboboxSelected>>", on_filter_mode_changed)

    ttk.Label(filter_settings, text="Match", style="Storm.TLabel").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=(0, 6))

    filter_match_by_combo = ttk.Combobox(
        filter_settings,
        textvariable=filter_match_by_var,
        values=["values", "index"],
        state="readonly",
        width=14
    )
    filter_match_by_combo.grid(row=3, column=1, sticky="e", pady=(0, 6))
    filter_match_by_combo.bind("<<ComboboxSelected>>", on_filter_mode_changed)

    ttk.Label(filter_settings, text="Logic", style="Storm.TLabel").grid(row=4, column=0, sticky="w", padx=(0, 8), pady=(0, 6))

    filter_match_combo = ttk.Combobox(
        filter_settings,
        textvariable=filter_match_mode_var,
        values=["or", "and"],
        state="readonly",
        width=14
    )
    filter_match_combo.grid(row=4, column=1, sticky="e", pady=(0, 6))
    filter_match_combo.bind("<<ComboboxSelected>>", on_filter_mode_changed)

    ttk.Label(filter_settings, text="Values / indexes", style="Storm.TLabel").grid(row=5, column=0, columnspan=2, sticky="w")

    filter_rows_frame = ttk.Frame(filter_settings, style="StormPanel.TFrame")
    filter_rows_frame.grid(row=6, column=0, columnspan=2, sticky="ew")
    filter_rows_frame.grid_columnconfigure(0, weight=1)

    ttk.Button(
        filter_settings,
        text="+ Add Row",
        style="Small.TButton",
        command=add_filter_row
    ).grid(row=7, column=0, columnspan=2, sticky="w", pady=(6, 0))

    node_row += 1

    generate_box = ttk.Frame(nodes_box, style="StormPanel.TFrame")
    generate_box.grid(row=node_row, column=0, sticky="ew", pady=(0, 6))
    generate_box.grid_columnconfigure(0, weight=1)

    generate_header = ttk.Frame(generate_box, style="StormPanel.TFrame")
    generate_header.grid(row=0, column=0, sticky="ew")
    generate_header.grid_columnconfigure(1, weight=1)
    generate_add_button = ttk.Button(
        generate_header,
        text="+ add",
        width=5,
        style="Add.TButton",
        command=lambda: add_order_item("Generate Column"),
    )
    generate_add_button.grid(row=0, column=0, sticky="w", padx=(0, 6))
    tunable_add_buttons["Generate Column"] = generate_add_button
    generate_toggle = ttk.Button(generate_header, text=format_node_toggle_text("Generate Column", False), style="NodeToggle.TButton")
    generate_toggle.grid(row=0, column=1, sticky="ew")
    generate_toggle.configure(command=lambda: toggle_settings(generate_settings, generate_toggle, "Generate Column"))
    generate_reset_button = ttk.Button(
        generate_header,
        text="\u21b6",
        width=3,
        style="Small.TButton",
        command=lambda: reset_tuneables("Generate Column")
    )
    generate_reset_button.grid(row=0, column=2, sticky="e", padx=(6, 0))
    generate_reset_button.grid_remove()
    tunable_reset_buttons["Generate Column"] = generate_reset_button

    generate_settings = ttk.Frame(generate_box, padding=(24, 6, 0, 0), style="StormPanel.TFrame")
    generate_settings.grid(row=1, column=0, sticky="ew")
    generate_settings.grid_columnconfigure(0, weight=1)

    ttk.Label(
        generate_settings,
        text="Adds a new column by applying one arithmetic operator across existing columns in order.",
        style="Storm.TLabel",
        wraplength=360,
        justify="left"
    ).grid(row=0, column=0, sticky="w", pady=(0, 6))
    ttk.Label(
        generate_settings,
        text="Example: unit_price, quantity with * creates unit_price * quantity",
        style="Storm.TLabel",
        wraplength=360,
        justify="left"
    ).grid(row=1, column=0, sticky="w", pady=(0, 6))

    ttk.Label(generate_settings, text="New column name", style="Storm.TLabel").grid(row=2, column=0, sticky="w")
    generate_column_name_entry = ttk.Entry(generate_settings, textvariable=generate_column_name_var)
    generate_column_name_entry.grid(row=3, column=0, sticky="ew", pady=(2, 6))

    ttk.Label(generate_settings, text="Operator to apply", style="Storm.TLabel").grid(row=4, column=0, sticky="w")
    generate_operator_combo = ttk.Combobox(
        generate_settings,
        textvariable=generate_operator_var,
        values=["+", "-", "*", "/"],
        state="readonly",
        width=6
    )
    generate_operator_combo.grid(row=5, column=0, sticky="w", pady=(2, 6))

    ttk.Label(generate_settings, text="Existing columns to combine", style="Storm.TLabel").grid(row=6, column=0, sticky="w")

    generate_rows_frame = ttk.Frame(generate_settings, style="StormPanel.TFrame")
    generate_rows_frame.grid(row=7, column=0, sticky="ew")
    generate_rows_frame.grid_columnconfigure(0, weight=1)

    ttk.Button(
        generate_settings,
        text="+ Add Row",
        style="Small.TButton",
        command=add_generate_row
    ).grid(row=8, column=0, sticky="w", pady=(6, 0))

    node_row += 1

    validate_box = ttk.Frame(nodes_box, style="StormPanel.TFrame")
    validate_box.grid(row=node_row, column=0, sticky="ew", pady=(0, 6))
    validate_box.grid_columnconfigure(0, weight=1)

    validate_header = ttk.Frame(validate_box, style="StormPanel.TFrame")
    validate_header.grid(row=0, column=0, sticky="ew")
    validate_header.grid_columnconfigure(1, weight=1)
    validate_add_button = ttk.Button(
        validate_header,
        text="+ add",
        width=5,
        style="Add.TButton",
        command=lambda: add_order_item("Validate Required Columns"),
    )
    validate_add_button.grid(row=0, column=0, sticky="w", padx=(0, 6))
    tunable_add_buttons["Validate Required Columns"] = validate_add_button
    validate_toggle = ttk.Button(validate_header, text=format_node_toggle_text("Validate Required Columns", False), style="NodeToggle.TButton")
    validate_toggle.grid(row=0, column=1, sticky="ew")
    validate_toggle.configure(command=lambda: toggle_settings(validate_settings, validate_toggle, "Validate Required Columns"))
    validate_reset_button = ttk.Button(
        validate_header,
        text="\u21b6",
        width=3,
        style="Small.TButton",
        command=lambda: reset_tuneables("Validate Required Columns")
    )
    validate_reset_button.grid(row=0, column=2, sticky="e", padx=(6, 0))
    validate_reset_button.grid_remove()
    tunable_reset_buttons["Validate Required Columns"] = validate_reset_button

    validate_settings = ttk.Frame(validate_box, padding=(24, 6, 0, 0), style="StormPanel.TFrame")
    validate_settings.grid(row=1, column=0, sticky="ew")
    validate_settings.grid_columnconfigure(0, weight=1)

    ttk.Label(
        validate_settings,
        text="Checks that these columns exist at this point in the run. It does not change the table; it stops the run if any are missing.",
        style="Storm.TLabel",
        wraplength=360,
        justify="left"
    ).grid(row=0, column=0, sticky="w", pady=(0, 6))

    ttk.Label(validate_settings, text="Columns that must exist", style="Storm.TLabel").grid(row=1, column=0, sticky="w")

    validate_rows_frame = ttk.Frame(validate_settings, style="StormPanel.TFrame")
    validate_rows_frame.grid(row=2, column=0, sticky="ew")
    validate_rows_frame.grid_columnconfigure(0, weight=1)

    ttk.Button(
        validate_settings,
        text="+ Add Row",
        style="Small.TButton",
        command=add_validate_row
    ).grid(row=3, column=0, sticky="w", pady=(6, 0))

    node_row += 1

    builtin_row_offset = len(custom_node_specs)
    extract_table_box.grid_configure(row=builtin_row_offset)
    normalize_box.grid_configure(row=builtin_row_offset + 1)
    type_box.grid_configure(row=builtin_row_offset + 2)
    filter_box.grid_configure(row=builtin_row_offset + 3)
    replace_box.grid_configure(row=builtin_row_offset + 4)
    generate_box.grid_configure(row=builtin_row_offset + 5)
    dropdup_box.grid_configure(row=builtin_row_offset + 6)
    validate_box.grid_remove()

    show_section(extract_table_settings, False)
    show_section(normalize_info, False)
    show_section(replace_settings, False)
    show_section(type_settings, False)
    show_section(dropdup_info, False)
    show_section(filter_settings, False)
    show_section(generate_settings, False)

    add_replace_row()
    add_filter_row()
    on_filter_mode_changed()
    add_generate_row()
    add_generate_row()
    add_validate_row()
    refresh_order_rows()

    bottom = ttk.Frame(root, padding=(10, 0, 10, 14), style="Storm.TFrame")
    bottom.grid(row=2, column=0, sticky="ew")
    bottom.grid_columnconfigure(0, weight=1)
    bottom.grid_columnconfigure(1, weight=0)
    bottom.grid_columnconfigure(2, weight=1)

    run_pipeline_button = ttk.Button(
        bottom,
        text="No File Selected",
        style="RunDisabled.TButton",
        state="disabled",
        command=run_pipeline
    )
    run_pipeline_button.grid(row=0, column=1, pady=(6, 0))
    update_run_pipeline_state()

    root.mainloop()
