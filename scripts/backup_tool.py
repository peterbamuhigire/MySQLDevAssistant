"""
Database backup utility script
"""

import argparse
import sys
from pathlib import Path
import subprocess
from datetime import datetime


def create_mysql_dump(host, port, user, password, database, output_file):
    """Create MySQL dump using mysqldump."""
    cmd = [
        'mysqldump',
        f'--host={host}',
        f'--port={port}',
        f'--user={user}',
        f'--password={password}',
        database
    ]

    try:
        with open(output_file, 'w') as f:
            subprocess.run(cmd, stdout=f, check=True, stderr=subprocess.PIPE)

        print(f"✓ Backup created: {output_file}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"✗ Backup failed: {e.stderr.decode()}")
        return False


def main():
    """Main backup function."""
    parser = argparse.ArgumentParser(description='MySQL Database Backup Tool')

    parser.add_argument('--host', default='localhost', help='MySQL host')
    parser.add_argument('--port', default='3306', help='MySQL port')
    parser.add_argument('--user', default='root', help='MySQL user')
    parser.add_argument('--password', required=True, help='MySQL password')
    parser.add_argument('--database', required=True, help='Database name')
    parser.add_argument('--output-dir', default='backups', help='Output directory')

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f"{args.database}_{timestamp}.sql"

    print("DDA Toolkit - Database Backup")
    print("=" * 60)
    print(f"Database: {args.database}")
    print(f"Output: {output_file}")
    print("=" * 60)

    success = create_mysql_dump(
        args.host,
        args.port,
        args.user,
        args.password,
        args.database,
        output_file
    )

    if success:
        print("\nBackup completed successfully!")
        sys.exit(0)
    else:
        print("\nBackup failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
