"""
Code Generator Tool - Generates random codes/serial numbers
"""

import random
import string
from typing import List, Dict, Any
import logging

from ..core.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class CodeGenerator:
    """Manages code/serial number generation for database tables."""

    def __init__(self, host: str = None, port: int = 3306, user: str = None,
                 password: str = None, database: str = None, config_file: str = None):
        """
        Initialize Code Generator.

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

    def is_foreign_key(self, table: str, column: str, database: str = None) -> Dict[str, Any]:
        """
        Check if a column is a foreign key.

        Args:
            table: Table name
            column: Column name
            database: Database name

        Returns:
            Dictionary with FK info or None if not a FK
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)

                # Query to check if column is a foreign key
                query = """
                    SELECT
                        CONSTRAINT_NAME,
                        REFERENCED_TABLE_NAME,
                        REFERENCED_COLUMN_NAME
                    FROM information_schema.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = %s
                        AND TABLE_NAME = %s
                        AND COLUMN_NAME = %s
                        AND REFERENCED_TABLE_NAME IS NOT NULL
                """

                cursor.execute(query, (database or self.db_manager.database, table, column))
                result = cursor.fetchone()
                cursor.close()

                if result:
                    return {
                        'is_fk': True,
                        'constraint_name': result['CONSTRAINT_NAME'],
                        'references_table': result['REFERENCED_TABLE_NAME'],
                        'references_column': result['REFERENCED_COLUMN_NAME']
                    }
                else:
                    return {'is_fk': False}

        except Exception as e:
            logger.error(f"Error checking foreign key: {e}")
            # Return safe default (assume it's a FK to be safe)
            return {'is_fk': True, 'error': str(e)}

    def check_columns_for_fk(self, table: str, columns: List[str], database: str = None) -> Dict[str, Dict[str, Any]]:
        """
        Check multiple columns for FK constraints.

        Args:
            table: Table name
            columns: List of column names
            database: Database name

        Returns:
            Dictionary mapping column names to FK info
        """
        results = {}
        for column in columns:
            results[column] = self.is_foreign_key(table, column, database)
        return results

    def generate_code(self, code_type: str, length: int, prefix: str = '') -> str:
        """
        Generate a random code.

        Args:
            code_type: 'letters', 'numbers', or 'mixed'
            length: Total length of code (including prefix)
            prefix: Optional prefix (up to 3 characters)

        Returns:
            Generated code string
        """
        # Calculate remaining length after prefix
        remaining_length = length - len(prefix)

        if remaining_length < 1:
            remaining_length = 1

        # Define character sets
        if code_type == 'letters':
            charset = string.ascii_uppercase
        elif code_type == 'numbers':
            charset = string.digits
        else:  # mixed
            charset = string.ascii_uppercase + string.digits

        # Generate random part
        random_part = ''.join(random.choice(charset) for _ in range(remaining_length))

        # Combine prefix and random part
        return f"{prefix.upper()}{random_part}"

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
        code_columns = config['code_columns']
        code_type = config['code_type']
        code_length = config['code_length']
        prefix = config.get('prefix', '')
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

                    # Generate new codes for each column
                    for code_col in code_columns:
                        old_code = row.get(code_col)
                        new_code = self.generate_code(
                            code_type=code_type,
                            length=code_length,
                            prefix=prefix
                        )

                        preview_row['updated'][code_col] = new_code
                        preview_row['changes'].append({
                            'column': code_col,
                            'old': str(old_code) if old_code else 'NULL',
                            'new': new_code
                        })

                    sample_data.append(preview_row)

                cursor.close()

        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            raise

        return sample_data

    def execute_update(self, config: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute code generation update.

        Args:
            config: Configuration dictionary
            dry_run: If True, don't actually update database

        Returns:
            Results dictionary with statistics
        """
        table = config['table']
        code_columns = config['code_columns']
        code_type = config['code_type']
        code_length = config['code_length']
        prefix = config.get('prefix', '')
        where_clause = config.get('where_clause', None)
        batch_size = config.get('batch_size', 1000)
        preserve_null = config.get('preserve_null', False)
        ensure_unique = config.get('ensure_unique', True)

        results = {
            'total_rows': 0,
            'updated_rows': 0,
            'skipped_rows': 0,
            'errors': [],
            'dry_run': dry_run
        }

        # Track generated codes to ensure uniqueness
        generated_codes = set()

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
                            for code_col in code_columns:
                                # Check if should preserve NULL
                                if preserve_null and row.get(code_col) is None:
                                    continue

                                # Generate unique code
                                attempts = 0
                                max_attempts = 100
                                while attempts < max_attempts:
                                    new_code = self.generate_code(
                                        code_type=code_type,
                                        length=code_length,
                                        prefix=prefix
                                    )

                                    if not ensure_unique or new_code not in generated_codes:
                                        generated_codes.add(new_code)
                                        break

                                    attempts += 1

                                if attempts >= max_attempts:
                                    logger.warning(f"Could not generate unique code after {max_attempts} attempts")
                                    results['skipped_rows'] += 1
                                    continue

                                update_parts.append(f"`{code_col}` = %s")
                                values.append(new_code)

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
