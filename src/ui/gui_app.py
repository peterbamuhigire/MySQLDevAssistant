"""
DDA GUI Application - Multi-tool interface with home screen
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from typing import Dict, Any, List, Optional
import logging
from pathlib import Path

from ..tools.name_generator import NameRandomizer
from ..tools.company_name_generator import CompanyNameGenerator
from ..tools.phone_number_generator import PhoneNumberGenerator
from ..tools.date_randomizer import DateRandomizer
from ..tools.code_generator import CodeGenerator
from ..tools.location_randomizer import LocationRandomizer
from ..core.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class DDAApplication:
    """Main GUI Application with multi-tool interface."""

    def __init__(self, root):
        self.root = root
        self.root.title("⚠️ DDA Toolkit - DEVELOPMENT/TESTING ONLY - DO NOT USE ON PRODUCTION")

        # Start maximized
        self.root.state('zoomed')  # Windows
        # Alternative for other platforms:
        # self.root.attributes('-zoomed', True)  # Linux
        # self.root.state('zoomed')  # macOS

        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)

        # Light mode only - no dark mode
        self.colors = {
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
            'grid_fg': '#212121',
            'info': '#00BCD4'
        }

        # Configure root
        self.root.configure(bg=self.colors['bg'])

        # Current screen tracking
        self.current_screen = None

        # Tool instances
        self.db_manager = None
        self.name_randomizer = None
        self.company_generator = None
        self.phone_generator = None
        self.date_randomizer = None
        self.code_generator = None
        self.location_randomizer = None

        # Connection variables (shared across tools)
        self.host_var = tk.StringVar(value='localhost')
        self.port_var = tk.StringVar(value='3306')
        self.user_var = tk.StringVar(value='root')
        self.password_var = tk.StringVar()
        self.database_var = tk.StringVar()

        # Name Randomizer variables
        self.selected_table = tk.StringVar()
        self.gender_column_var = tk.StringVar()
        self.name_columns_listvar = tk.StringVar()
        self.target_gender = tk.StringVar(value='both')
        self.full_name_mode = tk.BooleanVar(value=False)
        self.filter_column_var = tk.StringVar()
        self.filter_value_var = tk.StringVar()
        self.only_null_var = tk.BooleanVar(value=False)

        # Company Generator variables
        self.company_selected_table = tk.StringVar()
        self.company_columns_listvar = tk.StringVar()
        self.name1_groups_var = {}
        self.name2_groups_var = {}
        self.classification_groups_var = {}
        self.company_filter_column_var = tk.StringVar()
        self.company_filter_value_var = tk.StringVar()
        self.company_only_null_var = tk.BooleanVar(value=False)

        # Phone Number Generator variables
        self.phone_selected_table = tk.StringVar()
        self.phone_columns_listvar = tk.StringVar()
        self.phone_country_code = tk.StringVar(value='+256')
        self.phone_prefix = tk.StringVar(value='7')
        self.phone_min_number = tk.StringVar(value='10000000')
        self.phone_max_number = tk.StringVar(value='99999999')
        self.phone_filter_column_var = tk.StringVar()
        self.phone_filter_value_var = tk.StringVar()
        self.phone_only_null_var = tk.BooleanVar(value=False)

        # Date Randomizer variables
        self.date_selected_table = tk.StringVar()
        self.date_columns_listvar = tk.StringVar()
        self.date_start_date = tk.StringVar()
        self.date_end_date = tk.StringVar()
        self.date_include_time = tk.BooleanVar(value=True)
        self.date_filter_column_var = tk.StringVar()
        self.date_filter_value_var = tk.StringVar()
        self.date_only_null_var = tk.BooleanVar(value=False)

        # Code Generator variables
        self.code_selected_table = tk.StringVar()
        self.code_columns_listvar = tk.StringVar()
        self.code_type = tk.StringVar(value='mixed')
        self.code_length = tk.StringVar(value='8')
        self.code_prefix = tk.StringVar()
        self.code_filter_column_var = tk.StringVar()
        self.code_filter_value_var = tk.StringVar()
        self.code_only_null_var = tk.BooleanVar(value=False)

        # Location Randomizer variables
        self.location_selected_table = tk.StringVar()
        self.location_lat_column_var = tk.StringVar()
        self.location_lng_column_var = tk.StringVar()
        self.location_description_var = tk.StringVar()
        self.location_api_key_var = tk.StringVar()
        self.location_filter_column_var = tk.StringVar()
        self.location_filter_value_var = tk.StringVar()
        self.location_only_null_var = tk.BooleanVar(value=False)

        # Available columns
        self.available_columns = []
        self.company_available_columns = []
        self.phone_available_columns = []
        self.date_available_columns = []
        self.code_available_columns = []
        self.location_available_columns = []

        # Data storage
        self.current_table_data = []
        self.generated_sql = ""

        # Configure TTK style
        self._configure_ttk_style()

        # Show critical warning popup before anything else
        self._show_startup_warning()

        # Show home screen
        self._show_home_screen()

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

    def _show_startup_warning(self):
        """Show critical startup warning about development/testing only."""
        warning_msg = """
⚠️  CRITICAL WARNING  ⚠️

DEVELOPMENT & TESTING DATABASES ONLY!

This tool is designed EXCLUSIVELY for development and testing environments.

🚫 NEVER use this on production databases
🚫 NEVER connect to live customer data
🚫 NEVER use in production environments

This tool randomly modifies data and is intended ONLY for generating test data.

Using this on production data WILL:
• Corrupt your database
• Destroy real information permanently
• Replace genuine data with random test data
• Make data recovery impossible without backups

═══════════════════════════════════════

IF YOU ARE NOT 100% CERTAIN THIS IS A
TEST DATABASE, CLOSE THIS APPLICATION NOW!

═══════════════════════════════════════

