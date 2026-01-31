"""
DDA Toolkit - Main Entry Point
Database Development Assistant
"""

import sys
import logging
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from src.ui.cli_interface import CLIInterface
from src.utils.logger import setup_logger


def main():
    """Main entry point for DDA toolkit."""
    # Setup logging
    config_file = project_root / 'config' / 'tool_config.yaml'
    logger = setup_logger('dda', str(config_file) if config_file.exists() else None)

    logger.info("Starting DDA Toolkit")

    try:
        # Run CLI interface
        cli = CLIInterface()
        cli.run()

    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
