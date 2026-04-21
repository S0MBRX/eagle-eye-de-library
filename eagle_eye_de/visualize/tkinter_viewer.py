def LaunchVisualizer():
    import ast
    import os
    import time
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    from eagle_eye_de.nodes import (
        NormalizeColumnsNode,
        ReplaceValuesNode,
        DropDuplicatesNode,
        ColumnFilterNode,
        RowFilterNode,
        GenerateColumnNode,
        ValidateRequiredColumnsNode,
    )

    root = tk.Tk()
    root.title("EagleEyeDE Visualizer")
    root.geometry("540x620")
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
        "RunDisabled.TButton",
        font=("Arial", 18, "bold"),
        padding=(20, 10),
        background="#8B929C",
        foreground="#E6E6E6",
        borderwidth=0,
    )
    style.map(
        "RunDisabled.TButton",
        background=[("disabled", "#8B929C"), ("active", "#8B929C"), ("pressed", "#8B929C")],
        foreground=[("disabled", "#E6E6E6"), ("active", "#E6E6E6"), ("pressed", "#E6E6E6")],
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
    browse_pulse_positions = [0.0, 0.12, 0.26, 0.42, 0.6, 0.78, 1.0, 0.78, 0.6, 0.42, 0.26, 0.12]
    for pulse_index, pulse_position in enumerate(browse_pulse_positions):
        pulse_color = blend_hex(green, "#D9D9D9", pulse_position)
        style_name = f"BrowsePulse{pulse_index}.TButton"
        text_color = "white" if pulse_position < 0.6 else "black"
        style.configure(style_name, padding=(6, 3), background=pulse_color, foreground=text_color, borderwidth=0)
        style.map(style_name, background=[("active", pulse_color), ("pressed", pulse_color)])
        browse_pulse_styles.append(style_name)

    input_var = tk.StringVar()
    browse_button = None
    browse_pulse_index = 0
    run_pipeline_button = None

    normalize_var = tk.BooleanVar(value=True)
    replace_var = tk.BooleanVar(value=False)
    dropdup_var = tk.BooleanVar(value=False)
    filter_var = tk.BooleanVar(value=False)
    rowfilter_var = tk.BooleanVar(value=False)
    generate_var = tk.BooleanVar(value=False)
    validate_var = tk.BooleanVar(value=False)

    filter_mode_var = tk.StringVar(value="include")
    row_filter_mode_var = tk.StringVar(value="include")
    row_filter_condition_var = tk.StringVar(value="")
    generate_column_name_var = tk.StringVar(value="")
    generate_operator_var = tk.StringVar(value="+")

    replace_rows = []
    filter_rows = []
    generate_rows = []
    validate_rows = []
    operation_order = []
    customizing_order_index = None

    preview_window = None
    preview_table_state = {}
    preview_info_var = tk.StringVar(value="No preview loaded.")

    processed_window = None
    processed_table_state = {}
    processed_title_var = tk.StringVar(value="")
    processed_diag_var = tk.StringVar(value="")

    processed_steps = []
    processed_step_index = 0
    processed_play_job = None
    processed_is_playing = False

    def choose_input():
        path = filedialog.askopenfilename(
            title="Choose Input CSV",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if path:
            input_var.set(path)
            refresh_preview()

    def pulse_browse_button():
        nonlocal browse_pulse_index

        if browse_button is None:
            return

        if input_var.get().strip():
            browse_button.configure(style="Small.TButton")
            return

        browse_button.configure(style=browse_pulse_styles[browse_pulse_index])
        browse_pulse_index = (browse_pulse_index + 1) % len(browse_pulse_styles)
        root.after(180, pulse_browse_button)

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

    def toggle_settings(section_frame, button, label=None):
        visible = not section_frame.winfo_ismapped()
        show_section(section_frame, visible)
        symbol = "^" if visible else "v"
        if label is None:
            button.configure(text=symbol)
        else:
            button.configure(text=f"{label} {symbol}")

    def get_operation_summary(operation):
        name = operation["name"]
        meta = operation["meta"]

        if name == "Replace Values":
            return f"{len(meta.get('replace_map', {}))} pairs"
        if name == "Column Filter":
            values = meta.get("filter_values", meta.get("filter_columns", []))
            return f"{meta.get('filter_mode', 'include')} columns with {len(values)} values"
        if name == "Row Filter":
            values = meta.get("row_filter_values", [meta.get("condition", "")])
            return f"{meta.get('row_filter_mode', 'include')} rows with {len(values)} values"
        if name == "Generate Column":
            sources = ", ".join(meta.get("source_columns", []))
            return f"{meta.get('new_column', '')} = {sources}"
        if name == "Validate Required Columns":
            return f"{len(meta.get('validate_columns', []))} required"
        return ""

    def get_operation_config_lines(operation):
        name = operation["name"]
        meta = operation["meta"]

        if name == "Replace Values":
            return [f"{old} -> {new}" for old, new in meta.get("replace_map", {}).items()]
        if name == "Column Filter":
            values = meta.get("filter_values", meta.get("filter_columns", []))
            return [
                f"mode: {meta.get('filter_mode', 'include')}",
                f"values: {', '.join(values)}",
            ]
        if name == "Row Filter":
            values = meta.get("row_filter_values", [meta.get("condition", "")])
            return [
                f"mode: {meta.get('row_filter_mode', 'include')}",
                f"values: {', '.join(value for value in values if value)}",
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
            "Replace Values",
            "Column Filter",
            "Row Filter",
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

        if name == "Replace Values":
            return flash_row_widgets(replace_rows, "from_entry", "to_entry")
        if name == "Column Filter":
            return flash_row_widgets(filter_rows, "entry")
        if name == "Row Filter":
            flash_widget_red(row_filter_condition_entry)
            return True
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

        if name == "Column Filter":
            mode_var = tk.StringVar(value=meta.get("filter_mode", "include"))
            values_var = tk.StringVar(value=", ".join(meta.get("filter_values", meta.get("filter_columns", []))))

            ttk.Label(editor, text="mode", style="Storm.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=1)
            ttk.Combobox(editor, textvariable=mode_var, values=("include", "exclude"), state="readonly", width=10).grid(row=0, column=1, sticky="w", pady=1)
            ttk.Label(editor, text="values", style="Storm.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=1)
            ttk.Entry(editor, textvariable=values_var, width=28).grid(row=1, column=1, columnspan=3, sticky="ew", pady=1)

            def save_column_filter():
                values = split_entry_list(values_var.get())
                if not values:
                    messagebox.showerror("Missing Column Filter Config", "Column Filter needs at least one value.")
                    return

                mode = mode_var.get().strip().lower()
                if mode not in ("include", "exclude"):
                    mode = "include"

                save_order_item_meta(row_index, {"filter_mode": mode, "filter_values": values})

            return save_column_filter

        if name == "Row Filter":
            mode_var = tk.StringVar(value=meta.get("row_filter_mode", "include"))
            values_var = tk.StringVar(value=", ".join(meta.get("row_filter_values", [meta.get("condition", "")])))

            ttk.Label(editor, text="mode", style="Storm.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=1)
            ttk.Combobox(editor, textvariable=mode_var, values=("include", "exclude"), state="readonly", width=10).grid(row=0, column=1, sticky="w", pady=1)
            ttk.Label(editor, text="values", style="Storm.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=1)
            ttk.Entry(editor, textvariable=values_var, width=32).grid(row=1, column=1, columnspan=3, sticky="ew", pady=1)

            def save_row_filter():
                values = split_entry_list(values_var.get())
                if not values:
                    messagebox.showerror("Missing Row Filter Config", "Row Filter needs at least one value.")
                    return

                mode = mode_var.get().strip().lower()
                if mode not in ("include", "exclude"):
                    mode = "include"

                save_order_item_meta(row_index, {"row_filter_mode": mode, "row_filter_values": values})

            return save_row_filter

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

    def refresh_order_rows():
        for child in order_rows_frame.winfo_children():
            child.destroy()

        if not operation_order:
            ttk.Label(
                order_rows_frame,
                text="No nodes added.",
                style="Storm.TLabel"
            ).grid(row=0, column=0, sticky="w")
            return

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
                style="Storm.TLabel"
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
                    style="Storm.TLabel",
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
        except ValueError as error:
            set_settings_visible(name, True)
            root.update_idletasks()
            flash_missing_inputs(name)

    def set_settings_visible(name, visible):
        mapping = {
            "Normalize Columns": (lambda: normalize_info, lambda: normalize_toggle),
            "Replace Values": (lambda: replace_settings, lambda: replace_toggle),
            "Drop Duplicates": (lambda: dropdup_info, lambda: dropdup_toggle),
            "Column Filter": (lambda: filter_settings, lambda: filter_toggle),
            "Row Filter": (lambda: rowfilter_settings, lambda: rowfilter_toggle),
            "Generate Column": (lambda: generate_settings, lambda: generate_toggle),
            "Validate Required Columns": (lambda: validate_settings, lambda: validate_toggle),
        }

        if name not in mapping:
            return

        section_getter, button_getter = mapping[name]
        show_section(section_getter(), visible)
        button_getter().configure(text=f"{name} {'^' if visible else 'v'}")

    def clear_dynamic_rows(rows, refresh_callback):
        rows.clear()
        refresh_callback()

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

    def get_processed_output_path():
        input_path = input_var.get().strip()
        if not input_path:
            return None

        folder = os.path.dirname(input_path)
        filename = os.path.basename(input_path)
        stem, ext = os.path.splitext(filename)
        if not ext:
            ext = ".csv"
        return os.path.join(folder, f"Processed_{stem}{ext}")

    def get_processed_output_filename():
        output_path = get_processed_output_path()
        if not output_path:
            return "Processed Table"
        return os.path.basename(output_path)

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
        table_state["column_count"] = len(columns)

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

        table_width_px = max(1, sum(column_widths_px.values()))
        table_state["last_canvas_width"] = available_width
        table_state["table_width_px"] = table_width_px
        canvas.itemconfigure(table_state["window_id"], width=table_width_px)

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

        for col_index, column_name in enumerate(columns):
            current_column_width_px = column_widths_px[column_name]
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
            header.grid(row=0, column=col_index, sticky="nsew")
            inner.grid_columnconfigure(col_index, weight=0, minsize=current_column_width_px)

            if hover_old_values is not None and (-1, column_name) in hover_old_values:
                old_value = hover_old_values[(-1, column_name)]
                tip_text = f"Previous header: {old_value}"
                header.bind("<Enter>", lambda event, widget=header, text=tip_text: show_tooltip(widget, text))
                header.bind("<Leave>", lambda event: hide_tooltip())

        for row_index, (_, row) in enumerate(display_df.iterrows(), start=1):
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
                cell.grid(row=row_index, column=col_index, sticky="nsew")

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

    def ensure_processed_window():
        nonlocal processed_window, processed_table_state

        if processed_window is not None and processed_window.winfo_exists():
            processed_window.title(get_processed_output_filename())
            processed_window.lift()
            return

        if preview_window is None or not preview_window.winfo_exists():
            ensure_preview_window()

        processed_window = tk.Toplevel(root)
        processed_window.title(get_processed_output_filename())
        anchor_window = preview_window if preview_window is not None and preview_window.winfo_exists() else root
        place_window_right_of(processed_window, anchor_window, 1050, 700)
        processed_window.configure(bg=storm_blue)

        processed_frame = ttk.Frame(processed_window, padding=10, style="Storm.TFrame")
        processed_frame.pack(fill="both", expand=True)

        ttk.Label(
            processed_frame,
            textvariable=processed_title_var,
            style="StormTop.TLabel"
        ).pack(anchor="w", pady=(0, 6))

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

        controls_frame = ttk.Frame(processed_frame, style="Storm.TFrame")
        controls_frame.pack(fill="x", pady=(0, 8))

        ttk.Button(
            controls_frame,
            text="Previous",
            style="Small.TButton",
            command=show_previous_processed_step
        ).pack(side="left", padx=(0, 6))

        ttk.Button(
            controls_frame,
            text="Next",
            style="Small.TButton",
            command=show_next_processed_step
        ).pack(side="left", padx=(0, 6))

        table_holder = ttk.Frame(processed_frame, style="Storm.TFrame")
        table_holder.pack(fill="both", expand=True)

        processed_table_state = create_canvas_table(table_holder)

    def build_raw_preview_dataframe():
        import pandas as pd

        input_path = input_var.get().strip()
        if not input_path:
            return None

        return pd.read_csv(input_path).head(50)

    def build_operation_snapshot(name):
        if name == "Normalize Columns":
            return {
                "name": name,
                "meta": {},
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

        if name == "Drop Duplicates":
            return {
                "name": name,
                "meta": {},
            }

        if name == "Column Filter":
            filter_values = build_filter_columns()
            if not filter_values:
                raise ValueError("Column Filter needs at least one value before it can be added.")

            mode = filter_mode_var.get().strip().lower()
            if mode not in ("include", "exclude"):
                mode = "include"

            return {
                "name": name,
                "meta": {
                    "filter_mode": mode,
                    "filter_values": list(filter_values),
                },
            }

        if name == "Row Filter":
            values = split_entry_list(row_filter_condition_var.get())
            if not values:
                raise ValueError("Row Filter needs at least one value before it can be added.")
            mode = row_filter_mode_var.get().strip().lower()
            if mode not in ("include", "exclude"):
                mode = "include"

            return {
                "name": name,
                "meta": {
                    "row_filter_mode": mode,
                    "row_filter_values": values,
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

        if name == "Normalize Columns":
            node = NormalizeColumnsNode()
        elif name == "Replace Values":
            node = ReplaceValuesNode(meta["replace_map"])
        elif name == "Drop Duplicates":
            node = DropDuplicatesNode()
        elif name == "Column Filter":
            node = ColumnFilterNode(Mode=meta["filter_mode"], MatchValues=meta.get("filter_values", meta.get("filter_columns", [])))
        elif name == "Row Filter":
            node = RowFilterNode(Mode=meta.get("row_filter_mode", "include"), MatchValues=meta.get("row_filter_values", [meta.get("condition", "")]))
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
        }

        if step_name == "Normalize Columns":
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

        if step_name == "Drop Duplicates":
            if len(prev) > len(curr):
                diff["deleted_rows"] = set(
                    prev.index[prev.duplicated(keep="first")].tolist()
                )
            elif len(curr) > len(prev):
                diff["added_rows"] = set(range(len(prev), len(curr)))
            return diff

        if step_name == "Column Filter":
            mode = meta.get("filter_mode", "include")
            filter_values = {str(value).strip().lower() for value in meta.get("filter_values", meta.get("filter_columns", []))}
            matching_columns = []

            for column_name in prev_columns:
                column_values = set(prev[column_name].map(lambda value: str(value).strip().lower()).tolist())
                column_values.add(str(column_name).strip().lower())
                if column_values.intersection(filter_values):
                    matching_columns.append(column_name)

            if mode == "include":
                diff["deleted_columns"] = [col for col in prev_columns if col not in matching_columns]
            else:
                diff["deleted_columns"] = matching_columns

            return diff

        if step_name == "Row Filter":
            values = {str(value).strip().lower() for value in meta.get("row_filter_values", [meta.get("condition", "")]) if str(value).strip()}
            if values:
                matching_labels = set(
                    previous_df[
                        previous_df.apply(
                            lambda row: bool(
                                {str(value).strip().lower() for value in row.tolist()}.intersection(values)
                            ),
                            axis=1
                        )
                    ].index.tolist()
                )
                mode = meta.get("row_filter_mode", "include")
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
        processed_window.title(get_processed_output_filename())
        processed_title_var.set(f"{step['name']} ({processed_step_index + 1}/{len(processed_steps)})")
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

    def play_processed_step():
        nonlocal processed_play_job, processed_is_playing, processed_step_index

        if not processed_is_playing or not processed_steps:
            return

        render_processed_step()

        if processed_step_index >= len(processed_steps) - 1:
            processed_is_playing = False
            processed_play_job = None
            return

        total_duration_ms = 1000
        step_delay = max(80, int(total_duration_ms / max(1, len(processed_steps) - 1)))

        processed_step_index += 1
        processed_play_job = processed_window.after(step_delay, play_processed_step)

    def autoplay_processed_steps():
        nonlocal processed_is_playing, processed_step_index

        if not processed_steps:
            return

        stop_processed_playback()
        processed_step_index = 0
        processed_is_playing = True
        play_processed_step()

    def show_previous_processed_step():
        nonlocal processed_step_index

        if not processed_steps:
            return

        stop_processed_playback()

        if processed_step_index > 0:
            processed_step_index -= 1
            render_processed_step()

    def show_next_processed_step():
        nonlocal processed_step_index

        if not processed_steps:
            return

        stop_processed_playback()

        if processed_step_index < len(processed_steps) - 1:
            processed_step_index += 1
            render_processed_step()

    def on_filter_mode_changed(event=None):
        return

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
        row_data = {
            "from_var": tk.StringVar(value=from_value),
            "to_var": tk.StringVar(value=to_value),
        }
        replace_rows.append(row_data)
        refresh_replace_rows()

    def delete_replace_row(index):
        if 0 <= index < len(replace_rows):
            del replace_rows[index]

        if not replace_rows:
            add_replace_row()
        else:
            refresh_replace_rows()

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
        row_data = {
            "value_var": tk.StringVar(value=value),
        }
        filter_rows.append(row_data)
        refresh_filter_rows()

    def delete_filter_row(index):
        if 0 <= index < len(filter_rows):
            del filter_rows[index]

        if not filter_rows:
            add_filter_row()
        else:
            refresh_filter_rows()

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
        row_data = {
            "value_var": tk.StringVar(value=value),
        }
        generate_rows.append(row_data)
        refresh_generate_rows()

    def delete_generate_row(index):
        if 0 <= index < len(generate_rows):
            del generate_rows[index]

        if not generate_rows:
            add_generate_row()
        else:
            refresh_generate_rows()

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
        row_data = {
            "value_var": tk.StringVar(value=value),
        }
        validate_rows.append(row_data)
        refresh_validate_rows()

    def delete_validate_row(index):
        if 0 <= index < len(validate_rows):
            del validate_rows[index]

        if not validate_rows:
            add_validate_row()
        else:
            refresh_validate_rows()

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

            output_path = get_processed_output_path()
            if not output_path:
                messagebox.showerror("Missing Input", "Please choose an input CSV file.")
                return

            Data = pd.read_csv(input_path)

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

                current_df = Data.copy()
                diff = build_step_diff(step_name, previous_df, current_df, meta)

                if diff["deleted_rows"] or diff["deleted_columns"]:
                    steps.append(
                        build_deletion_preview_step(step_name, previous_df, diff, duration_seconds)
                    )

                cell_colors = build_final_step_cell_colors(current_df, diff, max_rows=100)
                diagnostics = build_step_diagnostics(step_name, previous_df, current_df, duration_seconds)

                steps.append({
                    "name": step_name,
                    "data": current_df,
                    "display_df": current_df.reset_index(drop=True).head(100).copy(),
                    "cell_colors": cell_colors,
                    "hover_old_values": diff["modified_old_values"],
                    "diagnostics": diagnostics,
                })

            Data.to_csv(output_path, index=False)

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

    global_canvas = tk.Canvas(main, bg=storm_blue, highlightthickness=0, bd=0)
    global_canvas.grid(row=0, column=0, sticky="nsew")
    global_scrollbar = ttk.Scrollbar(main, orient="vertical", command=global_canvas.yview)
    global_scrollbar.grid(row=0, column=1, sticky="ns")
    global_canvas.configure(yscrollcommand=global_scrollbar.set)

    global_content = ttk.Frame(global_canvas, style="Storm.TFrame")
    global_window_id = global_canvas.create_window((0, 0), window=global_content, anchor="nw")
    global_content.grid_columnconfigure(0, weight=1)
    global_content.grid_rowconfigure(1, weight=1)

    def on_global_content_configure(event=None):
        global_canvas.configure(scrollregion=global_canvas.bbox("all"))

    def on_global_canvas_configure(event):
        global_canvas.itemconfigure(global_window_id, width=event.width)

    global_content.bind("<Configure>", on_global_content_configure)
    global_canvas.bind("<Configure>", on_global_canvas_configure)

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
        return global_canvas

    def can_scroll_canvas(canvas, units):
        top, bottom = canvas.yview()
        if units < 0:
            return top > 0.0
        return bottom < 1.0

    def scroll_canvas_from_wheel(event):
        widget = root.winfo_containing(event.x_root, event.y_root)
        canvas = find_scroll_canvas(widget, event.x_root, event.y_root)
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
    register_scroll_target(global_canvas, main, global_content)

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

        return section_content

    order_rows_frame = create_scrollable_section(global_content, "Run Order", 0, 135)
    nodes_box = create_scrollable_section(global_content, "Pipeline Nodes", 1, 260, row_weight=1)

    node_row = 0

    normalize_box = ttk.Frame(nodes_box, style="StormPanel.TFrame")
    normalize_box.grid(row=node_row, column=0, sticky="ew", pady=(0, 6))
    normalize_box.grid_columnconfigure(0, weight=1)

    normalize_header = ttk.Frame(normalize_box, style="StormPanel.TFrame")
    normalize_header.grid(row=0, column=0, sticky="ew")
    normalize_header.grid_columnconfigure(1, weight=1)
    ttk.Button(
        normalize_header,
        text="+",
        width=4,
        style="Add.TButton",
        command=lambda: add_order_item("Normalize Columns")
    ).grid(row=0, column=0, sticky="w", padx=(0, 6))
    normalize_toggle = ttk.Button(normalize_header, text="Normalize Columns v", style="NodeToggle.TButton")
    normalize_toggle.grid(row=0, column=1, sticky="ew")
    normalize_toggle.configure(command=lambda: toggle_settings(normalize_info, normalize_toggle, "Normalize Columns"))

    normalize_info = ttk.Frame(normalize_box, padding=(24, 6, 0, 0), style="StormPanel.TFrame")
    normalize_info.grid(row=1, column=0, sticky="ew")
    ttk.Label(
        normalize_info,
        text="Renames every column into a clean format: trim spaces, lowercase text, and change spaces to underscores.",
        style="Storm.TLabel",
        wraplength=360,
        justify="left"
    ).grid(row=0, column=0, sticky="w")

    node_row += 1

    replace_box = ttk.Frame(nodes_box, style="StormPanel.TFrame")
    replace_box.grid(row=node_row, column=0, sticky="ew", pady=(0, 6))
    replace_box.grid_columnconfigure(0, weight=1)

    replace_header = ttk.Frame(replace_box, style="StormPanel.TFrame")
    replace_header.grid(row=0, column=0, sticky="ew")
    replace_header.grid_columnconfigure(1, weight=1)
    ttk.Button(
        replace_header,
        text="+",
        width=4,
        style="Add.TButton",
        command=lambda: add_order_item("Replace Values"),
    ).grid(row=0, column=0, sticky="w", padx=(0, 6))
    replace_toggle = ttk.Button(replace_header, text="Replace Values v", style="NodeToggle.TButton")
    replace_toggle.grid(row=0, column=1, sticky="ew")
    replace_toggle.configure(command=lambda: toggle_settings(replace_settings, replace_toggle, "Replace Values"))

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

    ttk.Label(
        replace_settings,
        text="Example: UNKNOWN -> Unknown",
        style="Storm.TLabel"
    ).grid(row=4, column=0, sticky="w", pady=(4, 0))

    node_row += 1

    dropdup_box = ttk.Frame(nodes_box, style="StormPanel.TFrame")
    dropdup_box.grid(row=node_row, column=0, sticky="ew", pady=(0, 6))
    dropdup_box.grid_columnconfigure(0, weight=1)

    dropdup_header = ttk.Frame(dropdup_box, style="StormPanel.TFrame")
    dropdup_header.grid(row=0, column=0, sticky="ew")
    dropdup_header.grid_columnconfigure(1, weight=1)
    ttk.Button(
        dropdup_header,
        text="+",
        width=4,
        style="Add.TButton",
        command=lambda: add_order_item("Drop Duplicates")
    ).grid(row=0, column=0, sticky="w", padx=(0, 6))
    dropdup_toggle = ttk.Button(dropdup_header, text="Drop Duplicates v", style="NodeToggle.TButton")
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
    ttk.Button(
        filter_header,
        text="+",
        width=4,
        style="Add.TButton",
        command=lambda: add_order_item("Column Filter"),
    ).grid(row=0, column=0, sticky="w", padx=(0, 6))
    filter_toggle = ttk.Button(filter_header, text="Column Filter v", style="NodeToggle.TButton")
    filter_toggle.grid(row=0, column=1, sticky="ew")
    filter_toggle.configure(command=lambda: toggle_settings(filter_settings, filter_toggle, "Column Filter"))

    filter_settings = ttk.Frame(filter_box, padding=(24, 6, 0, 0), style="StormPanel.TFrame")
    filter_settings.grid(row=1, column=0, sticky="ew")
    filter_settings.grid_columnconfigure(0, weight=1)

    ttk.Label(
        filter_settings,
        text="Include: keep columns with value X. Exclude: remove columns with value X.",
        style="Storm.TLabel",
        wraplength=360,
        justify="left"
    ).grid(row=0, column=0, sticky="w", pady=(0, 6))

    ttk.Label(filter_settings, text="Mode", style="Storm.TLabel").grid(row=1, column=0, sticky="w")

    filter_mode_combo = ttk.Combobox(
        filter_settings,
        textvariable=filter_mode_var,
        values=["include", "exclude"],
        state="readonly",
        width=14
    )
    filter_mode_combo.grid(row=2, column=0, sticky="w", pady=(2, 6))
    filter_mode_combo.bind("<<ComboboxSelected>>", on_filter_mode_changed)

    ttk.Label(filter_settings, text="Value", style="Storm.TLabel").grid(row=3, column=0, sticky="w")

    filter_rows_frame = ttk.Frame(filter_settings, style="StormPanel.TFrame")
    filter_rows_frame.grid(row=4, column=0, sticky="ew")
    filter_rows_frame.grid_columnconfigure(0, weight=1)

    ttk.Button(
        filter_settings,
        text="+ Add Row",
        style="Small.TButton",
        command=add_filter_row
    ).grid(row=5, column=0, sticky="w", pady=(6, 0))

    ttk.Label(
        filter_settings,
        text="Example: UNKNOWN",
        style="Storm.TLabel"
    ).grid(row=6, column=0, sticky="w", pady=(4, 0))

    node_row += 1

    rowfilter_box = ttk.Frame(nodes_box, style="StormPanel.TFrame")
    rowfilter_box.grid(row=node_row, column=0, sticky="ew", pady=(0, 6))
    rowfilter_box.grid_columnconfigure(0, weight=1)

    rowfilter_header = ttk.Frame(rowfilter_box, style="StormPanel.TFrame")
    rowfilter_header.grid(row=0, column=0, sticky="ew")
    rowfilter_header.grid_columnconfigure(1, weight=1)
    ttk.Button(
        rowfilter_header,
        text="+",
        width=4,
        style="Add.TButton",
        command=lambda: add_order_item("Row Filter"),
    ).grid(row=0, column=0, sticky="w", padx=(0, 6))
    rowfilter_toggle = ttk.Button(rowfilter_header, text="Row Filter v", style="NodeToggle.TButton")
    rowfilter_toggle.grid(row=0, column=1, sticky="ew")
    rowfilter_toggle.configure(command=lambda: toggle_settings(rowfilter_settings, rowfilter_toggle, "Row Filter"))

    rowfilter_settings = ttk.Frame(rowfilter_box, padding=(24, 6, 0, 0), style="StormPanel.TFrame")
    rowfilter_settings.grid(row=1, column=0, sticky="ew")
    rowfilter_settings.grid_columnconfigure(0, weight=1)

    ttk.Label(
        rowfilter_settings,
        text="Include: keep rows with value X. Exclude: remove rows with value X.",
        style="Storm.TLabel",
        wraplength=360,
        justify="left"
    ).grid(row=0, column=0, sticky="w", pady=(0, 6))

    ttk.Label(rowfilter_settings, text="Mode", style="Storm.TLabel").grid(row=1, column=0, sticky="w")
    row_filter_mode_combo = ttk.Combobox(
        rowfilter_settings,
        textvariable=row_filter_mode_var,
        values=["include", "exclude"],
        state="readonly",
        width=14
    )
    row_filter_mode_combo.grid(row=2, column=0, sticky="w", pady=(2, 6))

    ttk.Label(rowfilter_settings, text="Value", style="Storm.TLabel").grid(row=3, column=0, sticky="w")
    row_filter_condition_entry = ttk.Entry(rowfilter_settings, textvariable=row_filter_condition_var)
    row_filter_condition_entry.grid(row=4, column=0, sticky="ew", pady=(2, 0))
    ttk.Label(
        rowfilter_settings,
        text="Example: UNKNOWN",
        style="Storm.TLabel"
    ).grid(row=5, column=0, sticky="w", pady=(4, 0))

    node_row += 1

    generate_box = ttk.Frame(nodes_box, style="StormPanel.TFrame")
    generate_box.grid(row=node_row, column=0, sticky="ew", pady=(0, 6))
    generate_box.grid_columnconfigure(0, weight=1)

    generate_header = ttk.Frame(generate_box, style="StormPanel.TFrame")
    generate_header.grid(row=0, column=0, sticky="ew")
    generate_header.grid_columnconfigure(1, weight=1)
    ttk.Button(
        generate_header,
        text="+",
        width=4,
        style="Add.TButton",
        command=lambda: add_order_item("Generate Column"),
    ).grid(row=0, column=0, sticky="w", padx=(0, 6))
    generate_toggle = ttk.Button(generate_header, text="Generate Column v", style="NodeToggle.TButton")
    generate_toggle.grid(row=0, column=1, sticky="ew")
    generate_toggle.configure(command=lambda: toggle_settings(generate_settings, generate_toggle, "Generate Column"))

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

    ttk.Label(generate_settings, text="New column name", style="Storm.TLabel").grid(row=1, column=0, sticky="w")
    generate_column_name_entry = ttk.Entry(generate_settings, textvariable=generate_column_name_var)
    generate_column_name_entry.grid(row=2, column=0, sticky="ew", pady=(2, 6))

    ttk.Label(generate_settings, text="Operator to apply", style="Storm.TLabel").grid(row=3, column=0, sticky="w")
    generate_operator_combo = ttk.Combobox(
        generate_settings,
        textvariable=generate_operator_var,
        values=["+", "-", "*", "/"],
        state="readonly",
        width=6
    )
    generate_operator_combo.grid(row=4, column=0, sticky="w", pady=(2, 6))

    ttk.Label(generate_settings, text="Existing columns to combine", style="Storm.TLabel").grid(row=5, column=0, sticky="w")

    generate_rows_frame = ttk.Frame(generate_settings, style="StormPanel.TFrame")
    generate_rows_frame.grid(row=6, column=0, sticky="ew")
    generate_rows_frame.grid_columnconfigure(0, weight=1)

    ttk.Button(
        generate_settings,
        text="+ Add Row",
        style="Small.TButton",
        command=add_generate_row
    ).grid(row=7, column=0, sticky="w", pady=(6, 0))

    ttk.Label(
        generate_settings,
        text="Example: unit_price, quantity with * creates unit_price * quantity",
        style="Storm.TLabel"
    ).grid(row=8, column=0, sticky="w", pady=(4, 0))

    node_row += 1

    validate_box = ttk.Frame(nodes_box, style="StormPanel.TFrame")
    validate_box.grid(row=node_row, column=0, sticky="ew", pady=(0, 6))
    validate_box.grid_columnconfigure(0, weight=1)

    validate_header = ttk.Frame(validate_box, style="StormPanel.TFrame")
    validate_header.grid(row=0, column=0, sticky="ew")
    validate_header.grid_columnconfigure(1, weight=1)
    ttk.Button(
        validate_header,
        text="+",
        width=4,
        style="Add.TButton",
        command=lambda: add_order_item("Validate Required Columns"),
    ).grid(row=0, column=0, sticky="w", padx=(0, 6))
    validate_toggle = ttk.Button(validate_header, text="Validate Required Columns v", style="NodeToggle.TButton")
    validate_toggle.grid(row=0, column=1, sticky="ew")
    validate_toggle.configure(command=lambda: toggle_settings(validate_settings, validate_toggle, "Validate Required Columns"))

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

    ttk.Label(
        validate_settings,
        text="Example: customer_name",
        style="Storm.TLabel"
    ).grid(row=4, column=0, sticky="w", pady=(4, 0))

    node_row += 1

    show_section(normalize_info, False)
    show_section(replace_settings, False)
    show_section(dropdup_info, False)
    show_section(filter_settings, False)
    show_section(rowfilter_settings, False)
    show_section(generate_settings, False)
    show_section(validate_settings, False)

    add_replace_row()
    add_filter_row()
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
