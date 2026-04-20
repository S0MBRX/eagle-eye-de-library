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
        ValidateRequiredColumnsNode,
    )

    root = tk.Tk()
    root.title("EagleEyeDE Visualizer")
    root.geometry("500x500")
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

    style.configure("Small.TButton", padding=(6, 3))

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
    preview_table_state = {}
    preview_info_var = tk.StringVar(value="No preview loaded.")
    preview_selected_value_var = tk.StringVar(value="")
    preview_selected_entry = None

    processed_window = None
    processed_table_state = {}
    processed_selected_entry = None
    processed_selected_value_var = tk.StringVar(value="")
    processed_title_var = tk.StringVar(value="Processed Table")
    processed_diag_var = tk.StringVar(value="")
    processed_legend_var = tk.StringVar(
        value="Green = added cells | Orange = modified cells | Red = deleted cells"
    )

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

    def set_selected_cell_value(value_var, entry_widget, value, auto_select=False):
        value_var.set(str(value))
        if entry_widget is not None:
            entry_widget.focus_set()
            if auto_select:
                entry_widget.selection_range(0, tk.END)

    def create_canvas_table(parent, selected_value_var, selected_entry_getter):
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
            "selected_value_var": selected_value_var,
            "selected_entry_getter": selected_entry_getter,
            "tooltip": None,
            "last_render": None,
            "last_canvas_width": 0,
            "resize_job": None,
            "table_width_px": 0,
        }

        def on_inner_configure(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event):
            table_width = max(event.width, table_state.get("table_width_px", 0))
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

        canvas.update_idletasks()
        available_width = canvas.winfo_width()
        if available_width <= 1:
            available_width = canvas.winfo_reqwidth()
        if available_width <= 1:
            available_width = 900

        min_column_width_px = 120
        usable_width_px = max(1, available_width - 4)
        if len(columns) * min_column_width_px <= usable_width_px:
            column_width_px = max(min_column_width_px, int(usable_width_px / len(columns)))
        else:
            column_width_px = min_column_width_px

        table_width_px = max(usable_width_px, column_width_px * len(columns))
        wrap_width_px = max(90, column_width_px - 16)
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

        for col_index, column_name in enumerate(columns):
            header_color = header_bg
            if cell_colors is not None and (-1, column_name) in cell_colors:
                if cell_colors[(-1, column_name)] == "added":
                    header_color = added_bg
                elif cell_colors[(-1, column_name)] == "modified":
                    header_color = modified_bg
                elif cell_colors[(-1, column_name)] == "deleted":
                    header_color = deleted_bg

            header = tk.Label(
                inner,
                text=str(column_name),
                bg=header_color,
                fg="black",
                relief="solid",
                bd=1,
                anchor="w",
                padx=6,
                pady=4,
                font=("Arial", 9, "bold"),
                wraplength=wrap_width_px,
                width=max(10, int(column_width_px / 8)),
            )
            header.grid(row=0, column=col_index, sticky="nsew")
            inner.grid_columnconfigure(col_index, weight=1, minsize=column_width_px)

            if hover_old_values is not None and (-1, column_name) in hover_old_values:
                old_value = hover_old_values[(-1, column_name)]
                tip_text = f"Previous header: {old_value}"
                header.bind("<Enter>", lambda event, widget=header, text=tip_text: show_tooltip(widget, text))
                header.bind("<Leave>", lambda event: hide_tooltip())

        for row_index, (_, row) in enumerate(display_df.iterrows(), start=1):
            for col_index, column_name in enumerate(columns):
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

                cell = tk.Label(
                    inner,
                    text=cell_value,
                    bg=bg,
                    fg="black",
                    relief="solid",
                    bd=1,
                    anchor="w",
                    justify="left",
                    padx=6,
                    pady=4,
                    wraplength=wrap_width_px,
                    width=max(10, int(column_width_px / 8)),
                )
                cell.grid(row=row_index, column=col_index, sticky="nsew")

                def handle_click(event, value=cell_value, auto_select=False):
                    entry_widget = table_state["selected_entry_getter"]()
                    set_selected_cell_value(
                        table_state["selected_value_var"],
                        entry_widget,
                        value,
                        auto_select=auto_select
                    )

                cell.bind("<Button-1>", lambda event, value=cell_value: handle_click(event, value=value, auto_select=False))
                cell.bind("<Double-1>", lambda event, value=cell_value: handle_click(event, value=value, auto_select=True))

                hover_key = (row_index - 1, column_name)
                if hover_old_values is not None and hover_key in hover_old_values:
                    old_value = hover_old_values[hover_key]
                    tip_text = f"Previous value: {old_value}"
                    cell.bind("<Enter>", lambda event, widget=cell, text=tip_text: show_tooltip(widget, text))
                    cell.bind("<Leave>", lambda event: hide_tooltip())

        canvas.configure(scrollregion=canvas.bbox("all"))

    def ensure_preview_window():
        nonlocal preview_window, preview_selected_entry, preview_table_state

        if preview_window is not None and preview_window.winfo_exists():
            preview_window.title(get_input_filename())
            preview_window.lift()
            return

        preview_window = tk.Toplevel(root)
        preview_window.title(get_input_filename())
        preview_window.geometry("900x560")
        preview_window.configure(bg=storm_blue)

        preview_frame = ttk.Frame(preview_window, padding=10, style="Storm.TFrame")
        preview_frame.pack(fill="both", expand=True)

        ttk.Label(
            preview_frame,
            textvariable=preview_info_var,
            style="StormTop.TLabel"
        ).pack(anchor="w", pady=(0, 8))

        table_holder = ttk.Frame(preview_frame, style="Storm.TFrame")
        table_holder.pack(fill="both", expand=True)

        preview_table_state = create_canvas_table(
            table_holder,
            preview_selected_value_var,
            lambda: preview_selected_entry
        )

        selected_frame = ttk.Frame(preview_frame, style="Storm.TFrame")
        selected_frame.pack(fill="x", pady=(10, 0))

        ttk.Label(
            selected_frame,
            text="Selected Cell",
            style="StormTop.TLabel"
        ).pack(anchor="w", pady=(0, 4))

        preview_selected_entry = tk.Entry(selected_frame, textvariable=preview_selected_value_var)
        preview_selected_entry.pack(fill="x")

    def ensure_processed_window():
        nonlocal processed_window, processed_selected_entry, processed_table_state

        if processed_window is not None and processed_window.winfo_exists():
            processed_window.title(get_processed_output_filename())
            processed_window.lift()
            return

        processed_window = tk.Toplevel(root)
        processed_window.title(get_processed_output_filename())
        processed_window.geometry("1050x700")
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

        ttk.Label(
            processed_frame,
            textvariable=processed_legend_var,
            style="StormTop.TLabel",
            justify="left",
            wraplength=980
        ).pack(anchor="w", pady=(0, 8))

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

        processed_table_state = create_canvas_table(
            table_holder,
            processed_selected_value_var,
            lambda: processed_selected_entry
        )

        selected_frame = ttk.Frame(processed_frame, style="Storm.TFrame")
        selected_frame.pack(fill="x", pady=(10, 0))

        ttk.Label(
            selected_frame,
            text="Selected Cell",
            style="StormTop.TLabel"
        ).pack(anchor="w", pady=(0, 4))

        processed_selected_entry = tk.Entry(selected_frame, textvariable=processed_selected_value_var)
        processed_selected_entry.pack(fill="x")

    def build_raw_preview_dataframe():
        import pandas as pd

        input_path = input_var.get().strip()
        if not input_path:
            return None

        return pd.read_csv(input_path).head(50)

    def build_enabled_nodes():
        nodes = []

        if normalize_var.get():
            nodes.append({
                "name": "Normalize Columns",
                "node": NormalizeColumnsNode(),
                "meta": {},
            })

        if replace_var.get():
            replace_map = build_replace_map()
            if not replace_map:
                raise ValueError("Replace Values is enabled, but no replace pairs were provided.")
            nodes.append({
                "name": "Replace Values",
                "node": ReplaceValuesNode(replace_map),
                "meta": {
                    "replace_map": replace_map,
                },
            })

        if dropdup_var.get():
            nodes.append({
                "name": "Drop Duplicates",
                "node": DropDuplicatesNode(),
                "meta": {},
            })

        if filter_var.get():
            filter_cols = build_filter_columns()
            if not filter_cols:
                raise ValueError("Column Filter is enabled, but no columns were provided.")

            mode = filter_mode_var.get().strip().lower()
            if mode not in ("include", "exclude"):
                mode = "include"

            nodes.append({
                "name": "Column Filter",
                "node": ColumnFilterNode(filter_cols, Mode=mode),
                "meta": {
                    "filter_mode": mode,
                    "filter_columns": list(filter_cols),
                },
            })

        if validate_var.get():
            validate_cols = build_validate_columns()
            if not validate_cols:
                raise ValueError("Validate Required Columns is enabled, but no required columns were provided.")

            nodes.append({
                "name": "Validate Required Columns",
                "node": ValidateRequiredColumnsNode(validate_cols),
                "meta": {
                    "validate_columns": list(validate_cols),
                },
            })

        return nodes

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
                    operation_changes_value = not values_equal(cleaned_value, prev_value)

                    if cleaned_value in exact_keys:
                        replacement_value = clean_map[cleaned_value]
                        operation_changes_value = operation_changes_value or not values_equal(replacement_value, cleaned_value)
                    else:
                        loose_key = str(cleaned_value).strip()
                        if not has_exact_matches and loose_key in loose_map:
                            replacement_value = loose_map[loose_key]
                            operation_changes_value = operation_changes_value or not values_equal(replacement_value, cleaned_value)

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
            filter_columns = list(meta.get("filter_columns", []))

            if mode == "include":
                diff["deleted_columns"] = [col for col in prev_columns if col not in filter_columns]
            else:
                diff["deleted_columns"] = [col for col in filter_columns if col in prev_columns]

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
            f"Node: {step_name} | "
            f"Time: {duration_seconds:.3f}s | "
            f"Rows: {len(previous_df)} -> {len(previous_df)} | "
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
            f"Node: {step_name} | "
            f"Time: {duration_seconds:.3f}s | "
            f"Rows: {len(previous_df)} -> {len(current_df)} | "
            f"Columns: {len(previous_df.columns)} -> {len(current_df.columns)}"
        )

    def refresh_preview():
        try:
            ensure_preview_window()
            df = build_raw_preview_dataframe()
            if df is None:
                preview_info_var.set("No preview loaded.")
                preview_selected_value_var.set("")
                return

            preview_window.title(get_input_filename())
            preview_info_var.set(f"Previewing {len(df)} rows | {len(df.columns)} columns")
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

            ttk.Entry(row_frame, textvariable=row_data["from_var"]).grid(
                row=0, column=0, sticky="ew", padx=(0, 6)
            )
            ttk.Entry(row_frame, textvariable=row_data["to_var"]).grid(
                row=0, column=1, sticky="ew", padx=(0, 6)
            )

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

            ttk.Entry(row_frame, textvariable=row_data["value_var"]).grid(
                row=0, column=0, sticky="ew", padx=(0, 6)
            )

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

    def refresh_validate_rows():
        for child in validate_rows_frame.winfo_children():
            child.destroy()

        for row_index, row_data in enumerate(validate_rows):
            row_frame = ttk.Frame(validate_rows_frame, style="StormPanel.TFrame")
            row_frame.grid(row=row_index, column=0, sticky="ew", pady=2)
            row_frame.grid_columnconfigure(0, weight=1)

            ttk.Entry(row_frame, textvariable=row_data["value_var"]).grid(
                row=0, column=0, sticky="ew", padx=(0, 6)
            )

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
                "diagnostics": f"Node: Raw Input | Time: 0.000s | Rows: {len(Data)} -> {len(Data)} | Columns: {len(Data.columns)} -> {len(Data.columns)}"
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
    ttk.Button(top, text="Browse...", command=choose_input).grid(row=0, column=2, sticky="ew")

    main = ttk.Frame(root, padding=(10, 0, 10, 10), style="Storm.TFrame")
    main.grid(row=1, column=0, sticky="nsew")
    main.grid_rowconfigure(0, weight=1)
    main.grid_columnconfigure(0, weight=1)

    nodes_box = ttk.LabelFrame(main, text="Pipeline Nodes", padding=10, style="Storm.TLabelframe")
    nodes_box.grid(row=0, column=0, sticky="nsew")
    nodes_box.grid_columnconfigure(0, weight=1)

    node_row = 0

    normalize_box = ttk.Frame(nodes_box, style="StormPanel.TFrame")
    normalize_box.grid(row=node_row, column=0, sticky="ew", pady=(0, 6))
    normalize_box.grid_columnconfigure(0, weight=1)

    ttk.Checkbutton(
        normalize_box,
        text="Normalize Columns",
        variable=normalize_var,
        style="Storm.TCheckbutton",
        command=lambda: toggle_section(normalize_var, normalize_info)
    ).grid(row=0, column=0, sticky="w")

    normalize_info = ttk.Frame(normalize_box, padding=(24, 6, 0, 0), style="StormPanel.TFrame")
    normalize_info.grid(row=1, column=0, sticky="ew")
    ttk.Label(
        normalize_info,
        text="Standardizes column names by trimming spaces, converting to lowercase, and replacing spaces with underscores.",
        style="Storm.TLabel",
        wraplength=360,
        justify="left"
    ).grid(row=0, column=0, sticky="w")

    node_row += 1

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

    ttk.Label(
        replace_settings,
        text="Replaces matching values in the table using the find/replace pairs you add below.",
        style="Storm.TLabel",
        wraplength=360,
        justify="left"
    ).grid(row=0, column=0, sticky="w", pady=(0, 6))

    ttk.Label(replace_settings, text="Value To Find          Replace With", style="Storm.TLabel").grid(
        row=1, column=0, sticky="w", pady=(0, 4)
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
        text="Example: N/A        None",
        style="Storm.TLabel"
    ).grid(row=4, column=0, sticky="w", pady=(4, 0))

    node_row += 1

    dropdup_box = ttk.Frame(nodes_box, style="StormPanel.TFrame")
    dropdup_box.grid(row=node_row, column=0, sticky="ew", pady=(0, 6))
    dropdup_box.grid_columnconfigure(0, weight=1)

    ttk.Checkbutton(
        dropdup_box,
        text="Drop Duplicates",
        variable=dropdup_var,
        style="Storm.TCheckbutton",
        command=lambda: toggle_section(dropdup_var, dropdup_info)
    ).grid(row=0, column=0, sticky="w")

    dropdup_info = ttk.Frame(dropdup_box, padding=(24, 6, 0, 0), style="StormPanel.TFrame")
    dropdup_info.grid(row=1, column=0, sticky="ew")
    ttk.Label(
        dropdup_info,
        text="Removes duplicate rows from the table.",
        style="Storm.TLabel",
        wraplength=360,
        justify="left"
    ).grid(row=0, column=0, sticky="w")

    node_row += 1

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

    ttk.Label(
        filter_settings,
        text="Keeps only selected columns in include mode, or removes selected columns in exclude mode.",
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

    ttk.Label(filter_settings, text="Columns", style="Storm.TLabel").grid(row=3, column=0, sticky="w")

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
        text="Example: customer_name",
        style="Storm.TLabel"
    ).grid(row=6, column=0, sticky="w", pady=(4, 0))

    node_row += 1

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

    ttk.Label(
        validate_settings,
        text="Checks that the listed columns exist after the selected transformations are applied.",
        style="Storm.TLabel",
        wraplength=360,
        justify="left"
    ).grid(row=0, column=0, sticky="w", pady=(0, 6))

    ttk.Label(validate_settings, text="Required Columns", style="Storm.TLabel").grid(row=1, column=0, sticky="w")

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
        text="Example: email_address",
        style="Storm.TLabel"
    ).grid(row=4, column=0, sticky="w", pady=(4, 0))

    node_row += 1

    show_section(normalize_info, normalize_var.get())
    show_section(replace_settings, replace_var.get())
    show_section(dropdup_info, dropdup_var.get())
    show_section(filter_settings, filter_var.get())
    show_section(validate_settings, validate_var.get())

    add_replace_row()
    add_filter_row()
    add_validate_row()

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
