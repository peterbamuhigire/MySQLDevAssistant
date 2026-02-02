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
from ..core.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class DDAApplication:
    """Main GUI Application with multi-tool interface."""

    def __init__(self, root):
        self.root = root
        self.root.title("⚠️ DDA Toolkit - DEVELOPMENT/TESTING ONLY - DO NOT USE ON PRODUCTION")
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

        # Company Generator variables
        self.company_selected_table = tk.StringVar()
        self.company_columns_listvar = tk.StringVar()
        self.name1_groups_var = {}
        self.name2_groups_var = {}
        self.classification_groups_var = {}

        # Phone Number Generator variables
        self.phone_selected_table = tk.StringVar()
        self.phone_columns_listvar = tk.StringVar()
        self.phone_country_code = tk.StringVar(value='+256')
        self.phone_prefix = tk.StringVar(value='7')
        self.phone_min_number = tk.StringVar(value='10000000')
        self.phone_max_number = tk.StringVar(value='99999999')

        # Available columns
        self.available_columns = []
        self.company_available_columns = []
        self.phone_available_columns = []

        # Data storage
        self.current_table_data = []
        self.generated_sql = ""

        # Configure TTK style
        self._configure_ttk_style()

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

        # CRITICAL WARNING - Development/Testing Only
        warning_frame = tk.Frame(main_frame, bg=self.colors['error'], relief=tk.RAISED, bd=3)
        warning_frame.pack(fill=tk.X, pady=(0, 30))

        warning_header = tk.Frame(warning_frame, bg=self.colors['error'])
        warning_header.pack(fill=tk.X, padx=20, pady=(15, 10))

        warning_icon = tk.Label(
            warning_header,
            text="⚠",
            font=('Segoe UI', 40, 'bold'),
            fg='white',
            bg=self.colors['error']
        )
        warning_icon.pack(side=tk.LEFT, padx=(0, 15))

        warning_title = tk.Label(
            warning_header,
            text="DEVELOPMENT & TESTING ONLY",
            font=('Segoe UI', 20, 'bold'),
            fg='white',
            bg=self.colors['error']
        )
        warning_title.pack(side=tk.LEFT)

        warning_text = tk.Label(
            warning_frame,
            text="This tool is designed EXCLUSIVELY for development and testing databases.\n\n"
                 "🚫 NEVER use this on production databases\n"
                 "🚫 NEVER connect to live customer data\n"
                 "🚫 NEVER use in production environments\n\n"
                 "This tool randomly modifies data and is intended ONLY for generating test data.\n"
                 "Using this on production data WILL corrupt your database and destroy real information.",
            font=('Segoe UI', 11),
            fg='white',
            bg=self.colors['error'],
            justify=tk.LEFT,
            wraplength=800
        )
        warning_text.pack(padx=20, pady=(0, 15))

        # Tool selection frame
        tools_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        tools_frame.pack(expand=True)

        # Create tool buttons
        tools = [
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

        for i, tool in enumerate(tools):
            self._create_tool_button(tools_frame, tool, i)

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
            'full_name_mode': self.full_name_mode.get()
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

        return {
            'table': self.company_selected_table.get(),
            'company_columns': self._get_selected_company_columns(),
            'name1_groups': name1_groups,
            'name2_groups': name2_groups,
            'classification_groups': classification_groups,
            'batch_size': 1000,
            'preserve_null': False,  # Update NULL values too
            'primary_key': 'id'
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
        return {
            'table': self.phone_selected_table.get(),
            'phone_columns': self._get_selected_phone_columns(),
            'country_code': self.phone_country_code.get(),
            'prefix': self.phone_prefix.get(),
            'min_number': int(self.phone_min_number.get()),
            'max_number': int(self.phone_max_number.get()),
            'batch_size': 1000,
            'preserve_null': False,  # Update NULL values too
            'primary_key': 'id'
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
