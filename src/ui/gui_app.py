"""
DDA GUI Application - Enhanced with column selection, SQL preview, and data grid
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from typing import Dict, Any, List, Optional
import logging
from pathlib import Path

from ..tools.name_generator import NameRandomizer
from ..core.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class DDAApplication:
    """Main GUI Application with enhanced features."""

    def __init__(self, root):
        self.root = root
        self.root.title("DDA Toolkit - Database Development Assistant")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)

        # Theme colors
        self.themes = {
            'dark': {
                'bg': '#1e1e1e',
                'fg': '#ffffff',
                'secondary_bg': '#2d2d2d',
                'tertiary_bg': '#3d3d3d',
                'accent': '#2196F3',
                'accent_hover': '#1976D2',
                'border': '#404040',
                'text_secondary': '#b0b0b0',
                'success': '#4CAF50',
                'warning': '#FF9800',
                'error': '#F44336',
                'grid_bg': '#2d2d2d',
                'grid_fg': '#ffffff'
            },
            'light': {
                'bg': '#f5f5f5',
                'fg': '#212121',
                'secondary_bg': '#ffffff',
                'tertiary_bg': '#e0e0e0',
                'accent': '#2196F3',
                'accent_hover': '#1976D2',
                'border': '#d0d0d0',
                'text_secondary': '#757575',
                'success': '#4CAF50',
                'warning': '#FF9800',
                'error': '#F44336',
                'grid_bg': '#ffffff',
                'grid_fg': '#212121'
            }
        }

        self.current_theme = 'dark'
        self.colors = self.themes[self.current_theme]

        # Configure root
        self.root.configure(bg=self.colors['bg'])

        # Variables
        self.db_manager = None
        self.name_randomizer = None

        # Connection variables
        self.host_var = tk.StringVar(value='localhost')
        self.port_var = tk.StringVar(value='3306')
        self.user_var = tk.StringVar(value='root')
        self.password_var = tk.StringVar()
        self.database_var = tk.StringVar()

        # Tool variables
        self.selected_table = tk.StringVar()
        self.gender_column_var = tk.StringVar()
        self.name_columns_listvar = tk.StringVar()
        self.target_gender = tk.StringVar(value='both')

        # Available columns
        self.available_columns = []

        # Data storage
        self.current_table_data = []

        # Build UI
        self._create_ui()
        self._configure_ttk_style()

    def _configure_ttk_style(self):
        """Configure ttk widget styles."""
        style = ttk.Style()

        # Configure Treeview
        style.configure(
            "Custom.Treeview",
            background=self.colors['grid_bg'],
            foreground=self.colors['grid_fg'],
            fieldbackground=self.colors['grid_bg'],
            borderwidth=0
        )

        style.configure(
            "Custom.Treeview.Heading",
            background=self.colors['tertiary_bg'],
            foreground=self.colors['fg'],
            borderwidth=1,
            relief='flat'
        )

        style.map('Custom.Treeview',
                 background=[('selected', self.colors['accent'])])

    def _create_ui(self):
        """Create the user interface."""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg'], padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        self._create_header(main_frame)

        # Content area - 3 column layout
        content_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, pady=15)

        # Left column - Connection & Table
        left_frame = tk.Frame(content_frame, bg=self.colors['bg'], width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        left_frame.pack_propagate(False)

        self._create_connection_panel(left_frame)
        self._create_table_selection_panel(left_frame)

        # Middle column - Data Grid & SQL Preview
        middle_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8)

        self._create_data_grid_panel(middle_frame)
        self._create_sql_preview_panel(middle_frame)

        # Right column - Configuration & Actions
        right_frame = tk.Frame(content_frame, bg=self.colors['bg'], width=320)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))
        right_frame.pack_propagate(False)

        self._create_column_selection_panel(right_frame)
        self._create_name_config_panel(right_frame)
        self._create_action_panel(right_frame)

        # Footer - Status & Logs
        self._create_footer(main_frame)

    def _create_header(self, parent):
        """Create header with title and theme toggle."""
        header_frame = tk.Frame(parent, bg=self.colors['bg'], height=50)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)

        # Title
        title_label = tk.Label(
            header_frame,
            text="⚡ DDA Toolkit",
            font=('Segoe UI', 22, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['bg']
        )
        title_label.pack(side=tk.LEFT, pady=5)

        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="Name Randomizer - MySQL Development Assistant",
            font=('Segoe UI', 10),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg']
        )
        subtitle_label.pack(side=tk.LEFT, padx=(12, 0), pady=5)

        # Theme toggle
        theme_btn = tk.Button(
            header_frame,
            text="🌙" if self.current_theme == 'dark' else "☀",
            font=('Segoe UI', 13),
            command=self._toggle_theme,
            bg=self.colors['secondary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            padx=8,
            pady=4,
            cursor='hand2',
            borderwidth=0
        )
        theme_btn.pack(side=tk.RIGHT, pady=5)

    def _create_panel(self, parent, title, height=None):
        """Create a styled panel."""
        panel_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT)

        if height:
            panel_frame.config(height=height)

        panel_frame.pack(fill=tk.BOTH, expand=(height is None), pady=(0, 10))

        # Panel header
        header = tk.Frame(panel_frame, bg=self.colors['tertiary_bg'], height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text=title,
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['tertiary_bg']
        )
        title_label.pack(side=tk.LEFT, padx=12, pady=6)

        # Panel content
        content = tk.Frame(panel_frame, bg=self.colors['secondary_bg'], padx=12, pady=12)
        content.pack(fill=tk.BOTH, expand=True)

        return content

    def _create_connection_panel(self, parent):
        """Create database connection panel."""
        content = self._create_panel(parent, "📊 Database Connection")

        # Connection inputs
        fields = [
            ("Host:", self.host_var, None),
            ("Port:", self.port_var, None),
            ("User:", self.user_var, None),
            ("Password:", self.password_var, '*'),
            ("Database:", self.database_var, None),
        ]

        for i, (label, var, show) in enumerate(fields):
            self._create_input(content, label, var, i, show)

        # Connect button
        btn_frame = tk.Frame(content, bg=self.colors['secondary_bg'])
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=(8, 0))

        connect_btn = tk.Button(
            btn_frame,
            text="Connect & Load Tables",
            command=self._test_connection,
            bg=self.colors['accent'],
            fg='white',
            font=('Segoe UI', 9, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=6,
            cursor='hand2',
            borderwidth=0
        )
        connect_btn.pack()

    def _create_input(self, parent, label, variable, row, show=None):
        """Create input field with label."""
        label_widget = tk.Label(
            parent,
            text=label,
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg'],
            anchor='w'
        )
        label_widget.grid(row=row, column=0, sticky='w', pady=4)

        entry = tk.Entry(
            parent,
            textvariable=variable,
            font=('Segoe UI', 9),
            bg=self.colors['tertiary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            insertbackground=self.colors['fg'],
            bd=1,
            highlightthickness=1,
            highlightbackground=self.colors['border'],
            highlightcolor=self.colors['accent']
        )
        if show:
            entry.config(show=show)

        entry.grid(row=row, column=1, sticky='ew', pady=4, padx=(8, 0))
        parent.grid_columnconfigure(1, weight=1)

    def _create_table_selection_panel(self, parent):
        """Create table selection panel."""
        content = self._create_panel(parent, "📋 Table Selection")

        # Table dropdown
        tk.Label(
            content,
            text="Table:",
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        self.table_combo = ttk.Combobox(
            content,
            textvariable=self.selected_table,
            state='readonly',
            font=('Segoe UI', 9)
        )
        self.table_combo.pack(fill=tk.X, pady=(0, 8))
        self.table_combo.bind('<<ComboboxSelected>>', self._on_table_selected)

        # Refresh button
        refresh_btn = tk.Button(
            content,
            text="🔄 Refresh Data (Top 10)",
            command=self._refresh_table_data,
            bg=self.colors['tertiary_bg'],
            fg=self.colors['fg'],
            font=('Segoe UI', 9),
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor='hand2',
            borderwidth=0
        )
        refresh_btn.pack(fill=tk.X, pady=(0, 8))

        # Row count
        self.row_count_label = tk.Label(
            content,
            text="Rows: -",
            font=('Segoe UI', 9),
            fg=self.colors['text_secondary'],
            bg=self.colors['secondary_bg'],
            anchor='w'
        )
        self.row_count_label.pack(anchor='w')

    def _create_data_grid_panel(self, parent):
        """Create data grid panel showing top 10 rows."""
        content = self._create_panel(parent, "📊 Table Data (Top 10 Rows)", height=300)

        # Create Treeview with scrollbars
        tree_frame = tk.Frame(content, bg=self.colors['secondary_bg'])
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        self.data_tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            style="Custom.Treeview",
            selectmode='browse'
        )

        vsb.config(command=self.data_tree.yview)
        hsb.config(command=self.data_tree.xview)

        # Grid layout
        self.data_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

    def _create_sql_preview_panel(self, parent):
        """Create SQL preview panel."""
        content = self._create_panel(parent, "🔍 SQL Preview", height=150)

        self.sql_preview = scrolledtext.ScrolledText(
            content,
            height=6,
            font=('Courier New', 9),
            bg=self.colors['tertiary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            wrap=tk.WORD,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=self.colors['border']
        )
        self.sql_preview.pack(fill=tk.BOTH, expand=True)

        # Insert placeholder
        self.sql_preview.insert(1.0, "-- SQL UPDATE statement will appear here after configuration\n-- Example: UPDATE `employees` SET `first_name` = 'NewName' WHERE `gender` = 'female'")
        self.sql_preview.config(state='disabled')

    def _create_column_selection_panel(self, parent):
        """Create column selection panel."""
        content = self._create_panel(parent, "🎯 Column Selection")

        # Gender column
        tk.Label(
            content,
            text="Gender Column:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        self.gender_column_combo = ttk.Combobox(
            content,
            textvariable=self.gender_column_var,
            state='readonly',
            font=('Segoe UI', 9)
        )
        self.gender_column_combo.pack(fill=tk.X, pady=(0, 12))
        self.gender_column_combo.bind('<<ComboboxSelected>>', self._update_sql_preview)

        # Name columns
        tk.Label(
            content,
            text="Name Columns (select multiple):",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        # Listbox for multiple selection
        listbox_frame = tk.Frame(content, bg=self.colors['secondary_bg'])
        listbox_frame.pack(fill=tk.X, pady=(0, 8))

        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.name_columns_listbox = tk.Listbox(
            listbox_frame,
            listvariable=self.name_columns_listvar,
            selectmode=tk.MULTIPLE,
            font=('Segoe UI', 9),
            bg=self.colors['tertiary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            height=5,
            yscrollcommand=scrollbar.set,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=self.colors['border'],
            selectbackground=self.colors['accent']
        )
        self.name_columns_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.name_columns_listbox.bind('<<ListboxSelect>>', self._update_sql_preview)

        scrollbar.config(command=self.name_columns_listbox.yview)

    def _create_name_config_panel(self, parent):
        """Create name configuration panel."""
        content = self._create_panel(parent, "⚙ Name Configuration")

        # Gender selection
        tk.Label(
            content,
            text="Target Gender:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        gender_frame = tk.Frame(content, bg=self.colors['secondary_bg'])
        gender_frame.pack(fill=tk.X, pady=(0, 12))

        for gender in ['male', 'female', 'both']:
            rb = tk.Radiobutton(
                gender_frame,
                text=gender.capitalize(),
                variable=self.target_gender,
                value=gender,
                font=('Segoe UI', 9),
                fg=self.colors['fg'],
                bg=self.colors['secondary_bg'],
                selectcolor=self.colors['tertiary_bg'],
                activebackground=self.colors['secondary_bg'],
                command=self._update_sql_preview
            )
            rb.pack(side=tk.LEFT, padx=(0, 15))

        # Name groups
        tk.Label(
            content,
            text="Name Groups:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        self.group_vars = {}
        for group in ['English', 'Arabic', 'Asian', 'African', 'All']:
            var = tk.BooleanVar(value=(group == 'All'))
            self.group_vars[group] = var

            cb = tk.Checkbutton(
                content,
                text=group,
                variable=var,
                font=('Segoe UI', 9),
                fg=self.colors['fg'],
                bg=self.colors['secondary_bg'],
                selectcolor=self.colors['tertiary_bg'],
                activebackground=self.colors['secondary_bg'],
                command=self._update_sql_preview
            )
            cb.pack(anchor='w', pady=2)

    def _create_action_panel(self, parent):
        """Create action buttons panel."""
        content = self._create_panel(parent, "🚀 Actions")

        # Preview button
        preview_btn = tk.Button(
            content,
            text="👁 Preview Changes (10 samples)",
            command=self._preview_changes,
            bg=self.colors['warning'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            borderwidth=0
        )
        preview_btn.pack(fill=tk.X, pady=(0, 8))

        # Execute button
        execute_btn = tk.Button(
            content,
            text="▶ Execute Update",
            command=self._execute_update,
            bg=self.colors['success'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            borderwidth=0
        )
        execute_btn.pack(fill=tk.X)

    def _create_footer(self, parent):
        """Create footer with status and logs."""
        footer_frame = tk.Frame(parent, bg=self.colors['bg'])
        footer_frame.pack(fill=tk.BOTH, expand=False, pady=(10, 0))

        # Status label
        self.status_label = tk.Label(
            footer_frame,
            text="● Ready - Connect to database to begin",
            font=('Segoe UI', 9),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg'],
            anchor='w'
        )
        self.status_label.pack(fill=tk.X, pady=(0, 4))

        # Log area
        log_frame = tk.Frame(footer_frame, bg=self.colors['secondary_bg'], height=120)
        log_frame.pack(fill=tk.X)
        log_frame.pack_propagate(False)

        tk.Label(
            log_frame,
            text="Activity Log",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['tertiary_bg']
        ).pack(fill=tk.X, padx=0, pady=0)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=5,
            font=('Courier New', 8),
            bg=self.colors['secondary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            wrap=tk.WORD,
            borderwidth=0
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _toggle_theme(self):
        """Toggle between dark and light theme."""
        self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
        self.colors = self.themes[self.current_theme]

        # Recreate UI with new theme
        for widget in self.root.winfo_children():
            widget.destroy()

        self._create_ui()
        self._configure_ttk_style()

    def _test_connection(self):
        """Test database connection and load tables."""
        try:
            self._log("Connecting to database...", 'info')

            self.db_manager = DatabaseManager(
                host=self.host_var.get(),
                port=int(self.port_var.get()),
                user=self.user_var.get(),
                password=self.password_var.get(),
                database=self.database_var.get() if self.database_var.get() else None
            )

            success, message = self.db_manager.test_connection()

            if success:
                self._log(f"✓ {message}", 'success')

                # Initialize name randomizer
                self.name_randomizer = NameRandomizer(
                    host=self.host_var.get(),
                    port=int(self.port_var.get()),
                    user=self.user_var.get(),
                    password=self.password_var.get(),
                    database=self.database_var.get()
                )

                self._load_tables()
            else:
                self._log(f"✗ {message}", 'error')
                messagebox.showerror("Connection Error", message)

        except Exception as e:
            self._log(f"✗ Connection error: {e}", 'error')
            messagebox.showerror("Error", str(e))

    def _load_tables(self):
        """Load tables from database."""
        try:
            tables = self.db_manager.get_tables(self.database_var.get())

            if tables:
                self.table_combo['values'] = tables
                self._log(f"Loaded {len(tables)} tables", 'info')
            else:
                self._log("No tables found in database", 'warning')

        except Exception as e:
            self._log(f"Error loading tables: {e}", 'error')

    def _on_table_selected(self, event):
        """Handle table selection."""
        table = self.selected_table.get()

        if table and self.db_manager:
            self._log(f"Loading table: {table}", 'info')

            # Get schema
            schema = self.db_manager.get_table_schema(table, self.database_var.get())

            if schema:
                # Store available columns
                self.available_columns = [col['Field'] for col in schema]

                # Auto-detect columns
                gender_col = self.db_manager.detect_gender_column(table, self.database_var.get())
                name_cols = self.db_manager.detect_name_columns(table, self.database_var.get())

                # Populate gender column dropdown
                self.gender_column_combo['values'] = self.available_columns
                if gender_col:
                    self.gender_column_var.set(gender_col)
                    self._log(f"Auto-detected gender column: {gender_col}", 'success')

                # Populate name columns listbox
                self.name_columns_listbox.delete(0, tk.END)
                for col in self.available_columns:
                    self.name_columns_listbox.insert(tk.END, col)

                # Select detected name columns
                if name_cols:
                    for i, col in enumerate(self.available_columns):
                        if col in name_cols:
                            self.name_columns_listbox.selection_set(i)
                    self._log(f"Auto-detected name columns: {', '.join(name_cols)}", 'success')

                # Load row count
                count = self.db_manager.get_row_count(table, None, self.database_var.get())
                self.row_count_label.config(text=f"Total Rows: {count:,}")

                # Load data grid
                self._refresh_table_data()

                # Update SQL preview
                self._update_sql_preview()

    def _refresh_table_data(self):
        """Refresh the data grid with top 10 rows."""
        table = self.selected_table.get()

        if not table or not self.db_manager:
            return

        try:
            self._log("Refreshing table data...", 'info')

            # Get top 10 rows
            data = self.db_manager.get_sample_data(table, limit=10, database=self.database_var.get())

            if data:
                # Clear existing data
                for item in self.data_tree.get_children():
                    self.data_tree.delete(item)

                # Configure columns
                columns = list(data[0].keys())
                self.data_tree['columns'] = columns
                self.data_tree['show'] = 'headings'

                # Configure column headings
                for col in columns:
                    self.data_tree.heading(col, text=col)
                    # Set column width based on content
                    max_width = max(len(col) * 8, 100)
                    self.data_tree.column(col, width=max_width, minwidth=80)

                # Insert data
                for row in data:
                    values = [str(row[col]) if row[col] is not None else '' for col in columns]
                    self.data_tree.insert('', tk.END, values=values)

                self._log(f"✓ Loaded {len(data)} rows", 'success')
            else:
                self._log("No data in table", 'warning')

        except Exception as e:
            self._log(f"Error loading data: {e}", 'error')

    def _get_selected_name_columns(self) -> List[str]:
        """Get selected name columns from listbox."""
        selected_indices = self.name_columns_listbox.curselection()
        return [self.available_columns[i] for i in selected_indices]

    def _update_sql_preview(self, event=None):
        """Update SQL preview based on current configuration."""
        table = self.selected_table.get()
        gender_col = self.gender_column_var.get()
        name_cols = self._get_selected_name_columns()
        target_gender = self.target_gender.get()

        if not table or not gender_col or not name_cols:
            return

        # Build sample SQL
        set_clauses = ", ".join([f"`{col}` = '[RandomName]'" for col in name_cols])

        # Build WHERE clause based on target gender
        where_clause = ""
        if target_gender == 'male':
            where_clause = f"WHERE `{gender_col}` IN ('male', 'Male', 'M', 'm', '1')"
        elif target_gender == 'female':
            where_clause = f"WHERE `{gender_col}` IN ('female', 'Female', 'F', 'f', '2')"
        else:  # both
            where_clause = f"WHERE `{gender_col}` IS NOT NULL"

        sql = f"""-- Sample UPDATE statement (actual names will vary)
