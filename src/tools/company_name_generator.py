"""
Company Name Generator Tool - Generates realistic company/organization names
"""

import pandas as pd
import random
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from ..core.database_manager import DatabaseManager
from ..core.validator import Validator

logger = logging.getLogger(__name__)


class CompanyNameGenerator:
    """Manages company name generation for database tables."""

    def __init__(self, host: str = None, port: int = 3306, user: str = None,
                 password: str = None, database: str = None,
                 companies_dir: str = None, config_file: str = None):
        """
        Initialize Company Name Generator.

        Args:
            host: MySQL host
            port: MySQL port
            user: MySQL user
            password: MySQL password
            database: Database name
            companies_dir: Directory containing company name CSV files
            config_file: Path to config file
        """
        self.db_manager = DatabaseManager(
            host=host, port=port, user=user,
            password=password, database=database,
            config_file=config_file
        )

        # Set companies directory
        if companies_dir:
            self.companies_dir = Path(companies_dir)
        else:
            # Default to data/companies in project root
            project_root = Path(__file__).parent.parent.parent
            self.companies_dir = project_root / 'data' / 'companies'

        self.name1_data = None
        self.name2_data = None
        self.classification_data = None
        self.available_groups = {'name1': [], 'name2': [], 'classification': []}

        # Load company name components from CSV files
        self._load_company_data()

    def _load_company_data(self):
        """Load company name components from CSV files."""
        try:
            # Load name1 (first part)
            name1_csv = self.companies_dir / 'name1.csv'
            if name1_csv.exists():
                self.name1_data = pd.read_csv(name1_csv)
                self.available_groups['name1'] = self.name1_data['group'].unique().tolist()
                logger.info(f"Loaded {len(self.name1_data)} name1 entries from {len(self.available_groups['name1'])} groups")
            else:
                logger.warning(f"Name1 file not found: {name1_csv}")
                self.name1_data = pd.DataFrame(columns=['group', 'name'])

            # Load name2 (second part)
            name2_csv = self.companies_dir / 'name2.csv'
            if name2_csv.exists():
                self.name2_data = pd.read_csv(name2_csv)
                self.available_groups['name2'] = self.name2_data['group'].unique().tolist()
                logger.info(f"Loaded {len(self.name2_data)} name2 entries from {len(self.available_groups['name2'])} groups")
            else:
                logger.warning(f"Name2 file not found: {name2_csv}")
                self.name2_data = pd.DataFrame(columns=['group', 'name'])

            # Load classification (suffix)
            classification_csv = self.companies_dir / 'classification.csv'
            if classification_csv.exists():
                self.classification_data = pd.read_csv(classification_csv)
                self.available_groups['classification'] = self.classification_data['group'].unique().tolist()
                logger.info(f"Loaded {len(self.classification_data)} classification entries from {len(self.available_groups['classification'])} groups")
            else:
                logger.warning(f"Classification file not found: {classification_csv}")
                self.classification_data = pd.DataFrame(columns=['group', 'name'])

        except Exception as e:
            logger.error(f"Error loading company data: {e}")
            self.name1_data = pd.DataFrame(columns=['group', 'name'])
            self.name2_data = pd.DataFrame(columns=['group', 'name'])
            self.classification_data = pd.DataFrame(columns=['group', 'name'])

    def get_available_groups(self, component: str = 'all') -> List[str]:
        """
        Get available groups for a component.

        Args:
            component: 'name1', 'name2', 'classification', or 'all'

        Returns:
            List of group names
        """
        if component == 'all':
            # Return union of all groups
            all_groups = set()
            for groups in self.available_groups.values():
                all_groups.update(groups)
            return list(all_groups)
        else:
            return self.available_groups.get(component, [])

    def get_random_company_name(self, name1_groups: List[str] = None,
                                name2_groups: List[str] = None,
                                classification_groups: List[str] = None) -> str:
        """
        Generate a random company name.

        Args:
            name1_groups: List of group names for first part (None = all groups)
            name2_groups: List of group names for second part (None = all groups)
            classification_groups: List of group names for classification (None = all groups)

        Returns:
            Company name string in format "Name1 Name2 Classification"
        """
        # Filter name1
        name1_df = self.name1_data
        if name1_groups and 'all' not in [g.lower() for g in name1_groups]:
            name1_df = name1_df[name1_df['group'].isin(name1_groups)]

        # Filter name2
        name2_df = self.name2_data
        if name2_groups and 'all' not in [g.lower() for g in name2_groups]:
            name2_df = name2_df[name2_df['group'].isin(name2_groups)]

        # Filter classification
        classification_df = self.classification_data
        if classification_groups and 'all' not in [g.lower() for g in classification_groups]:
            classification_df = classification_df[classification_df['group'].isin(classification_groups)]

        # Get random components
        if name1_df.empty:
            logger.warning(f"No name1 data available for groups={name1_groups}")
            name1 = "Unknown"
        else:
            name1 = random.choice(name1_df['name'].tolist())

        if name2_df.empty:
            logger.warning(f"No name2 data available for groups={name2_groups}")
            name2 = "Company"
        else:
            name2 = random.choice(name2_df['name'].tolist())

        if classification_df.empty:
            logger.warning(f"No classification data available for groups={classification_groups}")
            classification = "Inc"
        else:
            classification = random.choice(classification_df['name'].tolist())

        # Combine into company name with space between names and capitalization
        return f"{name1.capitalize()} {name2.capitalize()} {classification}"

    def preview_changes(self, config: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Preview changes that would be made.

        Args:
            config: Configuration dictionary
            limit: Number of samples to show

        Returns:
            List of preview dictionaries
        """
        table = config['table']
        company_columns = config['company_columns']
        name1_groups = config.get('name1_groups', ['all'])
        name2_groups = config.get('name2_groups', ['all'])
        classification_groups = config.get('classification_groups', ['all'])
        where_clause = config.get('where_clause', None)

        # Get sample data
        sample_data = []
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)

                query = f"SELECT * FROM `{table}`"
                if where_clause:
                    query += f" WHERE {where_clause}"
                query += f" LIMIT {limit}"

                cursor.execute(query)
                rows = cursor.fetchall()

                for row in rows:
                    preview_row = {
                        'original': row.copy(),
                        'updated': row.copy(),
                        'changes': []
                    }

                    # Generate new company names for each column
                    for company_col in company_columns:
                        old_name = row.get(company_col)
                        new_name = self.get_random_company_name(
                            name1_groups=name1_groups,
                            name2_groups=name2_groups,
                            classification_groups=classification_groups
                        )

                        preview_row['updated'][company_col] = new_name
                        preview_row['changes'].append({
                            'column': company_col,
                            'old': old_name,
                            'new': new_name
                        })

                    sample_data.append(preview_row)

                cursor.close()

        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            raise

        return sample_data

    def execute_update(self, config: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute company name randomization update.

        Args:
            config: Configuration dictionary
            dry_run: If True, don't actually update database

        Returns:
            Results dictionary with statistics
        """
        table = config['table']
        company_columns = config['company_columns']
        name1_groups = config.get('name1_groups', ['all'])
        name2_groups = config.get('name2_groups', ['all'])
        classification_groups = config.get('classification_groups', ['all'])
        where_clause = config.get('where_clause', None)
        batch_size = config.get('batch_size', 1000)
        preserve_null = config.get('preserve_null', True)

        results = {
            'total_rows': 0,
            'updated_rows': 0,
            'skipped_rows': 0,
            'errors': [],
            'dry_run': dry_run
        }

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)

                # Get total count
                count_query = f"SELECT COUNT(*) as count FROM `{table}`"
                if where_clause:
                    count_query += f" WHERE {where_clause}"

                cursor.execute(count_query)
                results['total_rows'] = cursor.fetchone()['count']

                # Fetch rows in batches
                offset = 0
                while True:
                    fetch_query = f"SELECT * FROM `{table}`"
                    if where_clause:
                        fetch_query += f" WHERE {where_clause}"
                    fetch_query += f" LIMIT {batch_size} OFFSET {offset}"

                    cursor.execute(fetch_query)
                    rows = cursor.fetchall()

                    if not rows:
                        break

                    # Process batch
                    for row in rows:
                        try:
                            # Get primary key for UPDATE
                            pk_col = config.get('primary_key', 'id')
                            pk_value = row.get(pk_col)

                            if not pk_value:
                                logger.warning(f"No primary key found for row: {row}")
                                results['skipped_rows'] += 1
                                continue

                            # Build UPDATE query
                            update_parts = []
                            values = []
                            for company_col in company_columns:
                                # Check if should preserve NULL
                                if preserve_null and row.get(company_col) is None:
                                    continue

                                new_name = self.get_random_company_name(
                                    name1_groups=name1_groups,
                                    name2_groups=name2_groups,
                                    classification_groups=classification_groups
                                )

                                update_parts.append(f"`{company_col}` = %s")
                                values.append(new_name)

                            if not update_parts:
                                results['skipped_rows'] += 1
                                continue

                            # Execute update
                            if not dry_run:
                                update_query = f"UPDATE `{table}` SET {', '.join(update_parts)} WHERE `{pk_col}` = %s"
                                values.append(pk_value)
                                cursor.execute(update_query, tuple(values))

                            results['updated_rows'] += 1

                        except Exception as e:
                            logger.error(f"Error processing row: {e}")
                            results['errors'].append(str(e))
                            results['skipped_rows'] += 1

                    offset += batch_size

                # Commit transaction if not dry run
                if not dry_run:
                    conn.commit()

                cursor.close()

        except Exception as e:
            logger.error(f"Error executing update: {e}")
            results['errors'].append(str(e))
            raise

        return results
