"""
Phone Number Generator Tool - Generates random phone numbers with country codes
"""

import random
from typing import List, Dict, Any
import logging
from pathlib import Path

from ..core.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class PhoneNumberGenerator:
    """Manages phone number generation for database tables."""

    # Common country codes
    COUNTRY_CODES = {
        'Uganda': '+256',
        'Kenya': '+254',
        'Tanzania': '+255',
        'Rwanda': '+250',
        'USA': '+1',
        'UK': '+44',
        'South Africa': '+27',
        'Nigeria': '+234',
        'Ghana': '+233',
        'India': '+91',
        'Pakistan': '+92',
        'Bangladesh': '+880',
        'Custom': ''  # User can enter custom
    }

    def __init__(self, host: str = None, port: int = 3306, user: str = None,
                 password: str = None, database: str = None, config_file: str = None):
        """
        Initialize Phone Number Generator.

        Args:
            host: MySQL host
            port: MySQL port
            user: MySQL user
            password: MySQL password
            database: Database name
            config_file: Path to config file
        """
        self.db_manager = DatabaseManager(
            host=host, port=port, user=user,
            password=password, database=database,
            config_file=config_file
        )

    def get_country_codes(self) -> Dict[str, str]:
        """Get available country codes."""
        return self.COUNTRY_CODES.copy()

    def generate_phone_number(self, country_code: str, prefix: str,
                             min_number: int, max_number: int) -> str:
        """
        Generate a random phone number.

        Args:
            country_code: Country code (e.g., '+256')
            prefix: Prefix after country code (e.g., '7')
            min_number: Minimum number in range
            max_number: Maximum number in range

        Returns:
            Phone number string (e.g., '+256784464178')
        """
        # Generate random number within range
        random_num = random.randint(min_number, max_number)

        # Combine parts
        phone_number = f"{country_code}{prefix}{random_num}"

        return phone_number

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
        phone_columns = config['phone_columns']
        country_code = config['country_code']
        prefix = config['prefix']
        min_number = config['min_number']
        max_number = config['max_number']
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

                    # Generate new phone numbers for each column
                    for phone_col in phone_columns:
                        old_phone = row.get(phone_col)
                        new_phone = self.generate_phone_number(
                            country_code=country_code,
                            prefix=prefix,
                            min_number=min_number,
                            max_number=max_number
                        )

                        preview_row['updated'][phone_col] = new_phone
                        preview_row['changes'].append({
                            'column': phone_col,
                            'old': old_phone,
                            'new': new_phone
                        })

                    sample_data.append(preview_row)

                cursor.close()

        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            raise

        return sample_data

    def execute_update(self, config: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute phone number randomization update.

        Args:
            config: Configuration dictionary
            dry_run: If True, don't actually update database

        Returns:
            Results dictionary with statistics
        """
        table = config['table']
        phone_columns = config['phone_columns']
        country_code = config['country_code']
        prefix = config['prefix']
        min_number = config['min_number']
        max_number = config['max_number']
        where_clause = config.get('where_clause', None)
        batch_size = config.get('batch_size', 1000)
        preserve_null = config.get('preserve_null', False)

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
                            values = []
                            for phone_col in phone_columns:
                                # Check if should preserve NULL
                                if preserve_null and row.get(phone_col) is None:
                                    continue

                                new_phone = self.generate_phone_number(
                                    country_code=country_code,
                                    prefix=prefix,
                                    min_number=min_number,
                                    max_number=max_number
                                )

                                update_parts.append(f"`{phone_col}` = %s")
                                values.append(new_phone)

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