UPDATE `{table}`
SET {set_clauses}
{where_clause}
LIMIT 1000;  -- Batch size

-- This is a preview. Actual execution uses transactions with rollback support.
-- Selected groups: {', '.join([g for g, v in self.group_vars.items() if v.get()])}"""

        # Update preview
        self.sql_preview.config(state='normal')
        self.sql_preview.delete(1.0, tk.END)
        self.sql_preview.insert(1.0, sql)
        self.sql_preview.config(state='disabled')

    def _preview_changes(self):
        """Preview changes with actual sample data."""
        if not self._validate_config():
            return

        try:
            self._log("Generating preview...", 'info')

            config = self._build_config()
            preview = self.name_randomizer.preview_changes(config, limit=10)

            # Show preview in a new window
            self._show_preview_window(preview)

            self._log(f"✓ Preview generated ({len(preview)} samples)", 'success')

        except Exception as e:
            self._log(f"Error generating preview: {e}", 'error')
            messagebox.showerror("Preview Error", str(e))

    def _show_preview_window(self, preview_data):
        """Show preview in a popup window."""
        preview_win = tk.Toplevel(self.root)
        preview_win.title("Preview Changes")
        preview_win.geometry("900x600")
        preview_win.configure(bg=self.colors['bg'])

        # Header
        header = tk.Label(
            preview_win,
            text="Preview of Changes (10 samples)",
            font=('Segoe UI', 14, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['bg']
        )
        header.pack(pady=15)

        # Create frame with scrollbar
        frame = tk.Frame(preview_win, bg=self.colors['bg'])
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Text widget
        text = scrolledtext.ScrolledText(
            frame,
            font=('Courier New', 9),
            bg=self.colors['secondary_bg'],
            fg=self.colors['fg'],
            wrap=tk.WORD
        )
        text.pack(fill=tk.BOTH, expand=True)

        # Insert preview data
        for i, row in enumerate(preview_data, 1):
            text.insert(tk.END, f"Row {i}:\n", 'header')
            for change in row['changes']:
                text.insert(tk.END, f"  {change['column']}: ", 'label')
                text.insert(tk.END, f"{change['old']}", 'old')
                text.insert(tk.END, " → ", 'arrow')
                text.insert(tk.END, f"{change['new']}\n", 'new')
            text.insert(tk.END, "\n")

        # Configure tags
        text.tag_config('header', foreground=self.colors['accent'], font=('Courier New', 9, 'bold'))
        text.tag_config('label', foreground=self.colors['text_secondary'])
        text.tag_config('old', foreground=self.colors['error'])
        text.tag_config('new', foreground=self.colors['success'])
        text.tag_config('arrow', foreground=self.colors['warning'])

        text.config(state='disabled')

        # Close button
        close_btn = tk.Button(
            preview_win,
            text="Close",
            command=preview_win.destroy,
            bg=self.colors['accent'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=30,
            pady=8,
            cursor='hand2'
        )
        close_btn.pack(pady=(0, 15))

    def _execute_update(self):
        """Execute the name randomization update."""
        if not self._validate_config():
            return

        # Confirmation dialog
        name_cols = self._get_selected_name_columns()
        table = self.selected_table.get()

        msg = f"""Are you sure you want to update the following columns in '{table}'?

