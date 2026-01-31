"""
CLI Interface for DDA Toolkit
"""

import argparse
import sys
import logging
from typing import List, Dict, Any
from pathlib import Path

from ..tools.name_generator import NameRandomizer
from ..core.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class CLIInterface:
    """Command-line interface for DDA tools."""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser."""
        parser = argparse.ArgumentParser(
            description='DDA Toolkit - Database Development Assistant',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Launch GUI
  python main.py --gui

  # Update female names with English and Arabic
  python main.py --tool name-generator --db company_db --table employees \\
                 --gender-col gender --name-col first_name \\
                 --gender female --groups English,Arabic

  # Preview changes (dry run)
  python main.py --tool name-generator --db test_db --table users \\
                 --dry-run --preview-rows 20
            """
        )

        # Global options
        parser.add_argument('--gui', action='store_true',
                          help='Launch graphical user interface')

        parser.add_argument('--tool', choices=['name-generator'],
                          help='Tool to use')

        # Database connection
        parser.add_argument('--host', default='localhost',
                          help='MySQL host (default: localhost)')

        parser.add_argument('--port', type=int, default=3306,
                          help='MySQL port (default: 3306)')

        parser.add_argument('--user', default='root',
                          help='MySQL user (default: root)')

        parser.add_argument('--password',
                          help='MySQL password')

        parser.add_argument('--db', '--database',
                          help='Database name')

        # Name generator options
        parser.add_argument('--table',
                          help='Table name')

        parser.add_argument('--gender-col',
                          help='Gender column name')

        parser.add_argument('--name-col',
                          help='Name column(s) - comma separated for multiple')

        parser.add_argument('--gender', choices=['male', 'female', 'both'],
                          default='both',
                          help='Target gender (default: both)')

        parser.add_argument('--groups',
                          help='Name groups - comma separated (e.g., English,Arabic,Asian)')

        parser.add_argument('--distribution', choices=['equal', 'proportional'],
                          default='proportional',
                          help='Distribution mode (default: proportional)')

        parser.add_argument('--where',
                          help='WHERE clause for filtering rows')

        parser.add_argument('--limit', type=int,
                          help='Limit number of rows to update')

        parser.add_argument('--batch-size', type=int, default=1000,
                          help='Batch size for updates (default: 1000)')

        parser.add_argument('--backup', choices=['yes', 'no'], default='no',
                          help='Create backup before update')

        parser.add_argument('--dry-run', action='store_true',
                          help='Preview changes without executing')

        parser.add_argument('--preview-rows', type=int, default=10,
                          help='Number of preview rows (default: 10)')

        parser.add_argument('--verbose', '-v', action='store_true',
                          help='Verbose output')

        return parser

    def run(self, args: List[str] = None):
        """Run CLI interface."""
        if args is None:
            args = sys.argv[1:]

        parsed_args = self.parser.parse_args(args)

        # Configure logging
        log_level = logging.DEBUG if parsed_args.verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Launch GUI if requested
        if parsed_args.gui:
            self._launch_gui()
            return

        # Run tool if specified
        if parsed_args.tool:
            if parsed_args.tool == 'name-generator':
                self._run_name_generator(parsed_args)
            else:
                print(f"Unknown tool: {parsed_args.tool}")
                sys.exit(1)
        else:
            self.parser.print_help()

    def _launch_gui(self):
        """Launch GUI application."""
        from .gui_app import DDAApplication
        import tkinter as tk

        print("Launching GUI...")
        root = tk.Tk()
        app = DDAApplication(root)
        app.run()

    def _run_name_generator(self, args):
        """Run name generator tool."""
        # Validate required arguments
        required = ['db', 'table']
        missing = [arg for arg in required if not getattr(args, arg.replace('-', '_'))]

        if missing:
            print(f"Error: Missing required arguments: {', '.join(['--' + arg for arg in missing])}")
            sys.exit(1)

        try:
            # Initialize name randomizer
            randomizer = NameRandomizer(
                host=args.host,
                port=args.port,
                user=args.user,
                password=args.password,
                database=args.db
            )

            # Auto-detect columns if not specified
            gender_col = args.gender_col
            name_cols = args.name_col.split(',') if args.name_col else []

            if not gender_col:
                print("Auto-detecting gender column...")
                gender_col = randomizer.db_manager.detect_gender_column(args.table, args.db)
                if gender_col:
                    print(f"  → Detected: {gender_col}")
                else:
                    print("Error: Could not detect gender column. Please specify with --gender-col")
                    sys.exit(1)

            if not name_cols:
                print("Auto-detecting name columns...")
                name_cols = randomizer.db_manager.detect_name_columns(args.table, args.db)
                if name_cols:
                    print(f"  → Detected: {', '.join(name_cols)}")
                else:
                    print("Error: Could not detect name columns. Please specify with --name-col")
                    sys.exit(1)

            # Prepare configuration
            config = {
                'table': args.table,
                'gender_column': gender_col,
                'name_columns': name_cols,
                'target_gender': args.gender,
                'name_groups': args.groups.split(',') if args.groups else ['all'],
                'distribution': args.distribution,
                'where_clause': args.where,
                'batch_size': args.batch_size,
                'preserve_null': True,
                'primary_key': 'id'  # Configurable if needed
            }

            # Preview or execute
            if args.dry_run:
                print("\n=== DRY RUN MODE - No changes will be made ===\n")

                # Show statistics
                stats = randomizer.get_statistics(config)
                print(f"Total rows in table: {stats['total_rows']}")
                print(f"Gender distribution: {stats['gender_distribution']}")

                # Show preview
                print(f"\nPreview of {args.preview_rows} changes:")
                print("-" * 80)

                preview = randomizer.preview_changes(config, limit=args.preview_rows)

                for i, row in enumerate(preview, 1):
                    print(f"\nRow {i}:")
                    for change in row['changes']:
                        print(f"  {change['column']}: {change['old']} → {change['new']}")

                print("\n" + "=" * 80)
                print("Dry run completed. Use without --dry-run to execute.")

            else:
                # Execute update
                print("\n=== EXECUTING UPDATE ===\n")

                # Confirmation
                response = input("Are you sure you want to proceed? (yes/no): ")
                if response.lower() != 'yes':
                    print("Update cancelled.")
                    return

                print("Executing update...")
                result = randomizer.execute_update(config, dry_run=False)

                print("\n=== UPDATE COMPLETED ===\n")
                print(f"Total rows processed: {result['total_rows']}")
                print(f"Rows updated: {result['updated_rows']}")
                print(f"Rows skipped: {result['skipped_rows']}")

                if result['errors']:
                    print(f"\nErrors encountered: {len(result['errors'])}")
                    for error in result['errors'][:5]:  # Show first 5 errors
                        print(f"  - {error}")

        except Exception as e:
            logger.error(f"Error running name generator: {e}", exc_info=True)
            print(f"Error: {e}")
            sys.exit(1)


def main():
    """Main CLI entry point."""
    cli = CLIInterface()
    cli.run()


if __name__ == '__main__':
    main()