Click OK only if you understand and accept these terms.
        """

        result = messagebox.showwarning(
            "⚠️ CRITICAL WARNING - DEVELOPMENT/TESTING ONLY",
            warning_msg,
            icon='warning'
        )

        # If user closes the dialog without clicking OK, show it again
        if result is None:
            # User closed the window, ask for explicit confirmation
            confirm = messagebox.askyesno(
                "⚠️ Confirm Understanding",
                "Do you understand that this tool is ONLY for development/testing databases?\n\n"
                "Using this on production will DESTROY your data!\n\n"
                "Click YES only if this is a TEST database.",
                icon='warning'
            )
            if not confirm:
                messagebox.showerror(
                    "Application Closing",
                    "Application will close to protect your production data.\n\n"
                    "Only use this tool with development/testing databases."
                )
                self.root.quit()
                import sys
                sys.exit(0)

    def _create_name_randomizer_ui(self):
        """Create the name randomizer tool interface."""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg'], padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with back button
        self._create_header(main_frame, "Name Randomizer - MySQL Development Assistant", show_back=True)

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

        # Right column - Configuration & Actions (always visible)
        right_frame = tk.Frame(content_frame, bg=self.colors['bg'], width=360)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(8, 0))
        right_frame.pack_propagate(False)

        # Create scrollable frame for right column
        right_canvas = tk.Canvas(right_frame, bg=self.colors['bg'], highlightthickness=0)
        right_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=right_canvas.yview)
        right_scrollable = tk.Frame(right_canvas, bg=self.colors['bg'])

        def update_scrollregion(e=None):
            right_canvas.configure(scrollregion=right_canvas.bbox("all"))

        right_scrollable.bind("<Configure>", update_scrollregion)

        right_canvas.create_window((0, 0), window=right_scrollable, anchor="nw", width=340)
        right_canvas.configure(yscrollcommand=right_scrollbar.set)

        # Enable mousewheel scrolling
        def on_mousewheel(event):
            right_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        right_canvas.bind_all("<MouseWheel>", on_mousewheel)

        right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._create_column_selection_panel(right_scrollable)
        self._create_name_config_panel(right_scrollable)
        self._create_action_panel(right_scrollable)

        # Footer - Status & Logs
        self._create_footer(main_frame)

    def _create_header(self, parent, subtitle="", show_back=False):
        """Create header with title and optional back button."""
        header_frame = tk.Frame(parent, bg=self.colors['bg'], height=50)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)

        # Back button (if requested)
        if show_back:
            back_btn = tk.Button(
                header_frame,
                text="← Back to Home",
                font=('Segoe UI', 10),
                command=self._show_home_screen,
                bg=self.colors['secondary_bg'],
                fg=self.colors['fg'],
                relief=tk.FLAT,
                padx=12,
                pady=6,
                cursor='hand2',
                borderwidth=1,
                highlightbackground=self.colors['border'],
                highlightthickness=1
            )
            back_btn.pack(side=tk.LEFT, pady=5)

        # Title
        title_label = tk.Label(
            header_frame,
            text="⚡ DDA Toolkit",
            font=('Segoe UI', 22, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['bg']
        )
        if show_back:
            title_label.pack(side=tk.LEFT, pady=5, padx=(15, 0))
        else:
            title_label.pack(side=tk.LEFT, pady=5)

        # Subtitle
        if subtitle:
            subtitle_label = tk.Label(
                header_frame,
                text=subtitle,
                font=('Segoe UI', 10),
                fg=self.colors['text_secondary'],
                bg=self.colors['bg']
            )
            subtitle_label.pack(side=tk.LEFT, padx=(12, 0), pady=5)

    def _create_panel(self, parent, title, height=None):
        """Create a styled panel."""
        panel_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT)

        if height:
            panel_frame.config(height=height)
            panel_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))
            panel_frame.pack_propagate(False)
        else:
            panel_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

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
            text="🔄 Refresh Sample Data",
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
            text="Total Rows: -",
            font=('Segoe UI', 9),
            fg=self.colors['text_secondary'],
            bg=self.colors['secondary_bg'],
            anchor='w'
        )
        self.row_count_label.pack(anchor='w')

    def _create_data_grid_panel(self, parent):
        """Create data grid panel showing top 10 rows."""
        content = self._create_panel(parent, "📊 Sample Data (Top 10 Rows)", height=300)

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
        self.sql_preview.insert(1.0, "-- Click 'Generate SQL' to preview the UPDATE statement\n-- Configuration: Select columns, gender, and name groups first")
        self.sql_preview.config(state='disabled')

    def _create_column_selection_panel(self, parent):
        """Create column selection panel - always visible."""
        # Create panel frame
        panel_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT)
        panel_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        # Panel header
        header = tk.Frame(panel_frame, bg=self.colors['tertiary_bg'], height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="🎯 1. Column Selection",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['tertiary_bg']
        )
        title_label.pack(side=tk.LEFT, padx=12, pady=6)

        # Panel content
        content = tk.Frame(panel_frame, bg=self.colors['secondary_bg'], padx=12, pady=12)
        content.pack(fill=tk.X, expand=False)

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

        # Name columns
        tk.Label(
            content,
            text="Name Columns (select multiple):",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        # Listbox for multiple selection
        listbox_frame = tk.Frame(content, bg=self.colors['secondary_bg'], height=100)
        listbox_frame.pack(fill=tk.X, pady=(0, 8))
        listbox_frame.pack_propagate(False)

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
            yscrollcommand=scrollbar.set,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=self.colors['border'],
            selectbackground=self.colors['accent']
        )
        self.name_columns_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=self.name_columns_listbox.yview)

        # Full name mode checkbox
        full_name_cb = tk.Checkbutton(
            content,
            text="  Full Name Mode (First Last in one column)",
            variable=self.full_name_mode,
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg'],
            selectcolor=self.colors['tertiary_bg'],
            activebackground=self.colors['secondary_bg']
        )
        full_name_cb.pack(anchor='w', pady=(0, 4))

    def _create_name_config_panel(self, parent):
        """Create name configuration panel - always visible."""
        # Create panel frame
        panel_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT)
        panel_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        # Panel header
        header = tk.Frame(panel_frame, bg=self.colors['tertiary_bg'], height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="⚙ 2. Name Options",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['tertiary_bg']
        )
        title_label.pack(side=tk.LEFT, padx=12, pady=6)

        # Panel content
        content = tk.Frame(panel_frame, bg=self.colors['secondary_bg'], padx=12, pady=12)
        content.pack(fill=tk.X, expand=False)

        # Target Gender
        tk.Label(
            content,
            text="Target Gender:",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 6))

        gender_frame = tk.Frame(content, bg=self.colors['secondary_bg'])
        gender_frame.pack(fill=tk.X, pady=(0, 15))

        for gender in ['male', 'female', 'both']:
            rb = tk.Radiobutton(
                gender_frame,
                text=gender.capitalize(),
                variable=self.target_gender,
                value=gender,
                font=('Segoe UI', 10),
                fg=self.colors['fg'],
                bg=self.colors['secondary_bg'],
                selectcolor=self.colors['tertiary_bg'],
                activebackground=self.colors['secondary_bg']
            )
            rb.pack(side=tk.LEFT, padx=(0, 20))

        # Name Groups
        tk.Label(
            content,
            text="Name Groups:",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 6))

        groups_frame = tk.Frame(content, bg=self.colors['secondary_bg'])
        groups_frame.pack(fill=tk.X)

        self.group_vars = {}
        groups_list = [
            ('All', True),
            ('English', False),
            ('Arabic', False),
            ('Asian', False),
            ('African', False)
        ]

        for group, default in groups_list:
            var = tk.BooleanVar(value=default)
            self.group_vars[group] = var

            cb = tk.Checkbutton(
                groups_frame,
                text=f"  {group}",
                variable=var,
                font=('Segoe UI', 10),
                fg=self.colors['fg'],
                bg=self.colors['secondary_bg'],
                selectcolor=self.colors['tertiary_bg'],
                activebackground=self.colors['secondary_bg']
            )
            cb.pack(anchor='w', pady=3)

        # Row Filter
        tk.Label(
            content,
            text="Row Filter (Optional):",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(15, 6))

        # Filter Column
        tk.Label(
            content,
            text="Filter Column:",
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 3))

        self.filter_column_combo = ttk.Combobox(
            content,
            textvariable=self.filter_column_var,
            state='readonly',
            font=('Segoe UI', 9)
        )
        self.filter_column_combo.pack(fill=tk.X, pady=(0, 8))

        # Filter Value
        tk.Label(
            content,
            text="Filter Value:",
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 3))

        filter_value_entry = tk.Entry(
            content,
            textvariable=self.filter_value_var,
            font=('Segoe UI', 9),
            bg=self.colors['grid_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            borderwidth=1
        )
        filter_value_entry.pack(fill=tk.X, pady=(0, 8))

        # ONLY NULL checkbox
        only_null_cb = tk.Checkbutton(
            content,
            text="  ONLY NULL (update only rows where name columns are NULL)",
            variable=self.only_null_var,
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg'],
            selectcolor=self.colors['tertiary_bg'],
            activebackground=self.colors['secondary_bg']
        )
        only_null_cb.pack(anchor='w', pady=(8, 8))

        # Help text
        tk.Label(
            content,
            text="Filter: Match specific value | ONLY NULL: Update empty values only",
            font=('Segoe UI', 8),
            fg=self.colors['text_secondary'],
            bg=self.colors['secondary_bg'],
            wraplength=320,
            justify='left'
        ).pack(anchor='w')

    def _create_action_panel(self, parent):
        """Create action buttons panel - always visible."""
        # Create panel frame
        panel_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT)
        panel_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        # Panel header
        header = tk.Frame(panel_frame, bg=self.colors['tertiary_bg'], height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="🚀 3. Execute",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['tertiary_bg']
        )
        title_label.pack(side=tk.LEFT, padx=12, pady=6)

        # Panel content
        content = tk.Frame(panel_frame, bg=self.colors['secondary_bg'], padx=12, pady=12)
        content.pack(fill=tk.X, expand=False)

        # Generate SQL button
        generate_btn = tk.Button(
            content,
            text="📝 Generate SQL Statement",
            command=self._generate_sql,
            bg=self.colors['info'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            borderwidth=0
        )
        generate_btn.pack(fill=tk.X, pady=(0, 10))

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
        preview_btn.pack(fill=tk.X, pady=(0, 10))

        # Execute button
        execute_btn = tk.Button(
            content,
            text="▶ Run Query (Update Names)",
            command=self._execute_update,
            bg=self.colors['success'],
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=12,
            cursor='hand2',
            borderwidth=0
        )
        execute_btn.pack(fill=tk.X, pady=(0, 15))

        # Separator
        separator = tk.Frame(content, bg=self.colors['border'], height=1)
        separator.pack(fill=tk.X, pady=(0, 15))

        # Randomize Gender button
        randomize_gender_btn = tk.Button(
            content,
            text="🎲 Randomize Gender Column",
            command=self._randomize_gender,
            bg=self.colors['info'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            borderwidth=0
        )
        randomize_gender_btn.pack(fill=tk.X, pady=(0, 30))  # Add bottom padding for scrollability

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

    def _clear_screen(self):
        """Clear all widgets from root window."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def _show_home_screen(self):
        """Show the home screen with tool selection buttons."""
        self._clear_screen()
        self.current_screen = 'home'

        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)

        # Header
        header_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, pady=(0, 20))

        title_label = tk.Label(
            header_frame,
            text="DDA Toolkit",
            font=('Segoe UI', 32, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['bg']
        )
        title_label.pack()

        subtitle_label = tk.Label(
            header_frame,
            text="Database Development Assistant",
            font=('Segoe UI', 14),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg']
        )
        subtitle_label.pack(pady=(8, 0))

        # Small warning reminder (main warning is popup)
        reminder_frame = tk.Frame(main_frame, bg='#FFF3CD', relief=tk.FLAT, bd=1)
        reminder_frame.pack(fill=tk.X, pady=(0, 20))

        reminder_text = tk.Label(
            reminder_frame,
            text="⚠️  Reminder: Development & Testing Databases Only  ⚠️",
            font=('Segoe UI', 10, 'bold'),
            fg='#856404',
            bg='#FFF3CD',
            pady=10
        )
        reminder_text.pack()

        # Tool selection frame - two columns
        tools_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        tools_frame.pack(expand=True)

        # Create left and right columns
        left_column = tk.Frame(tools_frame, bg=self.colors['bg'])
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        right_column = tk.Frame(tools_frame, bg=self.colors['bg'])
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # Left column tools
        left_tools = [
            {
                'name': 'Name Randomizer',
                'description': 'Randomize personal names with gender-based datasets',
                'icon': '👤',
                'command': self._show_name_randomizer_screen
            },
            {
                'name': 'Company Name Generator',
                'description': 'Generate realistic company and organization names',
                'icon': '🏢',
                'command': self._show_company_generator_screen
            },
            {
                'name': 'Phone Number Generator',
                'description': 'Generate random phone numbers with country codes',
                'icon': '📱',
                'command': self._show_phone_generator_screen
            }
        ]

        # Right column tools
        right_tools = [
            {
                'name': 'Date Randomizer',
                'description': 'Randomize date/datetime columns within date ranges',
                'icon': '📅',
                'command': self._show_date_randomizer_screen
            },
            {
                'name': 'Code Generator',
                'description': 'Generate random codes and serial numbers',
                'icon': '🔢',
                'command': self._show_code_generator_screen
            },
            {
                'name': 'Location Randomizer',
                'description': 'Generate realistic geographic coordinates with AI descriptions',
                'icon': '🌍',
                'command': self._show_location_randomizer_screen
            }
        ]

        for i, tool in enumerate(left_tools):
            self._create_tool_button(left_column, tool, i)

        for i, tool in enumerate(right_tools):
            self._create_tool_button(right_column, tool, i)

        # Footer
        footer_label = tk.Label(
            main_frame,
            text="Select a tool to get started",
            font=('Segoe UI', 10),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg']
        )
        footer_label.pack(side=tk.BOTTOM, pady=(40, 0))

    def _create_tool_button(self, parent, tool_config, index):
        """Create a tool selection button."""
        # Container for button
        btn_container = tk.Frame(parent, bg=self.colors['secondary_bg'],
                                 relief=tk.FLAT, bd=1, highlightbackground=self.colors['border'],
                                 highlightthickness=1)
        btn_container.pack(pady=10, ipadx=20, ipady=20, fill=tk.X)

        # Make it clickable
        btn_container.bind('<Enter>', lambda e: btn_container.config(bg=self.colors['tertiary_bg']))
        btn_container.bind('<Leave>', lambda e: btn_container.config(bg=self.colors['secondary_bg']))
        btn_container.bind('<Button-1>', lambda e: tool_config['command']())

        # Icon
        icon_label = tk.Label(
            btn_container,
            text=tool_config['icon'],
            font=('Segoe UI', 40),
            bg=self.colors['secondary_bg']
        )
        icon_label.pack(side=tk.LEFT, padx=(20, 30))
        icon_label.bind('<Button-1>', lambda e: tool_config['command']())

        # Text container
        text_container = tk.Frame(btn_container, bg=self.colors['secondary_bg'])
        text_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_container.bind('<Button-1>', lambda e: tool_config['command']())

        # Tool name
        name_label = tk.Label(
            text_container,
            text=tool_config['name'],
            font=('Segoe UI', 18, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg'],
            anchor='w'
        )
        name_label.pack(anchor='w')
        name_label.bind('<Button-1>', lambda e: tool_config['command']())

        # Description
        desc_label = tk.Label(
            text_container,
            text=tool_config['description'],
            font=('Segoe UI', 11),
            fg=self.colors['text_secondary'],
            bg=self.colors['secondary_bg'],
            anchor='w'
        )
        desc_label.pack(anchor='w', pady=(4, 0))
        desc_label.bind('<Button-1>', lambda e: tool_config['command']())

    def _show_name_randomizer_screen(self):
        """Show the name randomizer tool screen."""
        self._clear_screen()
        self.current_screen = 'name_randomizer'
        self._create_name_randomizer_ui()

    def _show_company_generator_screen(self):
        """Show the company name generator tool screen."""
        self._clear_screen()
        self.current_screen = 'company_generator'
        self._create_company_generator_ui()

    def _show_phone_generator_screen(self):
        """Show the phone number generator tool screen."""
        self._clear_screen()
        self.current_screen = 'phone_generator'
        self._create_phone_generator_ui()

    def _show_date_randomizer_screen(self):
        """Show the date randomizer tool screen."""
        self._clear_screen()
        self.current_screen = 'date_randomizer'
        self._create_date_randomizer_ui()

    def _show_code_generator_screen(self):
        """Show the code generator tool screen."""
        self._clear_screen()
        self.current_screen = 'code_generator'
        self._create_code_generator_ui()

    def _show_location_randomizer_screen(self):
        """Show the location randomizer tool screen."""
        self._clear_screen()
        self.current_screen = 'location_randomizer'
        self._create_location_randomizer_ui()

    def _create_company_generator_ui(self):
        """Create the company name generator tool interface."""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg'], padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with back button
        self._create_header(main_frame, "Company Name Generator", show_back=True)

        # Content area - 3 column layout
        content_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, pady=15)

        # Left column - Connection & Table
        left_frame = tk.Frame(content_frame, bg=self.colors['bg'], width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        left_frame.pack_propagate(False)

        self._create_company_connection_panel(left_frame)
        self._create_company_table_selection_panel(left_frame)

        # Middle column - Data Grid & SQL Preview
        middle_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8)

        self._create_company_data_grid_panel(middle_frame)
        self._create_company_sql_preview_panel(middle_frame)

        # Right column - Configuration & Actions
        right_frame = tk.Frame(content_frame, bg=self.colors['bg'], width=360)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(8, 0))
        right_frame.pack_propagate(False)

        # Create scrollable frame for right column
        company_right_canvas = tk.Canvas(right_frame, bg=self.colors['bg'], highlightthickness=0)
        company_right_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=company_right_canvas.yview)
        company_right_scrollable = tk.Frame(company_right_canvas, bg=self.colors['bg'])

        def update_company_scrollregion(e=None):
            company_right_canvas.configure(scrollregion=company_right_canvas.bbox("all"))

        company_right_scrollable.bind("<Configure>", update_company_scrollregion)

        company_right_canvas.create_window((0, 0), window=company_right_scrollable, anchor="nw", width=340)
        company_right_canvas.configure(yscrollcommand=company_right_scrollbar.set)

        # Enable mousewheel scrolling
        def on_company_mousewheel(event):
            company_right_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        company_right_canvas.bind_all("<MouseWheel>", on_company_mousewheel)

        company_right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        company_right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._create_company_column_selection_panel(company_right_scrollable)
        self._create_company_config_panel(company_right_scrollable)
        self._create_company_action_panel(company_right_scrollable)

        # Footer - Status & Logs
        self._create_company_footer(main_frame)

    def _create_company_connection_panel(self, parent):
        """Create database connection panel for company generator."""
        content = self._create_panel(parent, "📊 Database Connection")

        # Connection inputs (same as name randomizer)
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
            command=self._test_company_connection,
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

    def _create_company_table_selection_panel(self, parent):
        """Create table selection panel for company generator."""
        content = self._create_panel(parent, "📋 Table Selection")

        # Table dropdown
        tk.Label(
            content,
            text="Table:",
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        self.company_table_combo = ttk.Combobox(
            content,
            textvariable=self.company_selected_table,
            state='readonly',
            font=('Segoe UI', 9)
        )
        self.company_table_combo.pack(fill=tk.X, pady=(0, 8))
        self.company_table_combo.bind('<<ComboboxSelected>>', self._on_company_table_selected)

        # Refresh button
        refresh_btn = tk.Button(
            content,
            text="🔄 Refresh Sample Data",
            command=self._refresh_company_table_data,
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
        self.company_row_count_label = tk.Label(
            content,
            text="Total Rows: -",
            font=('Segoe UI', 9),
            fg=self.colors['text_secondary'],
            bg=self.colors['secondary_bg'],
            anchor='w'
        )
        self.company_row_count_label.pack(anchor='w')

    def _create_company_data_grid_panel(self, parent):
        """Create data grid panel for company generator."""
        content = self._create_panel(parent, "📊 Sample Data (Top 10 Rows)", height=300)

        # Create Treeview with scrollbars
        tree_frame = tk.Frame(content, bg=self.colors['secondary_bg'])
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        self.company_data_tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            style="Custom.Treeview",
            selectmode='browse'
        )

        vsb.config(command=self.company_data_tree.yview)
        hsb.config(command=self.company_data_tree.xview)

        # Grid layout
        self.company_data_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

    def _create_company_sql_preview_panel(self, parent):
        """Create SQL preview panel for company generator."""
        content = self._create_panel(parent, "🔍 SQL Preview", height=150)

        self.company_sql_preview = scrolledtext.ScrolledText(
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
        self.company_sql_preview.pack(fill=tk.BOTH, expand=True)

        # Insert placeholder
        self.company_sql_preview.insert(1.0, "-- Click 'Generate SQL' to preview the UPDATE statement\n-- Configuration: Select columns and name groups first")
        self.company_sql_preview.config(state='disabled')

    def _create_company_column_selection_panel(self, parent):
        """Create column selection panel for company generator."""
        panel_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT)
        panel_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        # Panel header
        header = tk.Frame(panel_frame, bg=self.colors['tertiary_bg'], height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="🎯 1. Column Selection",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['tertiary_bg']
        )
        title_label.pack(side=tk.LEFT, padx=12, pady=6)

        # Panel content
        content = tk.Frame(panel_frame, bg=self.colors['secondary_bg'], padx=12, pady=12)
        content.pack(fill=tk.X, expand=False)

        # Company name columns
        tk.Label(
            content,
            text="Company Name Columns (select multiple):",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        # Listbox for multiple selection
        listbox_frame = tk.Frame(content, bg=self.colors['secondary_bg'], height=100)
        listbox_frame.pack(fill=tk.X, pady=(0, 8))
        listbox_frame.pack_propagate(False)

        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.company_columns_listbox = tk.Listbox(
            listbox_frame,
            listvariable=self.company_columns_listvar,
            selectmode=tk.MULTIPLE,
            font=('Segoe UI', 9),
            bg=self.colors['tertiary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            yscrollcommand=scrollbar.set,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=self.colors['border'],
            selectbackground=self.colors['accent']
        )
        self.company_columns_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=self.company_columns_listbox.yview)

    def _create_company_config_panel(self, parent):
        """Create company name configuration panel."""
        panel_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT)
        panel_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        # Panel header
        header = tk.Frame(panel_frame, bg=self.colors['tertiary_bg'], height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="⚙ 2. Name Options",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['tertiary_bg']
        )
        title_label.pack(side=tk.LEFT, padx=12, pady=6)

        # Panel content
        content = tk.Frame(panel_frame, bg=self.colors['secondary_bg'], padx=12, pady=12)
        content.pack(fill=tk.X, expand=False)

        # Name1 Groups
        tk.Label(
            content,
            text="Name1 Groups (First Part):",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 6))

        name1_frame = tk.Frame(content, bg=self.colors['secondary_bg'])
        name1_frame.pack(fill=tk.X, pady=(0, 15))

        self.name1_groups_var = {}
        name1_groups_list = [('All', True), ('English', False), ('Global', False)]

        for group, default in name1_groups_list:
            var = tk.BooleanVar(value=default)
            self.name1_groups_var[group] = var
            cb = tk.Checkbutton(
                name1_frame,
                text=f"  {group}",
                variable=var,
                font=('Segoe UI', 10),
                fg=self.colors['fg'],
                bg=self.colors['secondary_bg'],
                selectcolor=self.colors['tertiary_bg'],
                activebackground=self.colors['secondary_bg']
            )
            cb.pack(anchor='w', pady=3)

        # Name2 Groups
        tk.Label(
            content,
            text="Name2 Groups (Second Part):",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 6))

        name2_frame = tk.Frame(content, bg=self.colors['secondary_bg'])
        name2_frame.pack(fill=tk.X, pady=(0, 15))

        self.name2_groups_var = {}
        name2_groups_list = [('All', True), ('English', False), ('Global', False)]

        for group, default in name2_groups_list:
            var = tk.BooleanVar(value=default)
            self.name2_groups_var[group] = var
            cb = tk.Checkbutton(
                name2_frame,
                text=f"  {group}",
                variable=var,
                font=('Segoe UI', 10),
                fg=self.colors['fg'],
                bg=self.colors['secondary_bg'],
                selectcolor=self.colors['tertiary_bg'],
                activebackground=self.colors['secondary_bg']
            )
            cb.pack(anchor='w', pady=3)

        # Classification Groups
        tk.Label(
            content,
            text="Classification Groups (Suffix):",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 6))

        classification_frame = tk.Frame(content, bg=self.colors['secondary_bg'])
        classification_frame.pack(fill=tk.X)

        self.classification_groups_var = {}
        classification_groups_list = [
            ('All', True), ('Corporate', False), ('Professional', False),
            ('Financial', False), ('Tech', False), ('Industrial', False)
        ]

        for group, default in classification_groups_list:
            var = tk.BooleanVar(value=default)
            self.classification_groups_var[group] = var
            cb = tk.Checkbutton(
                classification_frame,
                text=f"  {group}",
                variable=var,
                font=('Segoe UI', 10),
                fg=self.colors['fg'],
                bg=self.colors['secondary_bg'],
                selectcolor=self.colors['tertiary_bg'],
                activebackground=self.colors['secondary_bg']
            )
            cb.pack(anchor='w', pady=3)

        # Row Filter
        tk.Label(
            content,
            text="Row Filter (Optional):",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(15, 6))

        # Filter Column
        tk.Label(
            content,
            text="Filter Column:",
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 3))

        self.company_filter_column_combo = ttk.Combobox(
            content,
            textvariable=self.company_filter_column_var,
            state='readonly',
            font=('Segoe UI', 9)
        )
        self.company_filter_column_combo.pack(fill=tk.X, pady=(0, 8))

        # Filter Value
        tk.Label(
            content,
            text="Filter Value:",
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 3))

        filter_value_entry = tk.Entry(
            content,
            textvariable=self.company_filter_value_var,
            font=('Segoe UI', 9),
            bg=self.colors['grid_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            borderwidth=1
        )
        filter_value_entry.pack(fill=tk.X, pady=(0, 8))

        # ONLY NULL checkbox
        only_null_cb = tk.Checkbutton(
            content,
            text="  ONLY NULL (update only rows where company columns are NULL)",
            variable=self.company_only_null_var,
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg'],
            selectcolor=self.colors['tertiary_bg'],
            activebackground=self.colors['secondary_bg']
        )
        only_null_cb.pack(anchor='w', pady=(8, 8))

        # Help text
        tk.Label(
            content,
            text="Filter: Match specific value | ONLY NULL: Update empty values only",
            font=('Segoe UI', 8),
            fg=self.colors['text_secondary'],
            bg=self.colors['secondary_bg'],
            wraplength=320,
            justify='left'
        ).pack(anchor='w')

    def _create_company_action_panel(self, parent):
        """Create action buttons panel for company generator."""
        panel_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT)
        panel_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        # Panel header
        header = tk.Frame(panel_frame, bg=self.colors['tertiary_bg'], height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="🚀 3. Execute",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['tertiary_bg']
        )
        title_label.pack(side=tk.LEFT, padx=12, pady=6)

        # Panel content
        content = tk.Frame(panel_frame, bg=self.colors['secondary_bg'], padx=12, pady=12)
        content.pack(fill=tk.X, expand=False)

        # Generate SQL button
        generate_btn = tk.Button(
            content,
            text="📝 Generate SQL Statement",
            command=self._generate_company_sql,
            bg=self.colors['info'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            borderwidth=0
        )
        generate_btn.pack(fill=tk.X, pady=(0, 10))

        # Preview button
        preview_btn = tk.Button(
            content,
            text="👁 Preview Changes (10 samples)",
            command=self._preview_company_changes,
            bg=self.colors['warning'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            borderwidth=0
        )
        preview_btn.pack(fill=tk.X, pady=(0, 10))

        # Execute button
        execute_btn = tk.Button(
            content,
            text="▶ Run Query (Update Names)",
            command=self._execute_company_update,
            bg=self.colors['success'],
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=12,
            cursor='hand2',
            borderwidth=0
        )
        execute_btn.pack(fill=tk.X, pady=(0, 30))  # Add bottom padding for scrollability

    def _create_company_footer(self, parent):
        """Create footer with status and logs for company generator."""
        footer_frame = tk.Frame(parent, bg=self.colors['bg'])
        footer_frame.pack(fill=tk.BOTH, expand=False, pady=(10, 0))

        # Status label
        self.company_status_label = tk.Label(
            footer_frame,
            text="● Ready - Connect to database to begin",
            font=('Segoe UI', 9),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg'],
            anchor='w'
        )
        self.company_status_label.pack(fill=tk.X, pady=(0, 4))

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

        self.company_log_text = scrolledtext.ScrolledText(
            log_frame,
            height=5,
            font=('Courier New', 8),
            bg=self.colors['secondary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            wrap=tk.WORD,
            borderwidth=0
        )
        self.company_log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _test_connection(self):
        """Test database connection and load tables."""
        # Show critical warning before connecting
        confirm = messagebox.askokcancel(
            "⚠ CRITICAL WARNING - Development/Testing Only",
            "THIS TOOL IS FOR DEVELOPMENT AND TESTING DATABASES ONLY!\n\n"
            "By clicking OK, you confirm that:\n\n"
            "✓ This is a development or testing database\n"
            "✓ This is NOT a production database\n"
            "✓ You understand this tool will randomly modify data\n"
            "✓ You have backups if needed\n\n"
            "⚠ NEVER USE THIS ON PRODUCTION DATABASES ⚠\n\n"
            "Are you absolutely sure you want to connect?",
            icon='warning'
        )

        if not confirm:
            self._log("Connection cancelled by user", 'warning')
            return

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

                # Populate filter column dropdown
                self.filter_column_combo['values'] = [''] + self.available_columns

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

    def _refresh_table_data(self):
        """Refresh the data grid with top 10 rows."""
        table = self.selected_table.get()

        if not table or not self.db_manager:
            return

        try:
            self._log("Refreshing sample data...", 'info')

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

    def _generate_sql(self):
        """Generate SQL UPDATE statement."""
        if not self._validate_config():
            return

        try:
            table = self.selected_table.get()
            gender_col = self.gender_column_var.get()
            name_cols = self._get_selected_name_columns()
            target_gender = self.target_gender.get()
            selected_groups = [g for g, v in self.group_vars.items() if v.get()]

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

            sql = f"""-- Generated UPDATE statement
-- This will update names in batches of 1000 rows with transaction safety

UPDATE `{table}`
SET {set_clauses}
{where_clause}
LIMIT 1000;  -- Batch size (repeats until all matching rows updated)

-- Configuration:
-- Target Gender: {target_gender}
-- Name Groups: {', '.join(selected_groups)}
-- Columns to update: {', '.join(name_cols)}
--
-- Click 'Preview Changes' to see sample before/after
-- Click 'Run Query' to execute the update"""

            # Store for later use
            self.generated_sql = sql

            # Update preview
            self.sql_preview.config(state='normal')
            self.sql_preview.delete(1.0, tk.END)
            self.sql_preview.insert(1.0, sql)
            self.sql_preview.config(state='disabled')

            self._log("✓ SQL statement generated", 'success')

        except Exception as e:
            self._log(f"Error generating SQL: {e}", 'error')

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
            error_details = str(e)
            self._log(f"✗ Preview generation failed: {error_details}", 'error')

            # Log full traceback for debugging
            import traceback
            tb = traceback.format_exc()
            self._log(f"Traceback:\n{tb}", 'error')

            messagebox.showerror("Preview Error", f"{error_details}\n\nCheck Activity Log for full details.")

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
        selected_groups = [g for g, v in self.group_vars.items() if v.get()]

        msg = f"""Are you sure you want to run this query?

Table: {table}
Columns: {', '.join(name_cols)}
Target Gender: {self.target_gender.get()}
Name Groups: {', '.join(selected_groups)}
Full Name Mode: {'Yes' if self.full_name_mode.get() else 'No'}

This will modify your database.
Transactions will be used (can rollback on error)."""

        if not messagebox.askyesno("Confirm Query Execution", msg):
            return

        try:
            self._log("Running query...", 'info')
            self.status_label.config(text="● Running query... Please wait", fg=self.colors['warning'])
            self.root.update()

            config = self._build_config()
            result = self.name_randomizer.execute_update(config, dry_run=False)

            # Log all errors to activity log
            if result['errors']:
                self._log(f"⚠ {len(result['errors'])} error(s) occurred during execution:", 'warning')
                for i, error in enumerate(result['errors'][:10], 1):  # Show first 10 errors
                    self._log(f"  Error {i}: {error}", 'error')
                if len(result['errors']) > 10:
                    self._log(f"  ... and {len(result['errors']) - 10} more errors", 'error')

            # Show results
            success_msg = f"""Query Completed!

Total Rows: {result['total_rows']}
Updated: {result['updated_rows']}
Skipped: {result['skipped_rows']}
Errors: {len(result['errors'])}"""

            if result['errors']:
                success_msg += f"\n\nCheck Activity Log for error details."
                success_msg += f"\nFirst error: {result['errors'][0]}"

            self._log(f"✓ Query complete: {result['updated_rows']} rows updated, {result['skipped_rows']} skipped", 'success' if len(result['errors']) == 0 else 'warning')

            if len(result['errors']) > 0:
                messagebox.showwarning("Query Completed with Errors", success_msg)
            else:
                messagebox.showinfo("Query Complete", success_msg)

            # Auto-refresh sample data
            self._log("Auto-refreshing sample data...", 'info')
            self._refresh_table_data()

        except Exception as e:
            error_details = str(e)
            self._log(f"✗ Query failed: {error_details}", 'error')

            # Log full traceback for debugging
            import traceback
            tb = traceback.format_exc()
            self._log(f"Traceback:\n{tb}", 'error')

            messagebox.showerror("Query Error", f"Query failed:\n\n{error_details}\n\nCheck Activity Log for full details.")
        finally:
            self.status_label.config(text="● Ready", fg=self.colors['text_secondary'])

    def _randomize_gender(self):
        """Randomize gender column with random male/female values."""
        if not self.db_manager:
            messagebox.showerror("Error", "Please connect to database first")
            return

        if not self.selected_table.get():
            messagebox.showerror("Error", "Please select a table")
            return

        if not self.gender_column_var.get():
            messagebox.showerror("Error", "Please select a gender column")
            return

        table = self.selected_table.get()
        gender_col = self.gender_column_var.get()

        # Confirmation
        msg = f"""Randomize Gender Column?

Table: {table}
Column: {gender_col}

This will randomly assign 'male' or 'female' to all rows.
Useful for generating test data.

Continue?"""

        if not messagebox.askyesno("Confirm Gender Randomization", msg):
            return

        try:
            self._log("Randomizing gender column...", 'info')
            self.status_label.config(text="● Randomizing gender... Please wait", fg=self.colors['warning'])
            self.root.update()

            # Get total rows
            total_rows = self.db_manager.get_row_count(table, None, self.database_var.get())

            # Build UPDATE query using RAND()
            sql = f"""UPDATE `{table}`
SET `{gender_col}` = CASE
    WHEN RAND() < 0.5 THEN 'male'
    ELSE 'female'
END"""

            # Execute
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                affected_rows = cursor.rowcount
                conn.commit()
                cursor.close()

            success_msg = f"""Gender Randomization Complete!

Table: {table}
Column: {gender_col}
Rows Updated: {affected_rows}

Gender values randomly assigned (50/50 split)."""

            self._log(f"✓ Gender randomized: {affected_rows} rows updated", 'success')
            messagebox.showinfo("Randomization Complete", success_msg)

            # Auto-refresh sample data
            self._log("Auto-refreshing sample data...", 'info')
            self._refresh_table_data()

        except Exception as e:
            error_details = str(e)
            self._log(f"✗ Gender randomization failed: {error_details}", 'error')

            # Log full traceback for debugging
            import traceback
            tb = traceback.format_exc()
            self._log(f"Traceback:\n{tb}", 'error')

            messagebox.showerror("Error", f"Randomization failed:\n\n{error_details}\n\nCheck Activity Log for full details.")
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

        # Build where clause from filter if provided
        where_clause = None
        filter_col = self.filter_column_var.get()
        filter_val = self.filter_value_var.get()
        if filter_col and filter_val:
            # Escape the value to prevent SQL injection
            escaped_val = filter_val.replace("'", "''")
            where_clause = f"`{filter_col}` = '{escaped_val}'"

        return {
            'table': self.selected_table.get(),
            'gender_column': self.gender_column_var.get(),
            'name_columns': self._get_selected_name_columns(),
            'target_gender': self.target_gender.get(),
            'name_groups': selected_groups,
            'distribution': 'proportional',
            'batch_size': 1000,
            'preserve_null': False,  # Update NULL values too
            'primary_key': 'id',
            'full_name_mode': self.full_name_mode.get(),
            'where_clause': where_clause
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

    # Company Generator Event Handlers

    def _test_company_connection(self):
        """Test database connection and load tables for company generator."""
        # Show critical warning before connecting
        confirm = messagebox.askokcancel(
            "⚠ CRITICAL WARNING - Development/Testing Only",
            "THIS TOOL IS FOR DEVELOPMENT AND TESTING DATABASES ONLY!\n\n"
            "By clicking OK, you confirm that:\n\n"
            "✓ This is a development or testing database\n"
            "✓ This is NOT a production database\n"
            "✓ You understand this tool will randomly modify data\n"
            "✓ You have backups if needed\n\n"
            "⚠ NEVER USE THIS ON PRODUCTION DATABASES ⚠\n\n"
            "Are you absolutely sure you want to connect?",
            icon='warning'
        )

        if not confirm:
            self._company_log("Connection cancelled by user", 'warning')
            return

        try:
            self._company_log("Connecting to database...", 'info')

            self.db_manager = DatabaseManager(
                host=self.host_var.get(),
                port=int(self.port_var.get()),
                user=self.user_var.get(),
                password=self.password_var.get(),
                database=self.database_var.get() if self.database_var.get() else None
            )

            success, message = self.db_manager.test_connection()

            if success:
                self._company_log(f"✓ {message}", 'success')

                # Initialize company generator
                self.company_generator = CompanyNameGenerator(
                    host=self.host_var.get(),
                    port=int(self.port_var.get()),
                    user=self.user_var.get(),
                    password=self.password_var.get(),
                    database=self.database_var.get()
                )

                self._load_company_tables()
            else:
                self._company_log(f"✗ {message}", 'error')
                messagebox.showerror("Connection Error", message)

        except Exception as e:
            self._company_log(f"✗ Connection error: {e}", 'error')
            messagebox.showerror("Error", str(e))

    def _load_company_tables(self):
        """Load tables from database for company generator."""
        try:
            tables = self.db_manager.get_tables(self.database_var.get())

            if tables:
                self.company_table_combo['values'] = tables
                self._company_log(f"Loaded {len(tables)} tables", 'info')
            else:
                self._company_log("No tables found in database", 'warning')

        except Exception as e:
            self._company_log(f"Error loading tables: {e}", 'error')

    def _on_company_table_selected(self, event):
        """Handle table selection for company generator."""
        table = self.company_selected_table.get()

        if table and self.db_manager:
            self._company_log(f"Loading table: {table}", 'info')

            # Get schema
            schema = self.db_manager.get_table_schema(table, self.database_var.get())

            if schema:
                # Store available columns
                self.company_available_columns = [col['Field'] for col in schema]

                # Populate filter column dropdown
                self.company_filter_column_combo['values'] = [''] + self.company_available_columns

                # Populate company columns listbox
                self.company_columns_listbox.delete(0, tk.END)
                for col in self.company_available_columns:
                    self.company_columns_listbox.insert(tk.END, col)

                # Load row count
                count = self.db_manager.get_row_count(table, None, self.database_var.get())
                self.company_row_count_label.config(text=f"Total Rows: {count:,}")

                # Load data grid
                self._refresh_company_table_data()

    def _refresh_company_table_data(self):
        """Refresh the data grid with top 10 rows for company generator."""
        table = self.company_selected_table.get()

        if not table or not self.db_manager:
            return

        try:
            self._company_log("Refreshing sample data...", 'info')

            # Get top 10 rows
            data = self.db_manager.get_sample_data(table, limit=10, database=self.database_var.get())

            if data:
                # Clear existing data
                for item in self.company_data_tree.get_children():
                    self.company_data_tree.delete(item)

                # Configure columns
                columns = list(data[0].keys())
                self.company_data_tree['columns'] = columns
                self.company_data_tree['show'] = 'headings'

                # Configure column headings
                for col in columns:
                    self.company_data_tree.heading(col, text=col)
                    # Set column width based on content
                    max_width = max(len(col) * 8, 100)
                    self.company_data_tree.column(col, width=max_width, minwidth=80)

                # Insert data
                for row in data:
                    values = [str(row[col]) if row[col] is not None else '' for col in columns]
                    self.company_data_tree.insert('', tk.END, values=values)

                self._company_log(f"✓ Loaded {len(data)} rows", 'success')
            else:
                self._company_log("No data in table", 'warning')

        except Exception as e:
            self._company_log(f"Error loading data: {e}", 'error')

    def _get_selected_company_columns(self) -> List[str]:
        """Get selected company columns from listbox."""
        selected_indices = self.company_columns_listbox.curselection()
        return [self.company_available_columns[i] for i in selected_indices]

    def _generate_company_sql(self):
        """Generate SQL UPDATE statement for company generator."""
        if not self._validate_company_config():
            return

        try:
            table = self.company_selected_table.get()
            company_cols = self._get_selected_company_columns()
            name1_groups = [g for g, v in self.name1_groups_var.items() if v.get()]
            name2_groups = [g for g, v in self.name2_groups_var.items() if v.get()]
            classification_groups = [g for g, v in self.classification_groups_var.items() if v.get()]

            # Build sample SQL
            set_clauses = ", ".join([f"`{col}` = '[RandomCompanyName]'" for col in company_cols])

            sql = f"""-- Generated UPDATE statement
-- This will update company names in batches of 1000 rows with transaction safety

UPDATE `{table}`
SET {set_clauses}
LIMIT 1000;  -- Batch size (repeats until all rows updated)

-- Configuration:
-- Name1 Groups: {', '.join(name1_groups)}
-- Name2 Groups: {', '.join(name2_groups)}
-- Classification Groups: {', '.join(classification_groups)}
-- Columns to update: {', '.join(company_cols)}
--
-- Format: Name1 + Name2 + Classification
-- Example: Ardson Bentley Associates, Apex Dynamics Corporation
--
-- Click 'Preview Changes' to see sample before/after
-- Click 'Run Query' to execute the update"""

            # Update preview
            self.company_sql_preview.config(state='normal')
            self.company_sql_preview.delete(1.0, tk.END)
            self.company_sql_preview.insert(1.0, sql)
            self.company_sql_preview.config(state='disabled')

            self._company_log("✓ SQL statement generated", 'success')

        except Exception as e:
            self._company_log(f"Error generating SQL: {e}", 'error')

    def _preview_company_changes(self):
        """Preview changes with actual sample data for company generator."""
        if not self._validate_company_config():
            return

        try:
            self._company_log("Generating preview...", 'info')

            config = self._build_company_config()
            preview = self.company_generator.preview_changes(config, limit=10)

            # Show preview in a new window
            self._show_company_preview_window(preview)

            self._company_log(f"✓ Preview generated ({len(preview)} samples)", 'success')

        except Exception as e:
            error_details = str(e)
            self._company_log(f"✗ Preview generation failed: {error_details}", 'error')

            # Log full traceback for debugging
            import traceback
            tb = traceback.format_exc()
            self._company_log(f"Traceback:\n{tb}", 'error')

            messagebox.showerror("Preview Error", f"{error_details}\n\nCheck Activity Log for full details.")

    def _show_company_preview_window(self, preview_data):
        """Show preview in a popup window for company generator."""
        preview_win = tk.Toplevel(self.root)
        preview_win.title("Preview Changes - Company Names")
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

    def _execute_company_update(self):
        """Execute the company name update."""
        if not self._validate_company_config():
            return

        # Confirmation dialog
        company_cols = self._get_selected_company_columns()
        table = self.company_selected_table.get()
        name1_groups = [g for g, v in self.name1_groups_var.items() if v.get()]
        name2_groups = [g for g, v in self.name2_groups_var.items() if v.get()]
        classification_groups = [g for g, v in self.classification_groups_var.items() if v.get()]

        msg = f"""Are you sure you want to run this query?

Table: {table}
Columns: {', '.join(company_cols)}
Name1 Groups: {', '.join(name1_groups)}
Name2 Groups: {', '.join(name2_groups)}
Classification Groups: {', '.join(classification_groups)}

This will modify your database.
Transactions will be used (can rollback on error)."""

        if not messagebox.askyesno("Confirm Query Execution", msg):
            return

        try:
            self._company_log("Running query...", 'info')
            self.company_status_label.config(text="● Running query... Please wait", fg=self.colors['warning'])
            self.root.update()

            config = self._build_company_config()
            result = self.company_generator.execute_update(config, dry_run=False)

            # Log all errors to activity log
            if result['errors']:
                self._company_log(f"⚠ {len(result['errors'])} error(s) occurred during execution:", 'warning')
                for i, error in enumerate(result['errors'][:10], 1):  # Show first 10 errors
                    self._company_log(f"  Error {i}: {error}", 'error')
                if len(result['errors']) > 10:
                    self._company_log(f"  ... and {len(result['errors']) - 10} more errors", 'error')

            # Show results
            success_msg = f"""Query Completed!

Total Rows: {result['total_rows']}
Updated: {result['updated_rows']}
Skipped: {result['skipped_rows']}
Errors: {len(result['errors'])}"""

            if result['errors']:
                success_msg += f"\n\nCheck Activity Log for error details."
                success_msg += f"\nFirst error: {result['errors'][0]}"

            self._company_log(f"✓ Query complete: {result['updated_rows']} rows updated, {result['skipped_rows']} skipped", 'success' if len(result['errors']) == 0 else 'warning')

            if len(result['errors']) > 0:
                messagebox.showwarning("Query Completed with Errors", success_msg)
            else:
                messagebox.showinfo("Query Complete", success_msg)

            # Auto-refresh sample data
            self._company_log("Auto-refreshing sample data...", 'info')
            self._refresh_company_table_data()

        except Exception as e:
            error_details = str(e)
            self._company_log(f"✗ Query failed: {error_details}", 'error')

            # Log full traceback for debugging
            import traceback
            tb = traceback.format_exc()
            self._company_log(f"Traceback:\n{tb}", 'error')

            messagebox.showerror("Query Error", f"Query failed:\n\n{error_details}\n\nCheck Activity Log for full details.")
        finally:
            self.company_status_label.config(text="● Ready", fg=self.colors['text_secondary'])

    def _validate_company_config(self) -> bool:
        """Validate current configuration for company generator."""
        if not self.db_manager:
            messagebox.showerror("Error", "Please connect to database first")
            return False

        if not self.company_selected_table.get():
            messagebox.showerror("Error", "Please select a table")
            return False

        if not self._get_selected_company_columns():
            messagebox.showerror("Error", "Please select at least one company column")
            return False

        name1_groups = [g for g, v in self.name1_groups_var.items() if v.get()]
        name2_groups = [g for g, v in self.name2_groups_var.items() if v.get()]
        classification_groups = [g for g, v in self.classification_groups_var.items() if v.get()]

        if not name1_groups:
            messagebox.showerror("Error", "Please select at least one Name1 group")
            return False

        if not name2_groups:
            messagebox.showerror("Error", "Please select at least one Name2 group")
            return False

        if not classification_groups:
            messagebox.showerror("Error", "Please select at least one Classification group")
            return False

        return True

    def _build_company_config(self) -> Dict[str, Any]:
        """Build configuration dictionary for company generator."""
        name1_groups = [g for g, v in self.name1_groups_var.items() if v.get()]
        name2_groups = [g for g, v in self.name2_groups_var.items() if v.get()]
        classification_groups = [g for g, v in self.classification_groups_var.items() if v.get()]

        # Build where clause from filter if provided
        where_clause = None
        filter_col = self.company_filter_column_var.get()
        filter_val = self.company_filter_value_var.get()
        if filter_col and filter_val:
            # Escape the value to prevent SQL injection
            escaped_val = filter_val.replace("'", "''")
            where_clause = f"`{filter_col}` = '{escaped_val}'"

        return {
            'table': self.company_selected_table.get(),
            'company_columns': self._get_selected_company_columns(),
            'name1_groups': name1_groups,
            'name2_groups': name2_groups,
            'classification_groups': classification_groups,
            'batch_size': 1000,
            'preserve_null': False,  # Update NULL values too
            'primary_key': 'id',
            'where_clause': where_clause
        }

    def _company_log(self, message: str, level: str = 'info'):
        """Log message to company generator console."""
        colors = {
            'info': self.colors['fg'],
            'success': self.colors['success'],
            'warning': self.colors['warning'],
            'error': self.colors['error']
        }

        timestamp = __import__('datetime').datetime.now().strftime('%H:%M:%S')
        self.company_log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.company_log_text.see(tk.END)

        status_symbols = {
            'info': '●',
            'success': '✓',
            'warning': '⚠',
            'error': '✗'
        }

        self.company_status_label.config(
            text=f"{status_symbols.get(level, '●')} {message}",
            fg=colors.get(level, self.colors['fg'])
        )

    # Phone Number Generator Methods

    def _create_phone_generator_ui(self):
        """Create the phone number generator tool interface."""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg'], padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with back button
        self._create_header(main_frame, "Phone Number Generator", show_back=True)

        # Content area - 3 column layout
        content_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, pady=15)

        # Left column - Connection & Table
        left_frame = tk.Frame(content_frame, bg=self.colors['bg'], width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        left_frame.pack_propagate(False)

        self._create_phone_connection_panel(left_frame)
        self._create_phone_table_selection_panel(left_frame)

        # Middle column - Data Grid & SQL Preview
        middle_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8)

        self._create_phone_data_grid_panel(middle_frame)
        self._create_phone_sql_preview_panel(middle_frame)

        # Right column - Configuration & Actions
        right_frame = tk.Frame(content_frame, bg=self.colors['bg'], width=360)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(8, 0))
        right_frame.pack_propagate(False)

        # Create scrollable frame for right column
        phone_right_canvas = tk.Canvas(right_frame, bg=self.colors['bg'], highlightthickness=0)
        phone_right_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=phone_right_canvas.yview)
        phone_right_scrollable = tk.Frame(phone_right_canvas, bg=self.colors['bg'])

        def update_phone_scrollregion(e=None):
            phone_right_canvas.configure(scrollregion=phone_right_canvas.bbox("all"))

        phone_right_scrollable.bind("<Configure>", update_phone_scrollregion)

        phone_right_canvas.create_window((0, 0), window=phone_right_scrollable, anchor="nw", width=340)
        phone_right_canvas.configure(yscrollcommand=phone_right_scrollbar.set)

        # Enable mousewheel scrolling
        def on_phone_mousewheel(event):
            phone_right_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        phone_right_canvas.bind_all("<MouseWheel>", on_phone_mousewheel)

        phone_right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        phone_right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._create_phone_column_selection_panel(phone_right_scrollable)
        self._create_phone_config_panel(phone_right_scrollable)
        self._create_phone_action_panel(phone_right_scrollable)

        # Footer - Status & Logs
        self._create_phone_footer(main_frame)

    def _create_phone_connection_panel(self, parent):
        """Create database connection panel for phone generator."""
        content = self._create_panel(parent, "📊 Database Connection")

        # Connection inputs (same as others)
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
            command=self._test_phone_connection,
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

    def _create_phone_table_selection_panel(self, parent):
        """Create table selection panel for phone generator."""
        content = self._create_panel(parent, "📋 Table Selection")

        # Table dropdown
        tk.Label(
            content,
            text="Table:",
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        self.phone_table_combo = ttk.Combobox(
            content,
            textvariable=self.phone_selected_table,
            state='readonly',
            font=('Segoe UI', 9)
        )
        self.phone_table_combo.pack(fill=tk.X, pady=(0, 8))
        self.phone_table_combo.bind('<<ComboboxSelected>>', self._on_phone_table_selected)

        # Refresh button
        refresh_btn = tk.Button(
            content,
            text="🔄 Refresh Sample Data",
            command=self._refresh_phone_table_data,
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
        self.phone_row_count_label = tk.Label(
            content,
            text="Total Rows: -",
            font=('Segoe UI', 9),
            fg=self.colors['text_secondary'],
            bg=self.colors['secondary_bg'],
            anchor='w'
        )
        self.phone_row_count_label.pack(anchor='w')

    def _create_phone_data_grid_panel(self, parent):
        """Create data grid panel for phone generator."""
        content = self._create_panel(parent, "📊 Sample Data (Top 10 Rows)", height=300)

        # Create Treeview with scrollbars
        tree_frame = tk.Frame(content, bg=self.colors['secondary_bg'])
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        self.phone_data_tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            style="Custom.Treeview",
            selectmode='browse'
        )

        vsb.config(command=self.phone_data_tree.yview)
        hsb.config(command=self.phone_data_tree.xview)

        # Grid layout
        self.phone_data_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

    def _create_phone_sql_preview_panel(self, parent):
        """Create SQL preview panel for phone generator."""
        content = self._create_panel(parent, "🔍 SQL Preview", height=150)

        self.phone_sql_preview = scrolledtext.ScrolledText(
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
        self.phone_sql_preview.pack(fill=tk.BOTH, expand=True)

        # Insert placeholder
        self.phone_sql_preview.insert(1.0, "-- Click 'Generate SQL' to preview the UPDATE statement\n-- Configuration: Select columns and phone number format first")
        self.phone_sql_preview.config(state='disabled')

    def _create_phone_column_selection_panel(self, parent):
        """Create column selection panel for phone generator."""
        panel_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT)
        panel_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        # Panel header
        header = tk.Frame(panel_frame, bg=self.colors['tertiary_bg'], height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="🎯 1. Column Selection",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['tertiary_bg']
        )
        title_label.pack(side=tk.LEFT, padx=12, pady=6)

        # Panel content
        content = tk.Frame(panel_frame, bg=self.colors['secondary_bg'], padx=12, pady=12)
        content.pack(fill=tk.X, expand=False)

        # Phone number columns
        tk.Label(
            content,
            text="Phone Number Columns (select multiple):",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        # Listbox for multiple selection
        listbox_frame = tk.Frame(content, bg=self.colors['secondary_bg'], height=100)
        listbox_frame.pack(fill=tk.X, pady=(0, 8))
        listbox_frame.pack_propagate(False)

        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.phone_columns_listbox = tk.Listbox(
            listbox_frame,
            listvariable=self.phone_columns_listvar,
            selectmode=tk.MULTIPLE,
            font=('Segoe UI', 9),
            bg=self.colors['tertiary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            yscrollcommand=scrollbar.set,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=self.colors['border'],
            selectbackground=self.colors['accent']
        )
        self.phone_columns_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=self.phone_columns_listbox.yview)

    def _create_phone_config_panel(self, parent):
        """Create phone number configuration panel."""
        panel_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT)
        panel_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        # Panel header
        header = tk.Frame(panel_frame, bg=self.colors['tertiary_bg'], height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="⚙ 2. Phone Number Format",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['tertiary_bg']
        )
        title_label.pack(side=tk.LEFT, padx=12, pady=6)

        # Panel content
        content = tk.Frame(panel_frame, bg=self.colors['secondary_bg'], padx=12, pady=12)
        content.pack(fill=tk.X, expand=False)

        # Country Code
        tk.Label(
            content,
            text="Country Code:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        country_frame = tk.Frame(content, bg=self.colors['secondary_bg'])
        country_frame.pack(fill=tk.X, pady=(0, 12))

        self.phone_country_combo = ttk.Combobox(
            country_frame,
            textvariable=self.phone_country_code,
            font=('Segoe UI', 9),
            width=15
        )
        self.phone_country_combo['values'] = [f"{country} ({code})" for country, code in
                                               PhoneNumberGenerator.COUNTRY_CODES.items() if code]
        self.phone_country_combo.pack(fill=tk.X)
        self.phone_country_combo.bind('<<ComboboxSelected>>', self._on_country_selected)

        # Prefix
        tk.Label(
            content,
            text="Prefix (after country code):",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        prefix_entry = tk.Entry(
            content,
            textvariable=self.phone_prefix,
            font=('Segoe UI', 9),
            bg=self.colors['tertiary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            bd=1
        )
        prefix_entry.pack(fill=tk.X, pady=(0, 12))

        # Number Range
        tk.Label(
            content,
            text="Number Range:",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 6))

        # Min Number
        tk.Label(
            content,
            text="Minimum Number:",
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        min_entry = tk.Entry(
            content,
            textvariable=self.phone_min_number,
            font=('Segoe UI', 9),
            bg=self.colors['tertiary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            bd=1
        )
        min_entry.pack(fill=tk.X, pady=(0, 8))

        # Max Number
        tk.Label(
            content,
            text="Maximum Number:",
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        max_entry = tk.Entry(
            content,
            textvariable=self.phone_max_number,
            font=('Segoe UI', 9),
            bg=self.colors['tertiary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            bd=1
        )
        max_entry.pack(fill=tk.X, pady=(0, 8))

        # Example
        self.phone_example_label = tk.Label(
            content,
            text="Example: +256784464178",
            font=('Segoe UI', 8, 'italic'),
            fg=self.colors['text_secondary'],
            bg=self.colors['secondary_bg'],
            anchor='w'
        )
        self.phone_example_label.pack(anchor='w')

        # Row Filter
        tk.Label(
            content,
            text="Row Filter (Optional):",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(15, 6))

        # Filter Column
        tk.Label(
            content,
            text="Filter Column:",
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 3))

        self.phone_filter_column_combo = ttk.Combobox(
            content,
            textvariable=self.phone_filter_column_var,
            state='readonly',
            font=('Segoe UI', 9)
        )
        self.phone_filter_column_combo.pack(fill=tk.X, pady=(0, 8))

        # Filter Value
        tk.Label(
            content,
            text="Filter Value:",
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 3))

        filter_value_entry = tk.Entry(
            content,
            textvariable=self.phone_filter_value_var,
            font=('Segoe UI', 9),
            bg=self.colors['grid_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            borderwidth=1
        )
        filter_value_entry.pack(fill=tk.X, pady=(0, 8))

        # ONLY NULL checkbox
        only_null_cb = tk.Checkbutton(
            content,
            text="  ONLY NULL (update only rows where phone columns are NULL)",
            variable=self.phone_only_null_var,
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg'],
            selectcolor=self.colors['tertiary_bg'],
            activebackground=self.colors['secondary_bg']
        )
        only_null_cb.pack(anchor='w', pady=(8, 8))

        # Help text
        tk.Label(
            content,
            text="Filter: Match specific value | ONLY NULL: Update empty values only",
            font=('Segoe UI', 8),
            fg=self.colors['text_secondary'],
            bg=self.colors['secondary_bg'],
            wraplength=320,
            justify='left'
        ).pack(anchor='w')

    def _create_phone_action_panel(self, parent):
        """Create action buttons panel for phone generator."""
        panel_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT)
        panel_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        # Panel header
        header = tk.Frame(panel_frame, bg=self.colors['tertiary_bg'], height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="🚀 3. Execute",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['tertiary_bg']
        )
        title_label.pack(side=tk.LEFT, padx=12, pady=6)

        # Panel content
        content = tk.Frame(panel_frame, bg=self.colors['secondary_bg'], padx=12, pady=12)
        content.pack(fill=tk.X, expand=False)

        # Generate SQL button
        generate_btn = tk.Button(
            content,
            text="📝 Generate SQL Statement",
            command=self._generate_phone_sql,
            bg=self.colors['info'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            borderwidth=0
        )
        generate_btn.pack(fill=tk.X, pady=(0, 10))

        # Preview button
        preview_btn = tk.Button(
            content,
            text="👁 Preview Changes (10 samples)",
            command=self._preview_phone_changes,
            bg=self.colors['warning'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            borderwidth=0
        )
        preview_btn.pack(fill=tk.X, pady=(0, 10))

        # Execute button
        execute_btn = tk.Button(
            content,
            text="▶ Run Query (Update Phone Numbers)",
            command=self._execute_phone_update,
            bg=self.colors['success'],
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=12,
            cursor='hand2',
            borderwidth=0
        )
        execute_btn.pack(fill=tk.X, pady=(0, 30))  # Add bottom padding for scrollability

    def _create_phone_footer(self, parent):
        """Create footer with status and logs for phone generator."""
        footer_frame = tk.Frame(parent, bg=self.colors['bg'])
        footer_frame.pack(fill=tk.BOTH, expand=False, pady=(10, 0))

        # Status label
        self.phone_status_label = tk.Label(
            footer_frame,
            text="● Ready - Connect to database to begin",
            font=('Segoe UI', 9),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg'],
            anchor='w'
        )
        self.phone_status_label.pack(fill=tk.X, pady=(0, 4))

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

        self.phone_log_text = scrolledtext.ScrolledText(
            log_frame,
            height=5,
            font=('Courier New', 8),
            bg=self.colors['secondary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            wrap=tk.WORD,
            borderwidth=0
        )
        self.phone_log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    # Phone Generator Event Handlers

    def _test_phone_connection(self):
        """Test database connection and load tables for phone generator."""
        # Show critical warning before connecting
        confirm = messagebox.askokcancel(
            "⚠ CRITICAL WARNING - Development/Testing Only",
            "THIS TOOL IS FOR DEVELOPMENT AND TESTING DATABASES ONLY!\n\n"
            "By clicking OK, you confirm that:\n\n"
            "✓ This is a development or testing database\n"
            "✓ This is NOT a production database\n"
            "✓ You understand this tool will randomly modify data\n"
            "✓ You have backups if needed\n\n"
            "⚠ NEVER USE THIS ON PRODUCTION DATABASES ⚠\n\n"
            "Are you absolutely sure you want to connect?",
            icon='warning'
        )

        if not confirm:
            self._phone_log("Connection cancelled by user", 'warning')
            return

        try:
            self._phone_log("Connecting to database...", 'info')

            self.db_manager = DatabaseManager(
                host=self.host_var.get(),
                port=int(self.port_var.get()),
                user=self.user_var.get(),
                password=self.password_var.get(),
                database=self.database_var.get() if self.database_var.get() else None
            )

            success, message = self.db_manager.test_connection()

            if success:
                self._phone_log(f"✓ {message}", 'success')

                # Initialize phone generator
                self.phone_generator = PhoneNumberGenerator(
                    host=self.host_var.get(),
                    port=int(self.port_var.get()),
                    user=self.user_var.get(),
                    password=self.password_var.get(),
                    database=self.database_var.get()
                )

                self._load_phone_tables()
            else:
                self._phone_log(f"✗ {message}", 'error')
                messagebox.showerror("Connection Error", message)

        except Exception as e:
            self._phone_log(f"✗ Connection error: {e}", 'error')
            messagebox.showerror("Error", str(e))

    def _load_phone_tables(self):
        """Load tables from database for phone generator."""
        try:
            tables = self.db_manager.get_tables(self.database_var.get())

            if tables:
                self.phone_table_combo['values'] = tables
                self._phone_log(f"Loaded {len(tables)} tables", 'info')
            else:
                self._phone_log("No tables found in database", 'warning')

        except Exception as e:
            self._phone_log(f"Error loading tables: {e}", 'error')

    def _on_phone_table_selected(self, event):
        """Handle table selection for phone generator."""
        table = self.phone_selected_table.get()

        if table and self.db_manager:
            self._phone_log(f"Loading table: {table}", 'info')

            # Get schema
            schema = self.db_manager.get_table_schema(table, self.database_var.get())

            if schema:
                # Store available columns
                self.phone_available_columns = [col['Field'] for col in schema]

                # Populate filter column dropdown
                self.phone_filter_column_combo['values'] = [''] + self.phone_available_columns

                # Populate phone columns listbox
                self.phone_columns_listbox.delete(0, tk.END)
                for col in self.phone_available_columns:
                    self.phone_columns_listbox.insert(tk.END, col)

                # Auto-select columns with 'phone' or 'tel' in name
                phone_keywords = ['phone', 'tel', 'mobile', 'contact']
                for i, col in enumerate(self.phone_available_columns):
                    if any(keyword in col.lower() for keyword in phone_keywords):
                        self.phone_columns_listbox.selection_set(i)

                # Load row count
                count = self.db_manager.get_row_count(table, None, self.database_var.get())
                self.phone_row_count_label.config(text=f"Total Rows: {count:,}")

                # Load data grid
                self._refresh_phone_table_data()

    def _refresh_phone_table_data(self):
        """Refresh the data grid with top 10 rows for phone generator."""
        table = self.phone_selected_table.get()

        if not table or not self.db_manager:
            return

        try:
            self._phone_log("Refreshing sample data...", 'info')

            # Get top 10 rows
            data = self.db_manager.get_sample_data(table, limit=10, database=self.database_var.get())

            if data:
                # Clear existing data
                for item in self.phone_data_tree.get_children():
                    self.phone_data_tree.delete(item)

                # Configure columns
                columns = list(data[0].keys())
                self.phone_data_tree['columns'] = columns
                self.phone_data_tree['show'] = 'headings'

                # Configure column headings
                for col in columns:
                    self.phone_data_tree.heading(col, text=col)
                    # Set column width based on content
                    max_width = max(len(col) * 8, 100)
                    self.phone_data_tree.column(col, width=max_width, minwidth=80)

                # Insert data
                for row in data:
                    values = [str(row[col]) if row[col] is not None else '' for col in columns]
                    self.phone_data_tree.insert('', tk.END, values=values)

                self._phone_log(f"✓ Loaded {len(data)} rows", 'success')
            else:
                self._phone_log("No data in table", 'warning')

        except Exception as e:
            self._phone_log(f"Error loading data: {e}", 'error')

    def _get_selected_phone_columns(self) -> List[str]:
        """Get selected phone columns from listbox."""
        selected_indices = self.phone_columns_listbox.curselection()
        return [self.phone_available_columns[i] for i in selected_indices]

    def _on_country_selected(self, event):
        """Handle country code selection."""
        selected = self.phone_country_combo.get()
        # Extract country code from selection like "Uganda (+256)"
        if '(' in selected and ')' in selected:
            code = selected.split('(')[1].split(')')[0]
            self.phone_country_code.set(code)

        # Update example
        self._update_phone_example()

    def _update_phone_example(self):
        """Update the example phone number display."""
        try:
            country_code = self.phone_country_code.get()
            prefix = self.phone_prefix.get()
            min_num = int(self.phone_min_number.get())
            max_num = int(self.phone_max_number.get())

            # Generate example with midpoint
            mid_num = (min_num + max_num) // 2
            example = f"Example: {country_code}{prefix}{mid_num}"
            self.phone_example_label.config(text=example)
        except:
            self.phone_example_label.config(text="Example: +256784464178")

    def _generate_phone_sql(self):
        """Generate SQL UPDATE statement for phone generator."""
        if not self._validate_phone_config():
            return

        try:
            table = self.phone_selected_table.get()
            phone_cols = self._get_selected_phone_columns()
            country_code = self.phone_country_code.get()
            prefix = self.phone_prefix.get()
            min_num = self.phone_min_number.get()
            max_num = self.phone_max_number.get()

            # Build sample SQL
            set_clauses = ", ".join([f"`{col}` = '[RandomPhoneNumber]'" for col in phone_cols])

            sql = f"""-- Generated UPDATE statement
-- This will update phone numbers in batches of 1000 rows with transaction safety

UPDATE `{table}`
SET {set_clauses}
LIMIT 1000;  -- Batch size (repeats until all rows updated)

-- Configuration:
-- Country Code: {country_code}
-- Prefix: {prefix}
-- Number Range: {min_num} to {max_num}
-- Columns to update: {', '.join(phone_cols)}
--
-- Format: {country_code}{prefix}[RandomNumber]
-- Example: {country_code}{prefix}{int(min_num) + (int(max_num) - int(min_num)) // 2}
--
-- Click 'Preview Changes' to see sample before/after
-- Click 'Run Query' to execute the update"""

            # Update preview
            self.phone_sql_preview.config(state='normal')
            self.phone_sql_preview.delete(1.0, tk.END)
            self.phone_sql_preview.insert(1.0, sql)
            self.phone_sql_preview.config(state='disabled')

            self._phone_log("✓ SQL statement generated", 'success')

        except Exception as e:
            self._phone_log(f"Error generating SQL: {e}", 'error')

    def _preview_phone_changes(self):
        """Preview changes with actual sample data for phone generator."""
        if not self._validate_phone_config():
            return

        try:
            self._phone_log("Generating preview...", 'info')

            config = self._build_phone_config()
            preview = self.phone_generator.preview_changes(config, limit=10)

            # Show preview in a new window
            self._show_phone_preview_window(preview)

            self._phone_log(f"✓ Preview generated ({len(preview)} samples)", 'success')

        except Exception as e:
            error_details = str(e)
            self._phone_log(f"✗ Preview generation failed: {error_details}", 'error')

            # Log full traceback for debugging
            import traceback
            tb = traceback.format_exc()
            self._phone_log(f"Traceback:\n{tb}", 'error')

            messagebox.showerror("Preview Error", f"{error_details}\n\nCheck Activity Log for full details.")

    def _show_phone_preview_window(self, preview_data):
        """Show preview in a popup window for phone generator."""
        preview_win = tk.Toplevel(self.root)
        preview_win.title("Preview Changes - Phone Numbers")
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

    def _execute_phone_update(self):
        """Execute the phone number update."""
        if not self._validate_phone_config():
            return

        # Confirmation dialog
        phone_cols = self._get_selected_phone_columns()
        table = self.phone_selected_table.get()
        country_code = self.phone_country_code.get()
        prefix = self.phone_prefix.get()
        min_num = self.phone_min_number.get()
        max_num = self.phone_max_number.get()

        msg = f"""Are you sure you want to run this query?

Table: {table}
Columns: {', '.join(phone_cols)}
Country Code: {country_code}
Prefix: {prefix}
Range: {min_num} to {max_num}

This will modify your database.
Transactions will be used (can rollback on error)."""

        if not messagebox.askyesno("Confirm Query Execution", msg):
            return

        try:
            self._phone_log("Running query...", 'info')
            self.phone_status_label.config(text="● Running query... Please wait", fg=self.colors['warning'])
            self.root.update()

            config = self._build_phone_config()
            result = self.phone_generator.execute_update(config, dry_run=False)

            # Log all errors to activity log
            if result['errors']:
                self._phone_log(f"⚠ {len(result['errors'])} error(s) occurred during execution:", 'warning')
                for i, error in enumerate(result['errors'][:10], 1):  # Show first 10 errors
                    self._phone_log(f"  Error {i}: {error}", 'error')
                if len(result['errors']) > 10:
                    self._phone_log(f"  ... and {len(result['errors']) - 10} more errors", 'error')

            # Show results
            success_msg = f"""Query Completed!

Total Rows: {result['total_rows']}
Updated: {result['updated_rows']}
Skipped: {result['skipped_rows']}
Errors: {len(result['errors'])}"""

            if result['errors']:
                success_msg += f"\n\nCheck Activity Log for error details."
                success_msg += f"\nFirst error: {result['errors'][0]}"

            self._phone_log(f"✓ Query complete: {result['updated_rows']} rows updated, {result['skipped_rows']} skipped", 'success' if len(result['errors']) == 0 else 'warning')

            if len(result['errors']) > 0:
                messagebox.showwarning("Query Completed with Errors", success_msg)
            else:
                messagebox.showinfo("Query Complete", success_msg)

            # Auto-refresh sample data
            self._phone_log("Auto-refreshing sample data...", 'info')
            self._refresh_phone_table_data()

        except Exception as e:
            error_details = str(e)
            self._phone_log(f"✗ Query failed: {error_details}", 'error')

            # Log full traceback for debugging
            import traceback
            tb = traceback.format_exc()
            self._phone_log(f"Traceback:\n{tb}", 'error')

            messagebox.showerror("Query Error", f"Query failed:\n\n{error_details}\n\nCheck Activity Log for full details.")
        finally:
            self.phone_status_label.config(text="● Ready", fg=self.colors['text_secondary'])

    def _validate_phone_config(self) -> bool:
        """Validate current configuration for phone generator."""
        if not self.db_manager:
            messagebox.showerror("Error", "Please connect to database first")
            return False

        if not self.phone_selected_table.get():
            messagebox.showerror("Error", "Please select a table")
            return False

        if not self._get_selected_phone_columns():
            messagebox.showerror("Error", "Please select at least one phone column")
            return False

        if not self.phone_country_code.get():
            messagebox.showerror("Error", "Please enter a country code")
            return False

        try:
            min_num = int(self.phone_min_number.get())
            max_num = int(self.phone_max_number.get())

            if min_num >= max_num:
                messagebox.showerror("Error", "Maximum number must be greater than minimum number")
                return False

            if min_num < 0 or max_num < 0:
                messagebox.showerror("Error", "Numbers must be positive")
                return False

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for range")
            return False

        return True

    def _build_phone_config(self) -> Dict[str, Any]:
        """Build configuration dictionary for phone generator."""
        # Build where clause from filter if provided
        where_clause = None
        filter_col = self.phone_filter_column_var.get()
        filter_val = self.phone_filter_value_var.get()
        if filter_col and filter_val:
            # Escape the value to prevent SQL injection
            escaped_val = filter_val.replace("'", "''")
            where_clause = f"`{filter_col}` = '{escaped_val}'"

        return {
            'table': self.phone_selected_table.get(),
            'phone_columns': self._get_selected_phone_columns(),
            'country_code': self.phone_country_code.get(),
            'prefix': self.phone_prefix.get(),
            'min_number': int(self.phone_min_number.get()),
            'max_number': int(self.phone_max_number.get()),
            'batch_size': 1000,
            'preserve_null': False,  # Update NULL values too
            'primary_key': 'id',
            'where_clause': where_clause
        }

    def _phone_log(self, message: str, level: str = 'info'):
        """Log message to phone generator console."""
        colors = {
            'info': self.colors['fg'],
            'success': self.colors['success'],
            'warning': self.colors['warning'],
            'error': self.colors['error']
        }

        timestamp = __import__('datetime').datetime.now().strftime('%H:%M:%S')
        self.phone_log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.phone_log_text.see(tk.END)

        status_symbols = {
            'info': '●',
            'success': '✓',
            'warning': '⚠',
            'error': '✗'
        }

        self.phone_status_label.config(
            text=f"{status_symbols.get(level, '●')} {message}",
            fg=colors.get(level, self.colors['fg'])
        )

    # Date Randomizer Methods

    def _create_date_randomizer_ui(self):
        """Create the date randomizer tool interface."""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg'], padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with back button
        self._create_header(main_frame, "Date Randomizer", show_back=True)

        # Content area - 3 column layout
        content_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, pady=15)

        # Left column - Connection & Table
        left_frame = tk.Frame(content_frame, bg=self.colors['bg'], width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        left_frame.pack_propagate(False)

        self._create_date_connection_panel(left_frame)
        self._create_date_table_selection_panel(left_frame)

        # Middle column - Data Grid & SQL Preview
        middle_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8)

        self._create_date_data_grid_panel(middle_frame)
        self._create_date_sql_preview_panel(middle_frame)

        # Right column - Configuration & Actions
        right_frame = tk.Frame(content_frame, bg=self.colors['bg'], width=360)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(8, 0))
        right_frame.pack_propagate(False)

        # Create scrollable frame for right column
        date_right_canvas = tk.Canvas(right_frame, bg=self.colors['bg'], highlightthickness=0)
        date_right_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=date_right_canvas.yview)
        date_right_scrollable = tk.Frame(date_right_canvas, bg=self.colors['bg'])

        def update_date_scrollregion(e=None):
            date_right_canvas.configure(scrollregion=date_right_canvas.bbox("all"))

        date_right_scrollable.bind("<Configure>", update_date_scrollregion)

        date_right_canvas.create_window((0, 0), window=date_right_scrollable, anchor="nw", width=340)
        date_right_canvas.configure(yscrollcommand=date_right_scrollbar.set)

        # Enable mousewheel scrolling
        def on_date_mousewheel(event):
            date_right_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        date_right_canvas.bind_all("<MouseWheel>", on_date_mousewheel)

        date_right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        date_right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._create_date_column_selection_panel(date_right_scrollable)
        self._create_date_config_panel(date_right_scrollable)
        self._create_date_action_panel(date_right_scrollable)

        # Footer - Status & Logs
        self._create_date_footer(main_frame)

    def _create_date_connection_panel(self, parent):
        """Create database connection panel for date randomizer."""
        content = self._create_panel(parent, "📊 Database Connection")

        # Connection inputs (same as others)
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
            command=self._test_date_connection,
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

    def _create_date_table_selection_panel(self, parent):
        """Create table selection panel for date randomizer."""
        content = self._create_panel(parent, "📋 Table Selection")

        # Table dropdown
        tk.Label(
            content,
            text="Table:",
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        self.date_table_combo = ttk.Combobox(
            content,
            textvariable=self.date_selected_table,
            state='readonly',
            font=('Segoe UI', 9)
        )
        self.date_table_combo.pack(fill=tk.X, pady=(0, 8))
        self.date_table_combo.bind('<<ComboboxSelected>>', self._on_date_table_selected)

        # Refresh button
        refresh_btn = tk.Button(
            content,
            text="🔄 Refresh Sample Data",
            command=self._refresh_date_table_data,
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
        self.date_row_count_label = tk.Label(
            content,
            text="Total Rows: -",
            font=('Segoe UI', 9),
            fg=self.colors['text_secondary'],
            bg=self.colors['secondary_bg'],
            anchor='w'
        )
        self.date_row_count_label.pack(anchor='w')

    def _create_date_data_grid_panel(self, parent):
        """Create data grid panel for date randomizer."""
        content = self._create_panel(parent, "📊 Sample Data (Top 10 Rows)", height=300)

        # Create Treeview with scrollbars
        tree_frame = tk.Frame(content, bg=self.colors['secondary_bg'])
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        self.date_data_tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            style="Custom.Treeview",
            selectmode='browse'
        )

        vsb.config(command=self.date_data_tree.yview)
        hsb.config(command=self.date_data_tree.xview)

        # Grid layout
        self.date_data_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

    def _create_date_sql_preview_panel(self, parent):
        """Create SQL preview panel for date randomizer."""
        content = self._create_panel(parent, "🔍 SQL Preview", height=150)

        self.date_sql_preview = scrolledtext.ScrolledText(
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
        self.date_sql_preview.pack(fill=tk.BOTH, expand=True)

        # Insert placeholder
        self.date_sql_preview.insert(1.0, "-- Click 'Generate SQL' to preview the UPDATE statement\n-- Configuration: Select date columns and date range first")
        self.date_sql_preview.config(state='disabled')

    def _create_date_column_selection_panel(self, parent):
        """Create column selection panel for date randomizer."""
        panel_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT)
        panel_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        # Panel header
        header = tk.Frame(panel_frame, bg=self.colors['tertiary_bg'], height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="🎯 1. Column Selection",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['tertiary_bg']
        )
        title_label.pack(side=tk.LEFT, padx=12, pady=6)

        # Panel content
        content = tk.Frame(panel_frame, bg=self.colors['secondary_bg'], padx=12, pady=12)
        content.pack(fill=tk.X, expand=False)

        # Date/Datetime columns
        tk.Label(
            content,
            text="Date/Datetime Columns (select multiple):",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        # Info label
        tk.Label(
            content,
            text="Only DATE, DATETIME, and TIMESTAMP columns shown",
            font=('Segoe UI', 8, 'italic'),
            fg=self.colors['text_secondary'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        # Listbox for multiple selection
        listbox_frame = tk.Frame(content, bg=self.colors['secondary_bg'], height=120)
        listbox_frame.pack(fill=tk.X, pady=(0, 8))
        listbox_frame.pack_propagate(False)

        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.date_columns_listbox = tk.Listbox(
            listbox_frame,
            listvariable=self.date_columns_listvar,
            selectmode=tk.MULTIPLE,
            font=('Segoe UI', 9),
            bg=self.colors['tertiary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            yscrollcommand=scrollbar.set,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=self.colors['border'],
            selectbackground=self.colors['accent']
        )
        self.date_columns_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=self.date_columns_listbox.yview)

    def _create_date_config_panel(self, parent):
        """Create date configuration panel."""
        panel_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT)
        panel_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        # Panel header
        header = tk.Frame(panel_frame, bg=self.colors['tertiary_bg'], height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="⚙ 2. Date Range Configuration",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['tertiary_bg']
        )
        title_label.pack(side=tk.LEFT, padx=12, pady=6)

        # Panel content
        content = tk.Frame(panel_frame, bg=self.colors['secondary_bg'], padx=12, pady=12)
        content.pack(fill=tk.X, expand=False)

        # Quick date presets
        tk.Label(
            content,
            text="Quick Presets:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        presets_frame = tk.Frame(content, bg=self.colors['secondary_bg'])
        presets_frame.pack(fill=tk.X, pady=(0, 12))

        presets = [
            ("Last Year", 365),
            ("Last 6 Months", 180),
            ("Last 3 Months", 90),
            ("Last Month", 30),
            ("This Year", 0)
        ]

        for preset_name, days_ago in presets:
            btn = tk.Button(
                presets_frame,
                text=preset_name,
                command=lambda d=days_ago: self._set_date_preset(d),
                bg=self.colors['tertiary_bg'],
                fg=self.colors['fg'],
                font=('Segoe UI', 8),
                relief=tk.FLAT,
                padx=8,
                pady=4,
                cursor='hand2'
            )
            btn.pack(side=tk.LEFT, padx=2)

        # Start Date
        tk.Label(
            content,
            text="Start Date:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        start_frame = tk.Frame(content, bg=self.colors['secondary_bg'])
        start_frame.pack(fill=tk.X, pady=(0, 12))

        # Year, Month, Day dropdowns for start date
        tk.Label(start_frame, text="Year:", bg=self.colors['secondary_bg'], font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(0, 4))
        self.date_start_year = ttk.Combobox(start_frame, width=6, font=('Segoe UI', 9))
        self.date_start_year['values'] = list(range(2020, 2031))
        self.date_start_year.set(2024)
        self.date_start_year.pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(start_frame, text="Month:", bg=self.colors['secondary_bg'], font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(0, 4))
        self.date_start_month = ttk.Combobox(start_frame, width=4, font=('Segoe UI', 9))
        self.date_start_month['values'] = list(range(1, 13))
        self.date_start_month.set(1)
        self.date_start_month.pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(start_frame, text="Day:", bg=self.colors['secondary_bg'], font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(0, 4))
        self.date_start_day = ttk.Combobox(start_frame, width=4, font=('Segoe UI', 9))
        self.date_start_day['values'] = list(range(1, 32))
        self.date_start_day.set(1)
        self.date_start_day.pack(side=tk.LEFT)

        # End Date
        tk.Label(
            content,
            text="End Date:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        end_frame = tk.Frame(content, bg=self.colors['secondary_bg'])
        end_frame.pack(fill=tk.X, pady=(0, 12))

        # Year, Month, Day dropdowns for end date
        tk.Label(end_frame, text="Year:", bg=self.colors['secondary_bg'], font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(0, 4))
        self.date_end_year = ttk.Combobox(end_frame, width=6, font=('Segoe UI', 9))
        self.date_end_year['values'] = list(range(2020, 2031))
        self.date_end_year.set(2026)
        self.date_end_year.pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(end_frame, text="Month:", bg=self.colors['secondary_bg'], font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(0, 4))
        self.date_end_month = ttk.Combobox(end_frame, width=4, font=('Segoe UI', 9))
        self.date_end_month['values'] = list(range(1, 13))
        self.date_end_month.set(12)
        self.date_end_month.pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(end_frame, text="Day:", bg=self.colors['secondary_bg'], font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(0, 4))
        self.date_end_day = ttk.Combobox(end_frame, width=4, font=('Segoe UI', 9))
        self.date_end_day['values'] = list(range(1, 32))
        self.date_end_day.set(31)
        self.date_end_day.pack(side=tk.LEFT)

        # Include Time checkbox
        include_time_cb = tk.Checkbutton(
            content,
            text="  Include Time Component (for DATETIME columns)",
            variable=self.date_include_time,
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg'],
            selectcolor=self.colors['tertiary_bg'],
            activebackground=self.colors['secondary_bg']
        )
        include_time_cb.pack(anchor='w', pady=(0, 4))

        # Date range preview
        self.date_range_preview = tk.Label(
            content,
            text="Date Range: -",
            font=('Segoe UI', 8, 'italic'),
            fg=self.colors['text_secondary'],
            bg=self.colors['secondary_bg'],
            anchor='w'
        )
        self.date_range_preview.pack(anchor='w')

        # Row Filter
        tk.Label(
            content,
            text="Row Filter (Optional):",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(15, 6))

        # Filter Column
        tk.Label(
            content,
            text="Filter Column:",
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 3))

        self.date_filter_column_combo = ttk.Combobox(
            content,
            textvariable=self.date_filter_column_var,
            state='readonly',
            font=('Segoe UI', 9)
        )
        self.date_filter_column_combo.pack(fill=tk.X, pady=(0, 8))

        # Filter Value
        tk.Label(
            content,
            text="Filter Value:",
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 3))

        filter_value_entry = tk.Entry(
            content,
            textvariable=self.date_filter_value_var,
            font=('Segoe UI', 9),
            bg=self.colors['grid_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            borderwidth=1
        )
        filter_value_entry.pack(fill=tk.X, pady=(0, 8))

        # Help text
        tk.Label(
            content,
            text="Only update rows where Filter Column = Filter Value",
            font=('Segoe UI', 8),
            fg=self.colors['text_secondary'],
            bg=self.colors['secondary_bg'],
            wraplength=320,
            justify='left'
        ).pack(anchor='w')

    def _create_date_action_panel(self, parent):
        """Create action buttons panel for date randomizer."""
        panel_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT)
        panel_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        # Panel header
        header = tk.Frame(panel_frame, bg=self.colors['tertiary_bg'], height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="🚀 3. Execute",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['tertiary_bg']
        )
        title_label.pack(side=tk.LEFT, padx=12, pady=6)

        # Panel content
        content = tk.Frame(panel_frame, bg=self.colors['secondary_bg'], padx=12, pady=12)
        content.pack(fill=tk.X, expand=False)

        # Generate SQL button
        generate_btn = tk.Button(
            content,
            text="📝 Generate SQL Statement",
            command=self._generate_date_sql,
            bg=self.colors['info'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            borderwidth=0
        )
        generate_btn.pack(fill=tk.X, pady=(0, 10))

        # Preview button
        preview_btn = tk.Button(
            content,
            text="👁 Preview Changes (10 samples)",
            command=self._preview_date_changes,
            bg=self.colors['warning'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            borderwidth=0
        )
        preview_btn.pack(fill=tk.X, pady=(0, 10))

        # Execute button
        execute_btn = tk.Button(
            content,
            text="▶ Run Query (Update Dates)",
            command=self._execute_date_update,
            bg=self.colors['success'],
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=12,
            cursor='hand2',
            borderwidth=0
        )
        execute_btn.pack(fill=tk.X, pady=(0, 30))  # Add bottom padding for scrollability

    def _create_date_footer(self, parent):
        """Create footer with status and logs for date randomizer."""
        footer_frame = tk.Frame(parent, bg=self.colors['bg'])
        footer_frame.pack(fill=tk.BOTH, expand=False, pady=(10, 0))

        # Status label
        self.date_status_label = tk.Label(
            footer_frame,
            text="● Ready - Connect to database to begin",
            font=('Segoe UI', 9),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg'],
            anchor='w'
        )
        self.date_status_label.pack(fill=tk.X, pady=(0, 4))

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

        self.date_log_text = scrolledtext.ScrolledText(
            log_frame,
            height=5,
            font=('Courier New', 8),
            bg=self.colors['secondary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            wrap=tk.WORD,
            borderwidth=0
        )
        self.date_log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    # Date Randomizer Event Handlers

    def _test_date_connection(self):
        """Test database connection and load tables for date randomizer."""
        # Show critical warning before connecting
        confirm = messagebox.askokcancel(
            "⚠ CRITICAL WARNING - Development/Testing Only",
            "THIS TOOL IS FOR DEVELOPMENT AND TESTING DATABASES ONLY!\n\n"
            "By clicking OK, you confirm that:\n\n"
            "✓ This is a development or testing database\n"
            "✓ This is NOT a production database\n"
            "✓ You understand this tool will randomly modify data\n"
            "✓ You have backups if needed\n\n"
            "⚠ NEVER USE THIS ON PRODUCTION DATABASES ⚠\n\n"
            "Are you absolutely sure you want to connect?",
            icon='warning'
        )

        if not confirm:
            self._date_log("Connection cancelled by user", 'warning')
            return

        try:
            self._date_log("Connecting to database...", 'info')

            self.db_manager = DatabaseManager(
                host=self.host_var.get(),
                port=int(self.port_var.get()),
                user=self.user_var.get(),
                password=self.password_var.get(),
                database=self.database_var.get() if self.database_var.get() else None
            )

            success, message = self.db_manager.test_connection()

            if success:
                self._date_log(f"✓ {message}", 'success')

                # Initialize date randomizer
                self.date_randomizer = DateRandomizer(
                    host=self.host_var.get(),
                    port=int(self.port_var.get()),
                    user=self.user_var.get(),
                    password=self.password_var.get(),
                    database=self.database_var.get()
                )

                self._load_date_tables()
            else:
                self._date_log(f"✗ {message}", 'error')
                messagebox.showerror("Connection Error", message)

        except Exception as e:
            self._date_log(f"✗ Connection error: {e}", 'error')
            messagebox.showerror("Error", str(e))

    def _load_date_tables(self):
        """Load tables from database for date randomizer."""
        try:
            tables = self.db_manager.get_tables(self.database_var.get())

            if tables:
                self.date_table_combo['values'] = tables
                self._date_log(f"Loaded {len(tables)} tables", 'info')
            else:
                self._date_log("No tables found in database", 'warning')

        except Exception as e:
            self._date_log(f"Error loading tables: {e}", 'error')

    def _on_date_table_selected(self, event):
        """Handle table selection for date randomizer."""
        table = self.date_selected_table.get()

        if table and self.date_randomizer:
            self._date_log(f"Loading table: {table}", 'info')

            # Get datetime columns
            datetime_cols = self.date_randomizer.get_datetime_columns(table, self.database_var.get())

            if datetime_cols:
                # Store available date columns
                self.date_available_columns = datetime_cols

                # Get all columns for filter dropdown
                schema = self.db_manager.get_table_schema(table, self.database_var.get())
                if schema:
                    all_columns = [col['Field'] for col in schema]
                    # Populate filter column dropdown
                    self.date_filter_column_combo['values'] = [''] + all_columns

                # Populate date columns listbox
                self.date_columns_listbox.delete(0, tk.END)
                for col_info in datetime_cols:
                    display_text = f"{col_info['name']} ({col_info['type']})"
                    self.date_columns_listbox.insert(tk.END, display_text)

                # Auto-select all date columns
                for i in range(len(datetime_cols)):
                    self.date_columns_listbox.selection_set(i)

                self._date_log(f"Found {len(datetime_cols)} date/datetime columns", 'success')
            else:
                self._date_log("No date/datetime columns found in this table", 'warning')
                messagebox.showwarning(
                    "No Date Columns",
                    "This table doesn't contain any DATE, DATETIME, or TIMESTAMP columns."
                )

            # Load row count
            count = self.db_manager.get_row_count(table, None, self.database_var.get())
            self.date_row_count_label.config(text=f"Total Rows: {count:,}")

            # Load data grid
            self._refresh_date_table_data()

    def _refresh_date_table_data(self):
        """Refresh the data grid with top 10 rows for date randomizer."""
        table = self.date_selected_table.get()

        if not table or not self.db_manager:
            return

        try:
            self._date_log("Refreshing sample data...", 'info')

            # Get top 10 rows
            data = self.db_manager.get_sample_data(table, limit=10, database=self.database_var.get())

            if data:
                # Clear existing data
                for item in self.date_data_tree.get_children():
                    self.date_data_tree.delete(item)

                # Configure columns
                columns = list(data[0].keys())
                self.date_data_tree['columns'] = columns
                self.date_data_tree['show'] = 'headings'

                # Configure column headings
                for col in columns:
                    self.date_data_tree.heading(col, text=col)
                    # Set column width based on content
                    max_width = max(len(col) * 8, 100)
                    self.date_data_tree.column(col, width=max_width, minwidth=80)

                # Insert data
                for row in data:
                    values = [str(row[col]) if row[col] is not None else '' for col in columns]
                    self.date_data_tree.insert('', tk.END, values=values)

                self._date_log(f"✓ Loaded {len(data)} rows", 'success')
            else:
                self._date_log("No data in table", 'warning')

        except Exception as e:
            self._date_log(f"Error loading data: {e}", 'error')

    def _get_selected_date_columns(self) -> List[Dict[str, str]]:
        """Get selected date columns from listbox."""
        selected_indices = self.date_columns_listbox.curselection()
        return [self.date_available_columns[i] for i in selected_indices]

    def _set_date_preset(self, days_ago: int):
        """Set date range based on preset."""
        from datetime import datetime, timedelta

        if days_ago == 0:  # This Year
            end_date = datetime.now()
            start_date = datetime(end_date.year, 1, 1)
        else:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_ago)

        # Update dropdowns
        self.date_start_year.set(start_date.year)
        self.date_start_month.set(start_date.month)
        self.date_start_day.set(start_date.day)

        self.date_end_year.set(end_date.year)
        self.date_end_month.set(end_date.month)
        self.date_end_day.set(end_date.day)

        self._update_date_range_preview()

    def _update_date_range_preview(self):
        """Update the date range preview label."""
        try:
            from datetime import datetime

            start_date = datetime(
                int(self.date_start_year.get()),
                int(self.date_start_month.get()),
                int(self.date_start_day.get())
            )
            end_date = datetime(
                int(self.date_end_year.get()),
                int(self.date_end_month.get()),
                int(self.date_end_day.get())
            )

            days_diff = (end_date - start_date).days

            preview_text = f"Date Range: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')} ({days_diff} days)"
            self.date_range_preview.config(text=preview_text)
        except:
            self.date_range_preview.config(text="Date Range: Invalid dates")

    def _generate_date_sql(self):
        """Generate SQL UPDATE statement for date randomizer."""
        if not self._validate_date_config():
            return

        try:
            from datetime import datetime

            table = self.date_selected_table.get()
            date_cols = self._get_selected_date_columns()

            start_date = datetime(
                int(self.date_start_year.get()),
                int(self.date_start_month.get()),
                int(self.date_start_day.get())
            )
            end_date = datetime(
                int(self.date_end_year.get()),
                int(self.date_end_month.get()),
                int(self.date_end_day.get())
            )

            # Build sample SQL
            set_clauses = ", ".join([f"`{col['name']}` = '[RandomDate]'" for col in date_cols])

            sql = f"""-- Generated UPDATE statement
-- This will update dates in batches of 1000 rows with transaction safety

UPDATE `{table}`
SET {set_clauses}
LIMIT 1000;  -- Batch size (repeats until all rows updated)

-- Configuration:
-- Start Date: {start_date.strftime('%Y-%m-%d')}
-- End Date: {end_date.strftime('%Y-%m-%d')}
-- Include Time: {'Yes' if self.date_include_time.get() else 'No'}
-- Columns to update: {', '.join([col['name'] for col in date_cols])}
--
-- Click 'Preview Changes' to see sample before/after
-- Click 'Run Query' to execute the update"""

            # Update preview
            self.date_sql_preview.config(state='normal')
            self.date_sql_preview.delete(1.0, tk.END)
            self.date_sql_preview.insert(1.0, sql)
            self.date_sql_preview.config(state='disabled')

            self._date_log("✓ SQL statement generated", 'success')

        except Exception as e:
            self._date_log(f"Error generating SQL: {e}", 'error')

    def _preview_date_changes(self):
        """Preview changes with actual sample data for date randomizer."""
        if not self._validate_date_config():
            return

        try:
            self._date_log("Generating preview...", 'info')

            config = self._build_date_config()
            preview = self.date_randomizer.preview_changes(config, limit=10)

            # Show preview in a new window
            self._show_date_preview_window(preview)

            self._date_log(f"✓ Preview generated ({len(preview)} samples)", 'success')

        except Exception as e:
            error_details = str(e)
            self._date_log(f"✗ Preview generation failed: {error_details}", 'error')

            # Log full traceback for debugging
            import traceback
            tb = traceback.format_exc()
            self._date_log(f"Traceback:\n{tb}", 'error')

            messagebox.showerror("Preview Error", f"{error_details}\n\nCheck Activity Log for full details.")

    def _show_date_preview_window(self, preview_data):
        """Show preview in a popup window for date randomizer."""
        preview_win = tk.Toplevel(self.root)
        preview_win.title("Preview Changes - Dates")
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

    def _execute_date_update(self):
        """Execute the date randomization update."""
        if not self._validate_date_config():
            return

        from datetime import datetime

        # Confirmation dialog
        date_cols = self._get_selected_date_columns()
        table = self.date_selected_table.get()

        start_date = datetime(
            int(self.date_start_year.get()),
            int(self.date_start_month.get()),
            int(self.date_start_day.get())
        )
        end_date = datetime(
            int(self.date_end_year.get()),
            int(self.date_end_month.get()),
            int(self.date_end_day.get())
        )

        msg = f"""Are you sure you want to run this query?

Table: {table}
Columns: {', '.join([col['name'] for col in date_cols])}
Start Date: {start_date.strftime('%B %d, %Y')}
End Date: {end_date.strftime('%B %d, %Y')}
Include Time: {'Yes' if self.date_include_time.get() else 'No'}

This will modify your database.
Transactions will be used (can rollback on error)."""

        if not messagebox.askyesno("Confirm Query Execution", msg):
            return

        try:
            self._date_log("Running query...", 'info')
            self.date_status_label.config(text="● Running query... Please wait", fg=self.colors['warning'])
            self.root.update()

            config = self._build_date_config()
            result = self.date_randomizer.execute_update(config, dry_run=False)

            # Log all errors to activity log
            if result['errors']:
                self._date_log(f"⚠ {len(result['errors'])} error(s) occurred during execution:", 'warning')
                for i, error in enumerate(result['errors'][:10], 1):  # Show first 10 errors
                    self._date_log(f"  Error {i}: {error}", 'error')
                if len(result['errors']) > 10:
                    self._date_log(f"  ... and {len(result['errors']) - 10} more errors", 'error')

            # Show results
            success_msg = f"""Query Completed!

Total Rows: {result['total_rows']}
Updated: {result['updated_rows']}
Skipped: {result['skipped_rows']}
Errors: {len(result['errors'])}"""

            if result['errors']:
                success_msg += f"\n\nCheck Activity Log for error details."
                success_msg += f"\nFirst error: {result['errors'][0]}"

            self._date_log(f"✓ Query complete: {result['updated_rows']} rows updated, {result['skipped_rows']} skipped", 'success' if len(result['errors']) == 0 else 'warning')

            if len(result['errors']) > 0:
                messagebox.showwarning("Query Completed with Errors", success_msg)
            else:
                messagebox.showinfo("Query Complete", success_msg)

            # Auto-refresh sample data
            self._date_log("Auto-refreshing sample data...", 'info')
            self._refresh_date_table_data()

        except Exception as e:
            error_details = str(e)
            self._date_log(f"✗ Query failed: {error_details}", 'error')

            # Log full traceback for debugging
            import traceback
            tb = traceback.format_exc()
            self._date_log(f"Traceback:\n{tb}", 'error')

            messagebox.showerror("Query Error", f"Query failed:\n\n{error_details}\n\nCheck Activity Log for full details.")
        finally:
            self.date_status_label.config(text="● Ready", fg=self.colors['text_secondary'])

    def _validate_date_config(self) -> bool:
        """Validate current configuration for date randomizer."""
        if not self.db_manager:
            messagebox.showerror("Error", "Please connect to database first")
            return False

        if not self.date_selected_table.get():
            messagebox.showerror("Error", "Please select a table")
            return False

        if not self._get_selected_date_columns():
            messagebox.showerror("Error", "Please select at least one date column")
            return False

        try:
            from datetime import datetime

            start_date = datetime(
                int(self.date_start_year.get()),
                int(self.date_start_month.get()),
                int(self.date_start_day.get())
            )
            end_date = datetime(
                int(self.date_end_year.get()),
                int(self.date_end_month.get()),
                int(self.date_end_day.get())
            )

            if start_date >= end_date:
                messagebox.showerror("Error", "End date must be after start date")
                return False

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid date selected: {str(e)}")
            return False

        return True

    def _build_date_config(self) -> Dict[str, Any]:
        """Build configuration dictionary for date randomizer."""
        from datetime import datetime

        start_date = datetime(
            int(self.date_start_year.get()),
            int(self.date_start_month.get()),
            int(self.date_start_day.get())
        )
        end_date = datetime(
            int(self.date_end_year.get()),
            int(self.date_end_month.get()),
            int(self.date_end_day.get())
        )

        # Build where clause from filter if provided
        where_clause = None
        filter_col = self.date_filter_column_var.get()
        filter_val = self.date_filter_value_var.get()
        if filter_col and filter_val:
            # Escape the value to prevent SQL injection
            escaped_val = filter_val.replace("'", "''")
            where_clause = f"`{filter_col}` = '{escaped_val}'"

        return {
            'table': self.date_selected_table.get(),
            'date_columns': self._get_selected_date_columns(),
            'start_date': start_date,
            'end_date': end_date,
            'include_time': self.date_include_time.get(),
            'batch_size': 1000,
            'preserve_null': False,  # Update NULL values too
            'primary_key': 'id',
            'where_clause': where_clause
        }

    def _date_log(self, message: str, level: str = 'info'):
        """Log message to date randomizer console."""
        colors = {
            'info': self.colors['fg'],
            'success': self.colors['success'],
            'warning': self.colors['warning'],
            'error': self.colors['error']
        }

        timestamp = __import__('datetime').datetime.now().strftime('%H:%M:%S')
        self.date_log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.date_log_text.see(tk.END)

        status_symbols = {
            'info': '●',
            'success': '✓',
            'warning': '⚠',
            'error': '✗'
        }

        self.date_status_label.config(
            text=f"{status_symbols.get(level, '●')} {message}",
            fg=colors.get(level, self.colors['fg'])
        )

    # Code Generator Methods

    def _create_code_generator_ui(self):
        """Create the code generator tool interface."""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg'], padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with back button
        self._create_header(main_frame, "Code/Serial Number Generator", show_back=True)

        # Content area - 3 column layout
        content_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, pady=15)

        # Left column - Connection & Table
        left_frame = tk.Frame(content_frame, bg=self.colors['bg'], width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        left_frame.pack_propagate(False)

        self._create_code_connection_panel(left_frame)
        self._create_code_table_selection_panel(left_frame)

        # Middle column - Data Grid & SQL Preview
        middle_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8)

        self._create_code_data_grid_panel(middle_frame)
        self._create_code_sql_preview_panel(middle_frame)

        # Right column - Configuration & Actions
        right_frame = tk.Frame(content_frame, bg=self.colors['bg'], width=360)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(8, 0))
        right_frame.pack_propagate(False)

        # Create scrollable frame for right column
        code_right_canvas = tk.Canvas(right_frame, bg=self.colors['bg'], highlightthickness=0)
        code_right_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=code_right_canvas.yview)
        code_right_scrollable = tk.Frame(code_right_canvas, bg=self.colors['bg'])

        def update_code_scrollregion(e=None):
            code_right_canvas.configure(scrollregion=code_right_canvas.bbox("all"))

        code_right_scrollable.bind("<Configure>", update_code_scrollregion)

        code_right_canvas.create_window((0, 0), window=code_right_scrollable, anchor="nw", width=340)
        code_right_canvas.configure(yscrollcommand=code_right_scrollbar.set)

        # Enable mousewheel scrolling
        def on_code_mousewheel(event):
            code_right_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        code_right_canvas.bind_all("<MouseWheel>", on_code_mousewheel)

        code_right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        code_right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._create_code_column_selection_panel(code_right_scrollable)
        self._create_code_config_panel(code_right_scrollable)
        self._create_code_action_panel(code_right_scrollable)

        # Footer - Status & Logs
        self._create_code_footer(main_frame)

    def _create_code_connection_panel(self, parent):
        """Create database connection panel for code generator."""
        content = self._create_panel(parent, "📊 Database Connection")

        # Connection inputs (same as others)
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
            command=self._test_code_connection,
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

    def _create_code_table_selection_panel(self, parent):
        """Create table selection panel for code generator."""
        content = self._create_panel(parent, "📋 Table Selection")

        # Table dropdown
        tk.Label(
            content,
            text="Table:",
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        self.code_table_combo = ttk.Combobox(
            content,
            textvariable=self.code_selected_table,
            state='readonly',
            font=('Segoe UI', 9)
        )
        self.code_table_combo.pack(fill=tk.X, pady=(0, 8))
        self.code_table_combo.bind('<<ComboboxSelected>>', self._on_code_table_selected)

        # Refresh button
        refresh_btn = tk.Button(
            content,
            text="🔄 Refresh Sample Data",
            command=self._refresh_code_table_data,
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
        self.code_row_count_label = tk.Label(
            content,
            text="Total Rows: -",
            font=('Segoe UI', 9),
            fg=self.colors['text_secondary'],
            bg=self.colors['secondary_bg'],
            anchor='w'
        )
        self.code_row_count_label.pack(anchor='w')

    def _create_code_data_grid_panel(self, parent):
        """Create data grid panel for code generator."""
        content = self._create_panel(parent, "📊 Sample Data (Top 10 Rows)", height=300)

        # Create Treeview with scrollbars
        tree_frame = tk.Frame(content, bg=self.colors['secondary_bg'])
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        self.code_data_tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            style="Custom.Treeview",
            selectmode='browse'
        )

        vsb.config(command=self.code_data_tree.yview)
        hsb.config(command=self.code_data_tree.xview)

        # Grid layout
        self.code_data_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

    def _create_code_sql_preview_panel(self, parent):
        """Create SQL preview panel for code generator."""
        content = self._create_panel(parent, "🔍 SQL Preview", height=150)

        self.code_sql_preview = scrolledtext.ScrolledText(
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
        self.code_sql_preview.pack(fill=tk.BOTH, expand=True)

        # Insert placeholder
        self.code_sql_preview.insert(1.0, "-- Click 'Generate SQL' to preview the UPDATE statement\n-- Configuration: Select columns and code format first")
        self.code_sql_preview.config(state='disabled')

    def _create_code_column_selection_panel(self, parent):
        """Create column selection panel for code generator."""
        panel_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT)
        panel_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        # Panel header
        header = tk.Frame(panel_frame, bg=self.colors['tertiary_bg'], height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="🎯 1. Column Selection",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['tertiary_bg']
        )
        title_label.pack(side=tk.LEFT, padx=12, pady=6)

        # Panel content
        content = tk.Frame(panel_frame, bg=self.colors['secondary_bg'], padx=12, pady=12)
        content.pack(fill=tk.X, expand=False)

        # Code columns
        tk.Label(
            content,
            text="Code/Serial Columns (select multiple):",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        # Warning label
        tk.Label(
            content,
            text="⚠️ Foreign Key columns will be blocked",
            font=('Segoe UI', 8, 'italic'),
            fg=self.colors['error'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        # Listbox for multiple selection
        listbox_frame = tk.Frame(content, bg=self.colors['secondary_bg'], height=120)
        listbox_frame.pack(fill=tk.X, pady=(0, 8))
        listbox_frame.pack_propagate(False)

        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.code_columns_listbox = tk.Listbox(
            listbox_frame,
            listvariable=self.code_columns_listvar,
            selectmode=tk.MULTIPLE,
            font=('Segoe UI', 9),
            bg=self.colors['tertiary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            yscrollcommand=scrollbar.set,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=self.colors['border'],
            selectbackground=self.colors['accent']
        )
        self.code_columns_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=self.code_columns_listbox.yview)

    def _create_code_config_panel(self, parent):
        """Create code configuration panel."""
        panel_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT)
        panel_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        # Panel header
        header = tk.Frame(panel_frame, bg=self.colors['tertiary_bg'], height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="⚙ 2. Code Format",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['tertiary_bg']
        )
        title_label.pack(side=tk.LEFT, padx=12, pady=6)

        # Panel content
        content = tk.Frame(panel_frame, bg=self.colors['secondary_bg'], padx=12, pady=12)
        content.pack(fill=tk.X, expand=False)

        # Code Type
        tk.Label(
            content,
            text="Code Type:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 6))

        type_frame = tk.Frame(content, bg=self.colors['secondary_bg'])
        type_frame.pack(fill=tk.X, pady=(0, 15))

        for code_type in [('Letters Only', 'letters'), ('Numbers Only', 'numbers'), ('Mixed', 'mixed')]:
            rb = tk.Radiobutton(
                type_frame,
                text=code_type[0],
                variable=self.code_type,
                value=code_type[1],
                font=('Segoe UI', 9),
                fg=self.colors['fg'],
                bg=self.colors['secondary_bg'],
                selectcolor=self.colors['tertiary_bg'],
                activebackground=self.colors['secondary_bg']
            )
            rb.pack(side=tk.LEFT, padx=(0, 15))

        # Code Length
        tk.Label(
            content,
            text="Code Length (minimum 5):",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        length_entry = tk.Entry(
            content,
            textvariable=self.code_length,
            font=('Segoe UI', 9),
            bg=self.colors['tertiary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            bd=1,
            width=10
        )
        length_entry.pack(anchor='w', pady=(0, 15))

        # Prefix
        tk.Label(
            content,
            text="Prefix (optional, max 3 chars):",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        prefix_entry = tk.Entry(
            content,
            textvariable=self.code_prefix,
            font=('Segoe UI', 9),
            bg=self.colors['tertiary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            bd=1,
            width=10
        )
        prefix_entry.pack(anchor='w', pady=(0, 8))

        # Prefix validation
        def validate_prefix(*args):
            prefix = self.code_prefix.get()
            if len(prefix) > 3:
                self.code_prefix.set(prefix[:3])
            self._update_code_example()

        self.code_prefix.trace('w', validate_prefix)

        # Example
        self.code_example_label = tk.Label(
            content,
            text="Example: ABC12345",
            font=('Segoe UI', 8, 'italic'),
            fg=self.colors['text_secondary'],
            bg=self.colors['secondary_bg'],
            anchor='w'
        )
        self.code_example_label.pack(anchor='w')

        # Row Filter
        tk.Label(
            content,
            text="Row Filter (Optional):",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(15, 6))

        # Filter Column
        tk.Label(
            content,
            text="Filter Column:",
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 3))

        self.code_filter_column_combo = ttk.Combobox(
            content,
            textvariable=self.code_filter_column_var,
            state='readonly',
            font=('Segoe UI', 9)
        )
        self.code_filter_column_combo.pack(fill=tk.X, pady=(0, 8))

        # Filter Value
        tk.Label(
            content,
            text="Filter Value:",
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 3))

        filter_value_entry = tk.Entry(
            content,
            textvariable=self.code_filter_value_var,
            font=('Segoe UI', 9),
            bg=self.colors['grid_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            borderwidth=1
        )
        filter_value_entry.pack(fill=tk.X, pady=(0, 8))

        # Help text
        tk.Label(
            content,
            text="Only update rows where Filter Column = Filter Value",
            font=('Segoe UI', 8),
            fg=self.colors['text_secondary'],
            bg=self.colors['secondary_bg'],
            wraplength=320,
            justify='left'
        ).pack(anchor='w')

    def _create_code_action_panel(self, parent):
        """Create action buttons panel for code generator."""
        panel_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT)
        panel_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        # Panel header
        header = tk.Frame(panel_frame, bg=self.colors['tertiary_bg'], height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="🚀 3. Execute",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['tertiary_bg']
        )
        title_label.pack(side=tk.LEFT, padx=12, pady=6)

        # Panel content
        content = tk.Frame(panel_frame, bg=self.colors['secondary_bg'], padx=12, pady=12)
        content.pack(fill=tk.X, expand=False)

        # Generate SQL button
        generate_btn = tk.Button(
            content,
            text="📝 Generate SQL Statement",
            command=self._generate_code_sql,
            bg=self.colors['info'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            borderwidth=0
        )
        generate_btn.pack(fill=tk.X, pady=(0, 10))

        # Preview button
        preview_btn = tk.Button(
            content,
            text="👁 Preview Changes (10 samples)",
            command=self._preview_code_changes,
            bg=self.colors['warning'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            borderwidth=0
        )
        preview_btn.pack(fill=tk.X, pady=(0, 10))

        # Execute button
        execute_btn = tk.Button(
            content,
            text="▶ Run Query (Update Codes)",
            command=self._execute_code_update,
            bg=self.colors['success'],
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=12,
            cursor='hand2',
            borderwidth=0
        )
        execute_btn.pack(fill=tk.X, pady=(0, 30))  # Add bottom padding for scrollability

    def _create_code_footer(self, parent):
        """Create footer with status and logs for code generator."""
        footer_frame = tk.Frame(parent, bg=self.colors['bg'])
        footer_frame.pack(fill=tk.BOTH, expand=False, pady=(10, 0))

        # Status label
        self.code_status_label = tk.Label(
            footer_frame,
            text="● Ready - Connect to database to begin",
            font=('Segoe UI', 9),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg'],
            anchor='w'
        )
        self.code_status_label.pack(fill=tk.X, pady=(0, 4))

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

        self.code_log_text = scrolledtext.ScrolledText(
            log_frame,
            height=5,
            font=('Courier New', 8),
            bg=self.colors['secondary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            wrap=tk.WORD,
            borderwidth=0
        )
        self.code_log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    # Code Generator Event Handlers

    def _test_code_connection(self):
        """Test database connection and load tables for code generator."""
        # Show critical warning before connecting
        confirm = messagebox.askokcancel(
            "⚠ CRITICAL WARNING - Development/Testing Only",
            "THIS TOOL IS FOR DEVELOPMENT AND TESTING DATABASES ONLY!\n\n"
            "By clicking OK, you confirm that:\n\n"
            "✓ This is a development or testing database\n"
            "✓ This is NOT a production database\n"
            "✓ You understand this tool will randomly modify data\n"
            "✓ You have backups if needed\n\n"
            "⚠ NEVER USE THIS ON PRODUCTION DATABASES ⚠\n\n"
            "Are you absolutely sure you want to connect?",
            icon='warning'
        )

        if not confirm:
            self._code_log("Connection cancelled by user", 'warning')
            return

        try:
            self._code_log("Connecting to database...", 'info')

            self.db_manager = DatabaseManager(
                host=self.host_var.get(),
                port=int(self.port_var.get()),
                user=self.user_var.get(),
                password=self.password_var.get(),
                database=self.database_var.get() if self.database_var.get() else None
            )

            success, message = self.db_manager.test_connection()

            if success:
                self._code_log(f"✓ {message}", 'success')

                # Initialize code generator
                self.code_generator = CodeGenerator(
                    host=self.host_var.get(),
                    port=int(self.port_var.get()),
                    user=self.user_var.get(),
                    password=self.password_var.get(),
                    database=self.database_var.get()
                )

                self._load_code_tables()
            else:
                self._code_log(f"✗ {message}", 'error')
                messagebox.showerror("Connection Error", message)

        except Exception as e:
            self._code_log(f"✗ Connection error: {e}", 'error')
            messagebox.showerror("Error", str(e))

    def _load_code_tables(self):
        """Load tables from database for code generator."""
        try:
            tables = self.db_manager.get_tables(self.database_var.get())

            if tables:
                self.code_table_combo['values'] = tables
                self._code_log(f"Loaded {len(tables)} tables", 'info')
            else:
                self._code_log("No tables found in database", 'warning')

        except Exception as e:
            self._code_log(f"Error loading tables: {e}", 'error')

    def _on_code_table_selected(self, event):
        """Handle table selection for code generator."""
        table = self.code_selected_table.get()

        if table and self.code_generator:
            self._code_log(f"Loading table: {table}", 'info')

            # Get schema
            schema = self.db_manager.get_table_schema(table, self.database_var.get())

            if schema:
                # Store available columns (text/varchar columns for codes)
                text_columns = []
                for col in schema:
                    col_type = col['Type'].lower()
                    if any(t in col_type for t in ['varchar', 'char', 'text']):
                        text_columns.append(col['Field'])

                self.code_available_columns = text_columns

                # Populate filter column dropdown
                self.code_filter_column_combo['values'] = [''] + text_columns

                # Check for foreign keys
                self._code_log("Checking columns for foreign key constraints...", 'info')
                fk_results = self.code_generator.check_columns_for_fk(
                    table, text_columns, self.database_var.get()
                )

                # Populate columns listbox
                self.code_columns_listbox.delete(0, tk.END)
                for col in text_columns:
                    fk_info = fk_results.get(col, {})
                    if fk_info.get('is_fk'):
                        # Mark FK columns
                        display_text = f"{col} [FK - BLOCKED]"
                        self.code_columns_listbox.insert(tk.END, display_text)
                        # Disable this item
                        self.code_columns_listbox.itemconfig(tk.END, fg='#999999')
                    else:
                        self.code_columns_listbox.insert(tk.END, col)

                self._code_log(f"Found {len(text_columns)} text columns", 'success')

                # Check if any FKs were found
                fk_count = sum(1 for fk in fk_results.values() if fk.get('is_fk'))
                if fk_count > 0:
                    self._code_log(f"⚠ {fk_count} foreign key column(s) blocked", 'warning')

            # Load row count
            count = self.db_manager.get_row_count(table, None, self.database_var.get())
            self.code_row_count_label.config(text=f"Total Rows: {count:,}")

            # Load data grid
            self._refresh_code_table_data()

    def _refresh_code_table_data(self):
        """Refresh the data grid with top 10 rows for code generator."""
        table = self.code_selected_table.get()

        if not table or not self.db_manager:
            return

        try:
            self._code_log("Refreshing sample data...", 'info')

            # Get top 10 rows
            data = self.db_manager.get_sample_data(table, limit=10, database=self.database_var.get())

            if data:
                # Clear existing data
                for item in self.code_data_tree.get_children():
                    self.code_data_tree.delete(item)

                # Configure columns
                columns = list(data[0].keys())
                self.code_data_tree['columns'] = columns
                self.code_data_tree['show'] = 'headings'

                # Configure column headings
                for col in columns:
                    self.code_data_tree.heading(col, text=col)
                    # Set column width based on content
                    max_width = max(len(col) * 8, 100)
                    self.code_data_tree.column(col, width=max_width, minwidth=80)

                # Insert data
                for row in data:
                    values = [str(row[col]) if row[col] is not None else '' for col in columns]
                    self.code_data_tree.insert('', tk.END, values=values)

                self._code_log(f"✓ Loaded {len(data)} rows", 'success')
            else:
                self._code_log("No data in table", 'warning')

        except Exception as e:
            self._code_log(f"Error loading data: {e}", 'error')

    def _get_selected_code_columns(self) -> List[str]:
        """Get selected code columns from listbox, excluding FK columns."""
        selected_indices = self.code_columns_listbox.curselection()
        selected_cols = []

        for i in selected_indices:
            col_text = self.code_columns_listbox.get(i)
            # Check if it's a FK column
            if '[FK - BLOCKED]' in col_text:
                continue  # Skip FK columns
            selected_cols.append(col_text)

        return selected_cols

    def _update_code_example(self):
        """Update the code example label."""
        try:
            prefix = self.code_prefix.get().upper()
            length = int(self.code_length.get()) if self.code_length.get() else 8
            code_type = self.code_type.get()

            # Generate example
            if code_type == 'letters':
                charset = 'ABCDEFGH'
            elif code_type == 'numbers':
                charset = '12345678'
            else:
                charset = 'ABC12345'

            remaining = length - len(prefix)
            if remaining < 1:
                remaining = 1

            example = prefix + charset[:remaining]
            self.code_example_label.config(text=f"Example: {example}")
        except:
            self.code_example_label.config(text="Example: ABC12345")

    def _generate_code_sql(self):
        """Generate SQL UPDATE statement for code generator."""
        if not self._validate_code_config():
            return

        try:
            table = self.code_selected_table.get()
            code_cols = self._get_selected_code_columns()
            code_type = self.code_type.get()
            code_length = self.code_length.get()
            prefix = self.code_prefix.get().upper()

            # Build sample SQL
            set_clauses = ", ".join([f"`{col}` = '[RandomCode]'" for col in code_cols])

            type_desc = {
                'letters': 'Letters Only (A-Z)',
                'numbers': 'Numbers Only (0-9)',
                'mixed': 'Mixed (A-Z, 0-9)'
            }

            sql = f"""-- Generated UPDATE statement
-- This will update codes in batches of 1000 rows with transaction safety

UPDATE `{table}`
SET {set_clauses}
LIMIT 1000;  -- Batch size (repeats until all rows updated)

-- Configuration:
-- Code Type: {type_desc[code_type]}
-- Code Length: {code_length} characters
-- Prefix: {prefix if prefix else 'None'}
-- Columns to update: {', '.join(code_cols)}
--
-- Example: {prefix}{code_type.upper()[:5]}{('12345' if code_type != 'letters' else 'ABCDE')[:int(code_length)-len(prefix)]}
--
-- Click 'Preview Changes' to see sample before/after
-- Click 'Run Query' to execute the update"""

            # Update preview
            self.code_sql_preview.config(state='normal')
            self.code_sql_preview.delete(1.0, tk.END)
            self.code_sql_preview.insert(1.0, sql)
            self.code_sql_preview.config(state='disabled')

            self._code_log("✓ SQL statement generated", 'success')

        except Exception as e:
            self._code_log(f"Error generating SQL: {e}", 'error')

    def _preview_code_changes(self):
        """Preview changes with actual sample data for code generator."""
        if not self._validate_code_config():
            return

        try:
            self._code_log("Generating preview...", 'info')

            config = self._build_code_config()
            preview = self.code_generator.preview_changes(config, limit=10)

            # Show preview in a new window
            self._show_code_preview_window(preview)

            self._code_log(f"✓ Preview generated ({len(preview)} samples)", 'success')

        except Exception as e:
            error_details = str(e)
            self._code_log(f"✗ Preview generation failed: {error_details}", 'error')

            # Log full traceback for debugging
            import traceback
            tb = traceback.format_exc()
            self._code_log(f"Traceback:\n{tb}", 'error')

            messagebox.showerror("Preview Error", f"{error_details}\n\nCheck Activity Log for full details.")

    def _show_code_preview_window(self, preview_data):
        """Show preview in a popup window for code generator."""
        preview_win = tk.Toplevel(self.root)
        preview_win.title("Preview Changes - Codes")
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

    def _execute_code_update(self):
        """Execute the code generation update."""
        if not self._validate_code_config():
            return

        # Confirmation dialog
        code_cols = self._get_selected_code_columns()
        table = self.code_selected_table.get()
        code_type = self.code_type.get()
        code_length = self.code_length.get()
        prefix = self.code_prefix.get().upper()

        type_desc = {
            'letters': 'Letters Only',
            'numbers': 'Numbers Only',
            'mixed': 'Mixed (Letters + Numbers)'
        }

        msg = f"""Are you sure you want to run this query?

Table: {table}
Columns: {', '.join(code_cols)}
Code Type: {type_desc[code_type]}
Code Length: {code_length}
Prefix: {prefix if prefix else 'None'}

This will modify your database.
Transactions will be used (can rollback on error)."""

        if not messagebox.askyesno("Confirm Query Execution", msg):
            return

        try:
            self._code_log("Running query...", 'info')
            self.code_status_label.config(text="● Running query... Please wait", fg=self.colors['warning'])
            self.root.update()

            config = self._build_code_config()
            result = self.code_generator.execute_update(config, dry_run=False)

            # Log all errors to activity log
            if result['errors']:
                self._code_log(f"⚠ {len(result['errors'])} error(s) occurred during execution:", 'warning')
                for i, error in enumerate(result['errors'][:10], 1):  # Show first 10 errors
                    self._code_log(f"  Error {i}: {error}", 'error')
                if len(result['errors']) > 10:
                    self._code_log(f"  ... and {len(result['errors']) - 10} more errors", 'error')

            # Show results
            success_msg = f"""Query Completed!

Total Rows: {result['total_rows']}
Updated: {result['updated_rows']}
Skipped: {result['skipped_rows']}
Errors: {len(result['errors'])}"""

            if result['errors']:
                success_msg += f"\n\nCheck Activity Log for error details."
                success_msg += f"\nFirst error: {result['errors'][0]}"

            self._code_log(f"✓ Query complete: {result['updated_rows']} rows updated, {result['skipped_rows']} skipped", 'success' if len(result['errors']) == 0 else 'warning')

            if len(result['errors']) > 0:
                messagebox.showwarning("Query Completed with Errors", success_msg)
            else:
                messagebox.showinfo("Query Complete", success_msg)

            # Auto-refresh sample data
            self._code_log("Auto-refreshing sample data...", 'info')
            self._refresh_code_table_data()

        except Exception as e:
            error_details = str(e)
            self._code_log(f"✗ Query failed: {error_details}", 'error')

            # Log full traceback for debugging
            import traceback
            tb = traceback.format_exc()
            self._code_log(f"Traceback:\n{tb}", 'error')

            messagebox.showerror("Query Error", f"Query failed:\n\n{error_details}\n\nCheck Activity Log for full details.")
        finally:
            self.code_status_label.config(text="● Ready", fg=self.colors['text_secondary'])

    def _validate_code_config(self) -> bool:
        """Validate current configuration for code generator."""
        if not self.db_manager:
            messagebox.showerror("Error", "Please connect to database first")
            return False

        if not self.code_selected_table.get():
            messagebox.showerror("Error", "Please select a table")
            return False

        selected_cols = self._get_selected_code_columns()
        if not selected_cols:
            messagebox.showerror("Error", "Please select at least one column (Foreign Key columns are blocked)")
            return False

        # Check if any selected columns are FKs
        for i in self.code_columns_listbox.curselection():
            col_text = self.code_columns_listbox.get(i)
            if '[FK - BLOCKED]' in col_text:
                messagebox.showerror(
                    "Foreign Key Column Blocked",
                    "You cannot generate codes for Foreign Key columns!\n\n"
                    "This would break referential integrity in your database.\n\n"
                    "FK columns are marked with '[FK - BLOCKED]'"
                )
                return False

        try:
            length = int(self.code_length.get())
            if length < 5:
                messagebox.showerror("Error", "Code length must be at least 5 characters")
                return False
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for code length")
            return False

        prefix = self.code_prefix.get()
        if len(prefix) > 3:
            messagebox.showerror("Error", "Prefix cannot be longer than 3 characters")
            return False

        return True

    def _build_code_config(self) -> Dict[str, Any]:
        """Build configuration dictionary for code generator."""
        # Build where clause from filter if provided
        where_clause = None
        filter_col = self.code_filter_column_var.get()
        filter_val = self.code_filter_value_var.get()
        if filter_col and filter_val:
            # Escape the value to prevent SQL injection
            escaped_val = filter_val.replace("'", "''")
            where_clause = f"`{filter_col}` = '{escaped_val}'"

        return {
            'table': self.code_selected_table.get(),
            'code_columns': self._get_selected_code_columns(),
            'code_type': self.code_type.get(),
            'code_length': int(self.code_length.get()),
            'prefix': self.code_prefix.get().upper(),
            'batch_size': 1000,
            'preserve_null': False,  # Update NULL values too
            'primary_key': 'id',
            'ensure_unique': True,
            'where_clause': where_clause
        }

    def _code_log(self, message: str, level: str = 'info'):
        """Log message to code generator console."""
        colors = {
            'info': self.colors['fg'],
            'success': self.colors['success'],
            'warning': self.colors['warning'],
            'error': self.colors['error']
        }

        timestamp = __import__('datetime').datetime.now().strftime('%H:%M:%S')
        self.code_log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.code_log_text.see(tk.END)

        status_symbols = {
            'info': '●',
            'success': '✓',
            'warning': '⚠',
            'error': '✗'
        }

        self.code_status_label.config(
            text=f"{status_symbols.get(level, '●')} {message}",
            fg=colors.get(level, self.colors['fg'])
        )

    # ========================================================================
    # LOCATION RANDOMIZER METHODS
    # ========================================================================

    def _create_location_randomizer_ui(self):
        """Create the location randomizer tool interface."""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg'], padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with back button
        self._create_header(main_frame, "Location Randomizer", show_back=True)

        # Content area - 3 column layout
        content_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, pady=15)

        # Left column - Connection & Table
        left_frame = tk.Frame(content_frame, bg=self.colors['bg'], width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        left_frame.pack_propagate(False)

        self._create_location_connection_panel(left_frame)
        self._create_location_table_selection_panel(left_frame)

        # Middle column - Data Grid & SQL Preview
        middle_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8)

        self._create_location_data_grid_panel(middle_frame)
        self._create_location_sql_preview_panel(middle_frame)

        # Right column - Configuration & Actions
        right_frame = tk.Frame(content_frame, bg=self.colors['bg'], width=360)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(8, 0))
        right_frame.pack_propagate(False)

        # Create scrollable frame for right column
        location_right_canvas = tk.Canvas(right_frame, bg=self.colors['bg'], highlightthickness=0)
        location_right_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=location_right_canvas.yview)
        location_right_scrollable = tk.Frame(location_right_canvas, bg=self.colors['bg'])

        def update_location_scrollregion(e=None):
            location_right_canvas.configure(scrollregion=location_right_canvas.bbox("all"))

        location_right_scrollable.bind("<Configure>", update_location_scrollregion)

        location_right_canvas.create_window((0, 0), window=location_right_scrollable, anchor="nw", width=340)
        location_right_canvas.configure(yscrollcommand=location_right_scrollbar.set)

        # Enable mousewheel scrolling
        def on_location_mousewheel(event):
            location_right_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        location_right_canvas.bind_all("<MouseWheel>", on_location_mousewheel)

        location_right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        location_right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._create_location_column_selection_panel(location_right_scrollable)
        self._create_location_config_panel(location_right_scrollable)
        self._create_location_action_panel(location_right_scrollable)

        # Footer - Status & Logs
        self._create_location_footer(main_frame)

    def _create_location_connection_panel(self, parent):
        """Create database connection panel for location randomizer."""
        content = self._create_panel(parent, "📊 Database Connection")

        # Connection inputs (same as others)
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
            command=self._test_location_connection,
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

    def _create_location_table_selection_panel(self, parent):
        """Create table selection panel for location randomizer."""
        content = self._create_panel(parent, "📋 Table Selection")

        # Table dropdown
        tk.Label(
            content,
            text="Table:",
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        self.location_table_combo = ttk.Combobox(
            content,
            textvariable=self.location_selected_table,
            state='readonly',
            font=('Segoe UI', 9)
        )
        self.location_table_combo.pack(fill=tk.X, pady=(0, 8))
        self.location_table_combo.bind('<<ComboboxSelected>>', self._on_location_table_selected)

        # Refresh button
        refresh_btn = tk.Button(
            content,
            text="🔄 Refresh Sample Data",
            command=self._refresh_location_table_data,
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
        self.location_row_count_label = tk.Label(
            content,
            text="Total Rows: -",
            font=('Segoe UI', 9),
            fg=self.colors['text_secondary'],
            bg=self.colors['secondary_bg'],
            anchor='w'
        )
        self.location_row_count_label.pack(anchor='w')

    def _create_location_data_grid_panel(self, parent):
        """Create data grid panel for location randomizer."""
        content = self._create_panel(parent, "📊 Sample Data (Top 10 Rows)", height=300)

        # Create Treeview with scrollbars
        tree_frame = tk.Frame(content, bg=self.colors['secondary_bg'])
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        self.location_data_tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            style="Custom.Treeview",
            selectmode='browse'
        )

        vsb.config(command=self.location_data_tree.yview)
        hsb.config(command=self.location_data_tree.xview)

        # Grid layout
        self.location_data_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

    def _create_location_sql_preview_panel(self, parent):
        """Create SQL preview panel for location randomizer."""
        content = self._create_panel(parent, "🔍 SQL Preview", height=150)

        self.location_sql_preview = scrolledtext.ScrolledText(
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
        self.location_sql_preview.pack(fill=tk.BOTH, expand=True)

        # Insert placeholder
        self.location_sql_preview.insert(1.0, "-- Click 'Generate SQL' to preview the UPDATE statement\n-- Configuration: Select latitude and longitude columns first")
        self.location_sql_preview.config(state='disabled')

    def _create_location_column_selection_panel(self, parent):
        """Create column selection panel for location randomizer."""
        panel_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT)
        panel_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        # Panel header
        header = tk.Frame(panel_frame, bg=self.colors['tertiary_bg'], height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="🎯 1. Column Selection",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['tertiary_bg']
        )
        title_label.pack(side=tk.LEFT, padx=12, pady=6)

        # Panel content
        content = tk.Frame(panel_frame, bg=self.colors['secondary_bg'], padx=12, pady=12)
        content.pack(fill=tk.X, expand=False)

        # Latitude column
        tk.Label(
            content,
            text="Latitude Column:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        tk.Label(
            content,
            text="Numeric columns (DECIMAL, FLOAT, DOUBLE)",
            font=('Segoe UI', 8, 'italic'),
            fg=self.colors['text_secondary'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        self.location_lat_combo = ttk.Combobox(
            content,
            textvariable=self.location_lat_column_var,
            state='readonly',
            font=('Segoe UI', 9)
        )
        self.location_lat_combo.pack(fill=tk.X, pady=(0, 12))

        # Longitude column
        tk.Label(
            content,
            text="Longitude Column:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        tk.Label(
            content,
            text="Numeric columns (DECIMAL, FLOAT, DOUBLE)",
            font=('Segoe UI', 8, 'italic'),
            fg=self.colors['text_secondary'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        self.location_lng_combo = ttk.Combobox(
            content,
            textvariable=self.location_lng_column_var,
            state='readonly',
            font=('Segoe UI', 9)
        )
        self.location_lng_combo.pack(fill=tk.X, pady=(0, 12))

    def _create_location_config_panel(self, parent):
        """Create location configuration panel."""
        panel_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT)
        panel_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        # Panel header
        header = tk.Frame(panel_frame, bg=self.colors['tertiary_bg'], height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="⚙ 2. Location Configuration",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['tertiary_bg']
        )
        title_label.pack(side=tk.LEFT, padx=12, pady=6)

        # Panel content
        content = tk.Frame(panel_frame, bg=self.colors['secondary_bg'], padx=12, pady=12)
        content.pack(fill=tk.X, expand=False)

        # Location Description
        tk.Label(
            content,
            text="Location Description:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        tk.Label(
            content,
            text="Describe the type of locations (e.g., 'hospitals in Kampala')",
            font=('Segoe UI', 8, 'italic'),
            fg=self.colors['text_secondary'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        desc_frame = tk.Frame(content, bg=self.colors['secondary_bg'], height=70)
        desc_frame.pack(fill=tk.X, pady=(0, 12))
        desc_frame.pack_propagate(False)

        self.location_description_text = scrolledtext.ScrolledText(
            desc_frame,
            height=3,
            font=('Segoe UI', 9),
            bg=self.colors['tertiary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            wrap=tk.WORD,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=self.colors['border']
        )
        self.location_description_text.pack(fill=tk.BOTH, expand=True)

        # DeepSeek API Key
        tk.Label(
            content,
            text="DeepSeek API Key:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 4))

        api_key_frame = tk.Frame(content, bg=self.colors['secondary_bg'])
        api_key_frame.pack(fill=tk.X, pady=(0, 4))

        self.location_api_key_entry = tk.Entry(
            api_key_frame,
            textvariable=self.location_api_key_var,
            font=('Segoe UI', 9),
            bg=self.colors['tertiary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            bd=1,
            show='*'
        )
        self.location_api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        # Show/Hide button
        self.location_api_key_visible = False
        self.location_show_hide_btn = tk.Button(
            api_key_frame,
            text="👁",
            command=self._toggle_location_api_key_visibility,
            bg=self.colors['tertiary_bg'],
            fg=self.colors['fg'],
            font=('Segoe UI', 9),
            relief=tk.FLAT,
            padx=8,
            pady=4,
            cursor='hand2'
        )
        self.location_show_hide_btn.pack(side=tk.RIGHT)

        tk.Label(
            content,
            text="Get your API key at: deepseek.com",
            font=('Segoe UI', 7, 'italic'),
            fg=self.colors['text_secondary'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 12))

        # Row Filter
        tk.Label(
            content,
            text="Row Filter (Optional):",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 6))

        # Filter Column
        tk.Label(
            content,
            text="Filter Column:",
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 3))

        self.location_filter_column_combo = ttk.Combobox(
            content,
            textvariable=self.location_filter_column_var,
            state='readonly',
            font=('Segoe UI', 9)
        )
        self.location_filter_column_combo.pack(fill=tk.X, pady=(0, 8))

        # Filter Value
        tk.Label(
            content,
            text="Filter Value:",
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w', pady=(0, 3))

        filter_value_entry = tk.Entry(
            content,
            textvariable=self.location_filter_value_var,
            font=('Segoe UI', 9),
            bg=self.colors['tertiary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            bd=1
        )
        filter_value_entry.pack(fill=tk.X, pady=(0, 4))

        tk.Label(
            content,
            text="Example: Only update rows where status='active'",
            font=('Segoe UI', 7, 'italic'),
            fg=self.colors['text_secondary'],
            bg=self.colors['secondary_bg']
        ).pack(anchor='w')

    def _create_location_action_panel(self, parent):
        """Create action panel for location randomizer."""
        panel_frame = tk.Frame(parent, bg=self.colors['secondary_bg'], relief=tk.FLAT)
        panel_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        # Panel header
        header = tk.Frame(panel_frame, bg=self.colors['tertiary_bg'], height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="🚀 3. Actions",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['tertiary_bg']
        )
        title_label.pack(side=tk.LEFT, padx=12, pady=6)

        # Panel content
        content = tk.Frame(panel_frame, bg=self.colors['secondary_bg'], padx=12, pady=12)
        content.pack(fill=tk.X, expand=False)

        # Preview button
        preview_btn = tk.Button(
            content,
            text="Generate SQL Preview",
            command=self._preview_location_changes,
            bg=self.colors['info'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            borderwidth=0
        )
        preview_btn.pack(fill=tk.X, pady=(0, 10))

        # Execute button
        execute_btn = tk.Button(
            content,
            text="⚠️ Execute Update",
            command=self._execute_location_update,
            bg=self.colors['warning'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            borderwidth=0
        )
        execute_btn.pack(fill=tk.X)

        # Warning
        warning_label = tk.Label(
            content,
            text="⚠️ This will permanently modify your database",
            font=('Segoe UI', 8, 'italic'),
            fg=self.colors['error'],
            bg=self.colors['secondary_bg'],
            wraplength=300
        )
        warning_label.pack(pady=(8, 0))

    def _create_location_footer(self, parent):
        """Create footer with status and logs for location randomizer."""
        footer_frame = tk.Frame(parent, bg=self.colors['bg'])
        footer_frame.pack(fill=tk.BOTH, expand=False, pady=(15, 0))

        # Status bar
        status_frame = tk.Frame(footer_frame, bg=self.colors['tertiary_bg'], height=30)
        status_frame.pack(fill=tk.X, pady=(0, 8))
        status_frame.pack_propagate(False)

        self.location_status_label = tk.Label(
            status_frame,
            text="● Ready",
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['tertiary_bg'],
            anchor='w'
        )
        self.location_status_label.pack(side=tk.LEFT, padx=12, fill=tk.X, expand=True)

        # Log panel
        log_panel_frame = tk.Frame(footer_frame, bg=self.colors['secondary_bg'], relief=tk.FLAT)
        log_panel_frame.pack(fill=tk.BOTH, expand=True)

        log_header = tk.Frame(log_panel_frame, bg=self.colors['tertiary_bg'], height=30)
        log_header.pack(fill=tk.X)
        log_header.pack_propagate(False)

        log_title = tk.Label(
            log_header,
            text="📋 Execution Log",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['tertiary_bg']
        )
        log_title.pack(side=tk.LEFT, padx=12, pady=6)

        # Clear log button
        clear_log_btn = tk.Button(
            log_header,
            text="Clear",
            command=lambda: self.location_log_text.delete(1.0, tk.END),
            bg=self.colors['tertiary_bg'],
            fg=self.colors['fg'],
            font=('Segoe UI', 8),
            relief=tk.FLAT,
            padx=10,
            cursor='hand2',
            borderwidth=0
        )
        clear_log_btn.pack(side=tk.RIGHT, padx=12)

        # Log text area
        log_content = tk.Frame(log_panel_frame, bg=self.colors['secondary_bg'], padx=8, pady=8)
        log_content.pack(fill=tk.BOTH, expand=True)

        self.location_log_text = scrolledtext.ScrolledText(
            log_content,
            height=6,
            font=('Courier New', 8),
            bg=self.colors['tertiary_bg'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            wrap=tk.WORD,
            borderwidth=0
        )
        self.location_log_text.pack(fill=tk.BOTH, expand=True)

    def _toggle_location_api_key_visibility(self):
        """Toggle API key visibility."""
        if self.location_api_key_visible:
            self.location_api_key_entry.config(show='*')
            self.location_api_key_visible = False
        else:
            self.location_api_key_entry.config(show='')
            self.location_api_key_visible = True

    def _test_location_connection(self):
        """Test database connection and load tables for location randomizer."""
        def connect_thread():
            try:
                self._location_log("Connecting to database...", 'info')

                # Create database manager
                self.db_manager = DatabaseManager(
                    host=self.host_var.get(),
                    port=int(self.port_var.get()),
                    user=self.user_var.get(),
                    password=self.password_var.get(),
                    database=self.database_var.get()
                )

                # Test connection
                success, message = self.db_manager.test_connection()

                if not success:
                    raise Exception(message)

                # Initialize location randomizer
                self.location_randomizer = LocationRandomizer(
                    host=self.host_var.get(),
                    port=int(self.port_var.get()),
                    user=self.user_var.get(),
                    password=self.password_var.get(),
                    database=self.database_var.get()
                )

                # Get tables
                tables = self.db_manager.get_tables()

                # Update UI in main thread
                self.root.after(0, lambda: self._on_location_connection_success(tables))

            except Exception as e:
                self.root.after(0, lambda: self._location_log(f"Connection failed: {str(e)}", 'error'))
                self.root.after(0, lambda: messagebox.showerror("Connection Error", str(e)))

        threading.Thread(target=connect_thread, daemon=True).start()

    def _on_location_connection_success(self, tables: List[str]):
        """Handle successful connection for location randomizer."""
        self._location_log(f"Connected successfully! Found {len(tables)} tables.", 'success')

        # Update table dropdown
        self.location_table_combo['values'] = tables
        if tables:
            self.location_selected_table.set(tables[0])
            self._on_location_table_selected(None)

    def _on_location_table_selected(self, event):
        """Handle table selection for location randomizer."""
        table_name = self.location_selected_table.get()
        if not table_name:
            return

        def load_table_thread():
            try:
                self._location_log(f"Loading table: {table_name}...", 'info')

                # Get column info (using get_table_schema)
                schema = self.db_manager.get_table_schema(table_name, self.database_var.get())

                # Filter numeric columns for lat/lng
                numeric_types = ['decimal', 'float', 'double', 'numeric', 'real']
                numeric_columns = [col['Field'] for col in schema
                                 if any(t in col['Type'].lower() for t in numeric_types)]

                # Get all columns for filter dropdown
                all_column_names = [col['Field'] for col in schema]

                # Get row count
                row_count = self.db_manager.get_row_count(table_name)

                # Get sample data
                sample_data = self.db_manager.get_sample_data(table_name, limit=10)

                # Update UI in main thread
                self.root.after(0, lambda: self._update_location_ui_after_table_load(
                    numeric_columns, all_column_names, row_count, sample_data, schema
                ))

            except Exception as e:
                self.root.after(0, lambda: self._location_log(f"Error loading table: {str(e)}", 'error'))

        threading.Thread(target=load_table_thread, daemon=True).start()

    def _update_location_ui_after_table_load(self, numeric_columns, all_columns, row_count, sample_data, columns):
        """Update UI after table is loaded for location randomizer."""
        # Store available columns
        self.location_available_columns = numeric_columns

        # Update lat/lng dropdowns
        self.location_lat_combo['values'] = numeric_columns
        self.location_lng_combo['values'] = numeric_columns

        # Set default selections
        if len(numeric_columns) >= 2:
            self.location_lat_column_var.set(numeric_columns[0])
            self.location_lng_column_var.set(numeric_columns[1])
        elif len(numeric_columns) == 1:
            self.location_lat_column_var.set(numeric_columns[0])

        # Update filter dropdown
        self.location_filter_column_combo['values'] = [''] + all_columns

        # Update row count
        self.location_row_count_label.config(text=f"Total Rows: {row_count:,}")

        # Update data grid
        self._populate_location_data_grid(sample_data, columns)

        self._location_log(f"Loaded table with {row_count:,} rows. Found {len(numeric_columns)} numeric columns.", 'success')

    def _populate_location_data_grid(self, data, columns):
        """Populate the data grid with sample data for location randomizer."""
        # Clear existing data
        self.location_data_tree.delete(*self.location_data_tree.get_children())

        # Configure columns
        column_names = [col['Field'] for col in columns]
        self.location_data_tree['columns'] = column_names
        self.location_data_tree['show'] = 'headings'

        # Set column headings and widths
        for col_name in column_names:
            self.location_data_tree.heading(col_name, text=col_name)
            self.location_data_tree.column(col_name, width=100, minwidth=80)

        # Insert data
        for row in data:
            values = [row.get(col_name) for col_name in column_names]
            self.location_data_tree.insert('', tk.END, values=values)

    def _refresh_location_table_data(self):
        """Refresh the sample data for location randomizer."""
        self._on_location_table_selected(None)

    def _validate_location_config(self) -> bool:
        """Validate location configuration."""
        if not self.db_manager:
            messagebox.showerror("Error", "Please connect to database first")
            return False

        if not self.location_selected_table.get():
            messagebox.showerror("Error", "Please select a table")
            return False

        lat_col = self.location_lat_column_var.get()
        lng_col = self.location_lng_column_var.get()

        if not lat_col or not lng_col:
            messagebox.showerror("Error", "Please select both latitude and longitude columns")
            return False

        if lat_col == lng_col:
            messagebox.showerror("Error", "Latitude and longitude must be different columns")
            return False

        description = self.location_description_text.get("1.0", tk.END).strip()
        if not description:
            messagebox.showerror("Error", "Please enter a location description")
            return False

        api_key = self.location_api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter your DeepSeek API key")
            return False

        return True

    def _build_location_config(self) -> Dict[str, Any]:
        """Build configuration dictionary for location randomizer."""
        # Build where clause from filter if provided
        where_clause = None
        filter_col = self.location_filter_column_var.get()
        filter_val = self.location_filter_value_var.get()
        if filter_col and filter_val:
            # Escape the value to prevent SQL injection
            escaped_val = filter_val.replace("'", "''")
            where_clause = f"`{filter_col}` = '{escaped_val}'"

        description = self.location_description_text.get("1.0", tk.END).strip()

        return {
            'table': self.location_selected_table.get(),
            'lat_column': self.location_lat_column_var.get(),
            'lng_column': self.location_lng_column_var.get(),
            'location_description': description,
            'api_key': self.location_api_key_var.get().strip(),
            'batch_size': 1000,
            'primary_key': 'id',
            'where_clause': where_clause
        }

    def _preview_location_changes(self):
        """Preview the location changes."""
        if not self._validate_location_config():
            return

        try:
            self._location_log("Generating preview...", 'info')
            config = self._build_location_config()
            self._location_log(f"Asking AI to interpret: '{config['location_description']}'", 'info')

            preview = self.location_randomizer.preview_changes(config, limit=10)

            # The preview_changes returns the data with bounds included
            # We need to call interpret_location_description to get the bounds for logging
            bounds = self.location_randomizer.interpret_location_description(
                config['location_description'],
                config['api_key']
            )

            self._location_log(f"✓ AI Interpretation: {bounds.get('description', 'N/A')}", 'success')
            self._location_log(f"  Latitude range: {bounds['min_lat']} to {bounds['max_lat']}", 'info')
            self._location_log(f"  Longitude range: {bounds['min_lng']} to {bounds['max_lng']}", 'info')

            # Show preview in a new window
            self._show_location_preview_window(preview)

            self._location_log(f"✓ Preview generated ({len(preview)} samples)", 'success')

        except Exception as e:
            error_details = str(e)
            self._location_log(f"✗ Preview generation failed: {error_details}", 'error')

            # Log full traceback for debugging
            import traceback
            tb = traceback.format_exc()
            self._location_log(f"Traceback:\n{tb}", 'error')

            messagebox.showerror("Preview Error", f"{error_details}\n\nCheck Activity Log for full details.")

    def _show_location_preview_window(self, preview_data):
        """Show preview in a popup window for location randomizer."""
        preview_win = tk.Toplevel(self.root)
        preview_win.title("Preview Changes - Locations")
        preview_win.geometry("900x600")

        # Header
        header = tk.Label(
            preview_win,
            text=f"Preview: {len(preview_data)} sample rows",
            font=('Segoe UI', 12, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            pady=10
        )
        header.pack(fill=tk.X)

        # Create treeview for preview
        tree_frame = tk.Frame(preview_win, bg=self.colors['bg'])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Scrollbars
        y_scroll = ttk.Scrollbar(tree_frame)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        x_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        # Treeview
        tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
            style="Custom.Treeview"
        )
        tree.pack(fill=tk.BOTH, expand=True)

        y_scroll.config(command=tree.yview)
        x_scroll.config(command=tree.xview)

        # Configure columns
        if preview_data:
            columns = list(preview_data[0]['updated'].keys())
            tree['columns'] = columns
            tree['show'] = 'headings'

            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=120)

            # Insert data
            for item in preview_data:
                values = [item['updated'].get(col) for col in columns]
                tree.insert('', tk.END, values=values)

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

    def _update_location_sql_preview(self, sql: str):
        """Update the SQL preview text for location randomizer."""
        self.location_sql_preview.config(state='normal')
        self.location_sql_preview.delete(1.0, tk.END)
        self.location_sql_preview.insert(1.0, sql)
        self.location_sql_preview.config(state='disabled')

    def _execute_location_update(self):
        """Execute the location update."""
        self._location_log("Execute button clicked", 'info')

        if not self._validate_location_config():
            self._location_log("Validation failed", 'error')
            return

        # Confirmation dialog
        config = self._build_location_config()
        table = config['table']

        where_info = ""
        if config['where_clause']:
            where_info = f"\n\nFilter: {config['where_clause']}"

        message = (
            f"⚠️ WARNING: This will update location data in table '{table}'!\n\n"
            f"Columns: {config['lat_column']}, {config['lng_column']}\n"
            f"Description: {config['location_description']}"
            f"{where_info}\n\n"
            "This operation CANNOT be undone!\n\n"
            "Do you want to continue?"
        )

        if not messagebox.askyesno("Confirm Update", message, icon='warning'):
            self._location_log("Update cancelled by user", 'warning')
            return

        def execute_thread():
            try:
                self._location_log("Starting location update...", 'info')
                self._location_log(f"Table: {config['table']}", 'info')
                self._location_log(f"Columns: {config['lat_column']}, {config['lng_column']}", 'info')
                self._location_log(f"Asking AI to interpret: '{config['location_description']}'", 'info')

                # Execute update (location_randomizer should already be initialized)
                result = self.location_randomizer.execute_update(config, dry_run=False)

                # Log AI interpretation
                if 'bounds' in result:
                    bounds = result['bounds']
                    self.root.after(0, lambda: self._location_log(
                        f"✓ AI Interpretation: {bounds.get('description', 'N/A')}", 'success'
                    ))
                    self.root.after(0, lambda: self._location_log(
                        f"  Latitude range: {bounds['min_lat']} to {bounds['max_lat']}", 'info'
                    ))
                    self.root.after(0, lambda: self._location_log(
                        f"  Longitude range: {bounds['min_lng']} to {bounds['max_lng']}", 'info'
                    ))

                # Update UI in main thread
                self.root.after(0, lambda: self._on_location_update_complete(result))

            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: self._location_log(f"Update failed: {error_msg}", 'error'))
                self.root.after(0, lambda: messagebox.showerror("Update Error", error_msg))

        threading.Thread(target=execute_thread, daemon=True).start()

    def _on_location_update_complete(self, result: Dict[str, Any]):
        """Handle completion of location update."""
        rows_updated = result.get('rows_updated', 0)

        self._location_log(f"✓ Update completed successfully!", 'success')
        self._location_log(f"Rows updated: {rows_updated:,}", 'success')

        # Refresh table data
        self._refresh_location_table_data()

        messagebox.showinfo(
            "Update Complete",
            f"Successfully updated {rows_updated:,} rows!\n\n"
            "The location coordinates have been randomized."
        )

    def _location_log(self, message: str, level: str = 'info'):
        """Log message to location randomizer console."""
        colors = {
            'info': self.colors['fg'],
            'success': self.colors['success'],
            'warning': self.colors['warning'],
            'error': self.colors['error']
        }

        timestamp = __import__('datetime').datetime.now().strftime('%H:%M:%S')
        self.location_log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.location_log_text.see(tk.END)

        status_symbols = {
            'info': '●',
            'success': '✓',
            'warning': '⚠',
            'error': '✗'
        }

        self.location_status_label.config(
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