Columns: {', '.join(name_cols)}
Target Gender: {self.target_gender.get()}
Groups: {', '.join([g for g, v in self.group_vars.items() if v.get()])}

This operation will modify your database.
A transaction will be used (can rollback on error)."""

        if not messagebox.askyesno("Confirm Update", msg):
            return

        try:
            self._log("Executing update...", 'info')
            self.status_label.config(text="● Executing update... Please wait", fg=self.colors['warning'])
            self.root.update()

            config = self._build_config()
            result = self.name_randomizer.execute_update(config, dry_run=False)

            # Show results
            success_msg = f"""Update Completed Successfully!

Total Rows: {result['total_rows']}
Updated: {result['updated_rows']}
Skipped: {result['skipped_rows']}
Errors: {len(result['errors'])}"""

            if result['errors']:
                success_msg += f"\n\nFirst error: {result['errors'][0]}"

            self._log(f"✓ Update complete: {result['updated_rows']} rows updated", 'success')
            messagebox.showinfo("Update Complete", success_msg)

            # Refresh data grid
            self._refresh_table_data()

        except Exception as e:
            self._log(f"✗ Update failed: {e}", 'error')
            messagebox.showerror("Update Error", f"Update failed:\n\n{str(e)}")
        finally:
            self.status_label.config(text="● Ready", fg=self.colors['text_secondary'])

    def _validate_config(self) -> bool:
        """Validate current configuration."""
        if not self.db_manager:
            messagebox.showerror("Error", "Please connect to database first")
            return False

        if not self.selected_table.get():
            messagebox.showerror("Error", "Please select a table")
            return False

        if not self.gender_column_var.get():
            messagebox.showerror("Error", "Please select a gender column")
            return False

        if not self._get_selected_name_columns():
            messagebox.showerror("Error", "Please select at least one name column")
            return False

        selected_groups = [g for g, v in self.group_vars.items() if v.get()]
        if not selected_groups:
            messagebox.showerror("Error", "Please select at least one name group")
            return False

        return True

    def _build_config(self) -> Dict[str, Any]:
        """Build configuration dictionary."""
        selected_groups = [g for g, v in self.group_vars.items() if v.get()]

        return {
            'table': self.selected_table.get(),
            'gender_column': self.gender_column_var.get(),
            'name_columns': self._get_selected_name_columns(),
            'target_gender': self.target_gender.get(),
            'name_groups': selected_groups,
            'distribution': 'proportional',
            'batch_size': 1000,
            'preserve_null': True,
            'primary_key': 'id'
        }

    def _log(self, message: str, level: str = 'info'):
        """Log message to console."""
        colors = {
            'info': self.colors['fg'],
            'success': self.colors['success'],
            'warning': self.colors['warning'],
            'error': self.colors['error']
        }

        timestamp = __import__('datetime').datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

        status_symbols = {
            'info': '●',
            'success': '✓',
            'warning': '⚠',
            'error': '✗'
        }

        self.status_label.config(
            text=f"{status_symbols.get(level, '●')} {message}",
            fg=colors.get(level, self.colors['fg'])
        )

    def run(self):
        """Start the application."""
        self.root.mainloop()


def main():
    """Launch the GUI application."""
    root = tk.Tk()
    app = DDAApplication(root)
    app.run()


if __name__ == '__main__':
    main()
