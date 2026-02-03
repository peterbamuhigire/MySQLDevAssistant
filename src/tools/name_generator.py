"""
Name Randomizer Tool - Intelligently updates name columns with realistic names
"""

import pandas as pd
import random
from typing import List, Dict, Any, Optional, Tuple
import logging
from pathlib import Path
import os

from ..core.database_manager import DatabaseManager
from ..core.validator import Validator

logger = logging.getLogger(__name__)


class NameRandomizer:
    """Manages name randomization for database tables."""

    def __init__(self, host: str = None, port: int = 3306, user: str = None,
                 password: str = None, database: str = None,
                 names_dir: str = None, config_file: str = None):
        """
        Initialize Name Randomizer.

        Args:
            host: MySQL host
            port: MySQL port
            user: MySQL user
            password: MySQL password
            database: Database name
            names_dir: Directory containing name CSV files
            config_file: Path to config file
        """
        self.db_manager = DatabaseManager(
            host=host, port=port, user=user,
            password=password, database=database,
            config_file=config_file
        )

        # Set names directory
        if names_dir:
            self.names_dir = Path(names_dir)
        else:
            # Default to data/names in project root
            project_root = Path(__file__).parent.parent.parent
            self.names_dir = project_root / 'data' / 'names'

        self.female_names = None
        self.male_names = None
        self.name_groups = {'female': [], 'male': []}

        # Load names from CSV files
        self._load_names()

    def _load_names(self):
        """Load names from CSV files."""
        try:
            # Load female names
            female_csv = self.names_dir / 'female_names.csv'
            if female_csv.exists():
                self.female_names = pd.read_csv(female_csv)
                self.name_groups['female'] = self.female_names['group'].unique().tolist()
                logger.info(f"Loaded {len(self.female_names)} female names from {len(self.name_groups['female'])} groups")
            else:
                logger.warning(f"Female names file not found: {female_csv}")
                self.female_names = pd.DataFrame(columns=['group', 'name'])

            # Load male names
            male_csv = self.names_dir / 'male_names.csv'
            if male_csv.exists():
                self.male_names = pd.read_csv(male_csv)
                self.name_groups['male'] = self.male_names['group'].unique().tolist()
                logger.info(f"Loaded {len(self.male_names)} male names from {len(self.name_groups['male'])} groups")
            else:
                logger.warning(f"Male names file not found: {male_csv}")
                self.male_names = pd.DataFrame(columns=['group', 'name'])

        except Exception as e:
            logger.error(f"Error loading names: {e}")
            self.female_names = pd.DataFrame(columns=['group', 'name'])
            self.male_names = pd.DataFrame(columns=['group', 'name'])

    def get_available_groups(self, gender: str = 'both') -> List[str]:
        """
        Get available name groups for gender.

        Args:
            gender: 'male', 'female', or 'both'

        Returns:
            List of group names
        """
        if gender == 'male':
            return self.name_groups['male']
        elif gender == 'female':
            return self.name_groups['female']
        else:  # both
            # Return union of both groups
            return list(set(self.name_groups['male'] + self.name_groups['female']))

    def get_random_name(self, gender: str, groups: List[str] = None,
                       distribution: str = 'proportional', full_name: bool = False) -> str:
        """
        Get a random name based on criteria.

        Args:
            gender: 'male' or 'female'
            groups: List of group names (None = all groups)
            distribution: 'equal' or 'proportional'
            full_name: If True, generate "FirstName LastName" format

        Returns:
            Random name string
        """
        # Select appropriate name dataset
        if gender == 'male':
            names_df = self.male_names
        else:
            names_df = self.female_names

        # Check if dataframe loaded properly
        if names_df is None or names_df.empty:
            logger.error(f"Names dataframe is empty or None for gender={gender}. Check if CSV files are loaded.")
            return f"Unknown_{gender}"

        # Normalize groups to lowercase for case-insensitive comparison
        groups_lower = [g.lower() for g in groups] if groups else []

        # Filter by groups if specified (skip if 'all' is selected)
        if groups_lower and 'all' not in groups_lower:
            logger.debug(f"Filtering names by groups: {groups}")
            names_df = names_df[names_df['group'].isin(groups)]
        else:
            logger.debug(f"Using all available names (groups={groups})")

        if names_df.empty:
            logger.warning(f"No names available after filtering: gender={gender}, groups={groups}, available_groups={self.name_groups.get(gender, [])}")
            return f"Unknown_{gender}"

        if full_name:
            # Generate "FirstName LastName" format
            first_name = random.choice(names_df['name'].tolist())
            last_name = random.choice(names_df['name'].tolist())
            return f"{first_name} {last_name}"
        else:
            if distribution == 'equal':
                # Equal chance for all groups - sample from all filtered names
                return random.choice(names_df['name'].tolist())
            else:  # proportional
                # Proportional to group size
                return random.choice(names_df['name'].tolist())

    def generate_email(self, name: str, full_name: bool = False) -> str:
        """
        Generate an email address based on a name.

        Args:
            name: The name to base the email on (can be full name or single name)
            full_name: Whether this is a full name (FirstName LastName)

        Returns:
            Generated email address
        """
        domains = ['email.com', 'letters.net', 'communication.co.uk']
        random_number = random.randint(100, 999)

        # Convert name to lowercase and handle spaces
        name_lower = name.lower().strip()

        if full_name and ' ' in name_lower:
            # Format: firstname.lastname###@domain
            parts = name_lower.split()
            if len(parts) >= 2:
                email_prefix = f"{parts[0]}.{parts[-1]}{random_number}"
            else:
                email_prefix = f"{name_lower.replace(' ', '.')}{random_number}"
        else:
            # Format: name###@domain (single name or no space found)
            email_prefix = f"{name_lower.replace(' ', '.')}{random_number}"

        domain = random.choice(domains)
        return f"{email_prefix}@{domain}"

    def preview_changes(self, config: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Preview changes that would be made.

        Args:
            config: Configuration dictionary
            limit: Number of samples to show

        Returns:
            List of preview dictionaries
        """
        # Validate config
        errors = Validator.validate_config(config)
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

        table = config['table']
        gender_column = config['gender_column']
        name_columns = config['name_columns']
        target_gender = Validator.normalize_gender(config['target_gender'])
        name_groups = config.get('name_groups', ['all'])
        where_clause = config.get('where_clause', None)
        full_name_mode = config.get('full_name_mode', False)

        # Build WHERE clause
        where_parts = []

        if target_gender != 'both':
            # Filter by specific gender
            gender_values = {
                'male': "('male', 'Male', 'MALE', 'M', 'm', '1')",
                'female': "('female', 'Female', 'FEMALE', 'F', 'f', '2')"
            }
            where_parts.append(f"`{gender_column}` IN {gender_values[target_gender]}")

        if where_clause:
            where_parts.append(f"({where_clause})")

        full_where = " AND ".join(where_parts) if where_parts else None

        # Get sample data
        sample_data = []
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)

                query = f"SELECT * FROM `{table}`"
                if full_where:
                    query += f" WHERE {full_where}"
                query += f" LIMIT {limit}"

                cursor.execute(query)
                rows = cursor.fetchall()

                for row in rows:
                    gender_value = str(row.get(gender_column, '')).lower()
                    gender = Validator.normalize_gender(gender_value)

                    if not gender:
                        continue

                    # Skip if target gender specified and doesn't match
                    if target_gender != 'both' and gender != target_gender:
                        continue

                    preview_row = {
                        'original': row.copy(),
                        'updated': row.copy(),
                        'changes': []
                    }

                    generated_name = None
                    update_names = config.get('update_names', True)
                    update_emails = config.get('update_emails', True)

                    # Generate names if name columns are specified AND we should update them
                    if name_columns and update_names:
                        for name_col in name_columns:
                            old_name = row.get(name_col)
                            new_name = self.get_random_name(
                                gender=gender,
                                groups=name_groups,
                                distribution=config.get('distribution', 'proportional'),
                                full_name=full_name_mode
                            )

                            preview_row['updated'][name_col] = new_name
                            preview_row['changes'].append({
                                'column': name_col,
                                'old': old_name,
                                'new': new_name
                            })
                            # Store first generated name for email generation
                            if generated_name is None:
                                generated_name = new_name

                    # Generate email if email column is specified AND we should update it
                    email_column = config.get('email_column')
                    if email_column and update_emails:
                        old_email = row.get(email_column)
                        # If we generated new names, use those for email
                        if generated_name:
                            new_email = self.generate_email(generated_name, full_name_mode)
                        else:
                            # Otherwise, read existing names from the row
                            if name_columns:
                                # Combine all selected name columns
                                name_parts = []
                                for name_col in name_columns:
                                    name_val = row.get(name_col)
                                    if name_val:
                                        name_parts.append(str(name_val))

                                if name_parts:
                                    existing_name = ' '.join(name_parts) if len(name_parts) > 1 else name_parts[0]
                                else:
                                    existing_name = "user"
                            else:
                                existing_name = "user"

                            new_email = self.generate_email(existing_name, full_name_mode)

                        preview_row['updated'][email_column] = new_email
                        preview_row['changes'].append({
                            'column': email_column,
                            'old': old_email,
                            'new': new_email
                        })

                    sample_data.append(preview_row)

                cursor.close()

        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            raise

        return sample_data

    def execute_update(self, config: Dict[str, Any],
                      dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute name randomization update.

        Args:
            config: Configuration dictionary
            dry_run: If True, don't actually update database

        Returns:
            Results dictionary with statistics
        """
        # Validate config
        errors = Validator.validate_config(config)
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

        table = config['table']
        gender_column = config['gender_column']
        name_columns = config['name_columns']
        target_gender = Validator.normalize_gender(config['target_gender'])
        name_groups = config.get('name_groups', ['all'])
        where_clause = config.get('where_clause', None)
        full_name_mode = config.get('full_name_mode', False)
        batch_size = config.get('batch_size', 1000)
        preserve_null = config.get('preserve_null', True)

        # Build WHERE clause
        where_parts = []

        if target_gender != 'both':
            # Filter by specific gender
            gender_values = {
                'male': "('male', 'Male', 'MALE', 'M', 'm', '1')",
                'female': "('female', 'Female', 'FEMALE', 'F', 'f', '2')"
            }
            where_parts.append(f"`{gender_column}` IN {gender_values[target_gender]}")

        if where_clause:
            where_parts.append(f"({where_clause})")

        full_where = " AND ".join(where_parts) if where_parts else None

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
                if full_where:
                    count_query += f" WHERE {full_where}"

                cursor.execute(count_query)
                results['total_rows'] = cursor.fetchone()['count']

                # Fetch rows in batches
                offset = 0
                while True:
                    fetch_query = f"SELECT * FROM `{table}`"
                    if full_where:
                        fetch_query += f" WHERE {full_where}"
                    fetch_query += f" LIMIT {batch_size} OFFSET {offset}"

                    cursor.execute(fetch_query)
                    rows = cursor.fetchall()

                    if not rows:
                        break

                    # Process batch
                    for row in rows:
                        try:
                            gender_value = str(row.get(gender_column, '')).lower()
                            gender = Validator.normalize_gender(gender_value)

                            # If gender can't be determined, assign random gender
                            if not gender:
                                gender = random.choice(['male', 'female'])
                                logger.info(f"Assigned random gender '{gender}' for row with invalid gender value: {gender_value}")

                            # Skip if target gender specified and doesn't match
                            if target_gender != 'both' and gender != target_gender:
                                results['skipped_rows'] += 1
                                continue

                            # Get primary key for UPDATE
                            pk_col = config.get('primary_key', 'id')
                            pk_value = row.get(pk_col)

                            if not pk_value:
                                # Try to find any unique identifier
                                possible_keys = ['id', 'ID', 'Id', 'user_id', 'userId', 'pk']
                                for key in possible_keys:
                                    if key in row and row.get(key):
                                        pk_col = key
                                        pk_value = row.get(key)
                                        break

                                if not pk_value:
                                    # Skip row silently if no primary key found
                                    results['skipped_rows'] += 1
                                    continue

                            # Build UPDATE query
                            update_parts = []
                            generated_name = None
                            update_names = config.get('update_names', True)
                            update_emails = config.get('update_emails', True)

                            # Generate names if name columns specified AND update_names is True
                            if name_columns and update_names:
                                for name_col in name_columns:
                                    # Check if should preserve NULL
                                    if preserve_null and row.get(name_col) is None:
                                        continue

                                    new_name = self.get_random_name(
                                        gender=gender,
                                        groups=name_groups,
                                        distribution=config.get('distribution', 'proportional'),
                                        full_name=full_name_mode
                                    )

                                    update_parts.append(f"`{name_col}` = %s")
                                    # Store first generated name for email
                                    if generated_name is None:
                                        generated_name = new_name

                            # Generate email if email column specified AND update_emails is True
                            email_column = config.get('email_column')
                            if email_column and update_emails:
                                # Check if should preserve NULL
                                if not (preserve_null and row.get(email_column) is None):
                                    update_parts.append(f"`{email_column}` = %s")

                            if not update_parts:
                                results['skipped_rows'] += 1
                                continue

                            # Execute update
                            if not dry_run:
                                update_query = f"UPDATE `{table}` SET {', '.join(update_parts)} WHERE `{pk_col}` = %s"

                                # Prepare values
                                values = []

                                # Add name values if updating names
                                if name_columns and update_names:
                                    for name_col in name_columns:
                                        if preserve_null and row.get(name_col) is None:
                                            continue
                                        new_name = self.get_random_name(
                                            gender=gender,
                                            groups=name_groups,
                                            distribution=config.get('distribution', 'proportional'),
                                            full_name=full_name_mode
                                        )
                                        values.append(new_name)
                                        # Store first generated name for email
                                        if generated_name is None:
                                            generated_name = new_name

                                # Add email value if updating emails
                                if email_column and update_emails:
                                    if not (preserve_null and row.get(email_column) is None):
                                        # If we generated new names, use those for email
                                        if generated_name:
                                            new_email = self.generate_email(generated_name, full_name_mode)
                                        else:
                                            # Otherwise, read existing names from the row
                                            if name_columns:
                                                # Combine all selected name columns
                                                name_parts = []
                                                for name_col in name_columns:
                                                    name_val = row.get(name_col)
                                                    if name_val:
                                                        name_parts.append(str(name_val))

                                                if name_parts:
                                                    existing_name = ' '.join(name_parts) if len(name_parts) > 1 else name_parts[0]
                                                else:
                                                    existing_name = "user"
                                            else:
                                                existing_name = "user"

                                            new_email = self.generate_email(existing_name, full_name_mode)
                                        values.append(new_email)

                                values.append(pk_value)

                                cursor.execute(update_query, tuple(values))

                            results['updated_rows'] += 1

                        except Exception as e:
                            pk_col = config.get('primary_key', 'id')
                            pk_value = row.get(pk_col, 'unknown')
                            error_msg = f"Row {pk_col}={pk_value}: {str(e)}"
                            logger.error(f"Error processing row: {error_msg}")
                            results['errors'].append(error_msg)
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

    def get_statistics(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get statistics about what would be updated.

        Args:
            config: Configuration dictionary

        Returns:
            Statistics dictionary
        """
        table = config['table']
        gender_column = config['gender_column']
        where_clause = config.get('where_clause', None)

        stats = {
            'total_rows': 0,
            'gender_distribution': {},
            'null_values': {}
        }

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)

                # Total rows
                count_query = f"SELECT COUNT(*) as count FROM `{table}`"
                if where_clause:
                    count_query += f" WHERE {where_clause}"

                cursor.execute(count_query)
                stats['total_rows'] = cursor.fetchone()['count']

                # Gender distribution
                gender_query = f"SELECT `{gender_column}`, COUNT(*) as count FROM `{table}`"
                if where_clause:
                    gender_query += f" WHERE {where_clause}"
                gender_query += f" GROUP BY `{gender_column}`"

                cursor.execute(gender_query)
                for row in cursor.fetchall():
                    stats['gender_distribution'][row[gender_column]] = row['count']

                cursor.close()

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")

        return stats
