"""
Date Randomizer Tool - Randomizes date/datetime columns within specified ranges
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

from ..core.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class DateRandomizer:
    """Manages date randomization for database tables."""

    def __init__(self, host: str = None, port: int = 3306, user: str = None,
                 password: str = None, database: str = None, config_file: str = None):
        """
        Initialize Date Randomizer.

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

    def get_datetime_columns(self, table: str, database: str = None) -> List[Dict[str, str]]:
        """
        Get all datetime-type columns from a table.

        Args:
            table: Table name
            database: Database name

        Returns:
            List of dictionaries with column info
        """
        datetime_types = ['date', 'datetime', 'timestamp', 'time', 'year']
        schema = self.db_manager.get_table_schema(table, database)

        datetime_cols = []
        for col in schema:
            col_type = col['Type'].lower()
            if any(dt_type in col_type for dt_type in datetime_types):
                datetime_cols.append({
                    'name': col['Field'],
                    'type': col['Type'],
                    'nullable': col['Null'] == 'YES'
                })

        return datetime_cols

    def generate_random_datetime(self, start_date: datetime, end_date: datetime,
                                 column_type: str, include_time: bool = True) -> str:
        """
        Generate a random datetime between start and end dates.

        Args:
            start_date: Start of date range
            end_date: End of date range
            column_type: MySQL column type (DATE, DATETIME, TIMESTAMP)
            include_time: Whether to include time component

        Returns:
            Formatted datetime string
        """
        # Calculate random datetime
        time_diff = end_date - start_date
        random_seconds = random.randint(0, int(time_diff.total_seconds()))
        random_datetime = start_date + timedelta(seconds=random_seconds)

        # Format based on column type
        col_type_lower = column_type.lower()

        if 'date' in col_type_lower and 'datetime' not in col_type_lower:
            # DATE type - no time component
            return random_datetime.strftime('%Y-%m-%d')
        elif 'time' in col_type_lower and 'datetime' not in col_type_lower:
            # TIME type - only time component
            return random_datetime.strftime('%H:%M:%S')
        elif 'year' in col_type_lower:
            # YEAR type - only year
            return random_datetime.strftime('%Y')
        else:
            # DATETIME or TIMESTAMP - full datetime
            if include_time:
                return random_datetime.strftime('%Y-%m-%d %H:%M:%S')
            else:
                return random_datetime.strftime('%Y-%m-%d 00:00:00')

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
        date_columns = config['date_columns']
        start_date = config['start_date']
        end_date = config['end_date']
        include_time = config.get('include_time', True)
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

                    # Generate new dates for each column
                    for date_col_info in date_columns:
                        col_name = date_col_info['name']
                        col_type = date_col_info['type']
                        old_date = row.get(col_name)

                        new_date = self.generate_random_datetime(
                            start_date=start_date,
                            end_date=end_date,
                            column_type=col_type,
                            include_time=include_time
                        )

                        preview_row['updated'][col_name] = new_date
                        preview_row['changes'].append({
                            'column': col_name,
                            'old': str(old_date) if old_date else 'NULL',
                            'new': new_date
                        })

                    sample_data.append(preview_row)

                cursor.close()

        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            raise

        return sample_data

    def execute_update(self, config: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute date randomization update.

        Args:
            config: Configuration dictionary
            dry_run: If True, don't actually update database

        Returns:
            Results dictionary with statistics
        """
        table = config['table']
        date_columns = config['date_columns']
        start_date = config['start_date']
        end_date = config['end_date']
        include_time = config.get('include_time', True)
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
                                possible_keys = ['id', 'ID', 'Id', 'pk', 'primary_id']
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
                            for date_col_info in date_columns:
                                col_name = date_col_info['name']
                                col_type = date_col_info['type']

                                # Check if should preserve NULL
                                if preserve_null and row.get(col_name) is None:
                                    continue

                                new_date = self.generate_random_datetime(
                                    start_date=start_date,
                                    end_date=end_date,
                                    column_type=col_type,
                                    include_time=include_time
                                )

                                update_parts.append(f"`{col_name}` = %s")
                                values.append(new_date)

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
