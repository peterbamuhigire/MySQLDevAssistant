"""
Initialize name databases - verify CSV files exist and are valid
"""

import sys
from pathlib import Path
import pandas as pd


def main():
    """Verify name database files."""
    project_root = Path(__file__).parent.parent
    names_dir = project_root / 'data' / 'names'

    print("DDA Toolkit - Name Database Initialization")
    print("=" * 60)

    # Check female names
    female_csv = names_dir / 'female_names.csv'
    if female_csv.exists():
        df = pd.read_csv(female_csv)
        print(f"✓ Female names: {len(df)} names loaded")
        print(f"  Groups: {', '.join(df['group'].unique())}")
    else:
        print(f"✗ Female names file not found: {female_csv}")
        sys.exit(1)

    # Check male names
    male_csv = names_dir / 'male_names.csv'
    if male_csv.exists():
        df = pd.read_csv(male_csv)
        print(f"✓ Male names: {len(df)} names loaded")
        print(f"  Groups: {', '.join(df['group'].unique())}")
    else:
        print(f"✗ Male names file not found: {male_csv}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Name database initialization completed successfully!")


if __name__ == '__main__':
    main()
