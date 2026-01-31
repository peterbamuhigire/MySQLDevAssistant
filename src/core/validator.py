"""
Validator - Input validation and constraint checking
"""

import re
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Validator:
    """Validates inputs and database constraints."""

    @staticmethod
    def validate_table_name(table_name: str) -> bool:
        """
        Validate table name format.

        Args:
            table_name: Table name to validate

        Returns:
            True if valid, False otherwise
        """
        if not table_name:
            return False

        # MySQL table names: alphanumeric, underscore, max 64 chars
        pattern = r'^[a-zA-Z0-9_]{1,64}$'
        return bool(re.match(pattern, table_name))

    @staticmethod
    def validate_column_name(column_name: str) -> bool:
        """
        Validate column name format.

        Args:
            column_name: Column name to validate

        Returns:
            True if valid, False otherwise
        """
        if not column_name:
            return False

        # MySQL column names: alphanumeric, underscore, max 64 chars
        pattern = r'^[a-zA-Z0-9_]{1,64}$'
        return bool(re.match(pattern, column_name))

    @staticmethod
    def validate_database_name(db_name: str) -> bool:
        """
        Validate database name format.

        Args:
            db_name: Database name to validate

        Returns:
            True if valid, False otherwise
        """
        if not db_name:
            return False

        # MySQL database names: alphanumeric, underscore, max 64 chars
        pattern = r'^[a-zA-Z0-9_]{1,64}$'
        return bool(re.match(pattern, db_name))

    @staticmethod
    def validate_gender_value(gender: str) -> bool:
        """
        Validate gender value.

        Args:
            gender: Gender value to validate

        Returns:
            True if valid, False otherwise
        """
        valid_values = ['male', 'female', 'm', 'f', 'M', 'F', 'Male', 'Female',
                       'MALE', 'FEMALE', '1', '2', 'both']
        return gender in valid_values

    @staticmethod
    def normalize_gender(gender: str) -> Optional[str]:
        """
        Normalize gender value to standard format.

        Args:
            gender: Gender value to normalize

        Returns:
            Normalized gender ('male', 'female', 'both') or None
        """
        gender_lower = gender.lower()

        male_values = ['male', 'm', '1']
        female_values = ['female', 'f', '2']

        if gender_lower in male_values:
            return 'male'
        elif gender_lower in female_values:
            return 'female'
        elif gender_lower == 'both':
            return 'both'
        else:
            return None

    @staticmethod
    def validate_where_clause(where_clause: str) -> bool:
        """
        Basic validation of WHERE clause for SQL injection prevention.

        Args:
            where_clause: WHERE clause to validate

        Returns:
            True if appears safe, False otherwise
        """
        if not where_clause:
            return True

        # Block common SQL injection patterns
        dangerous_patterns = [
            r';\s*drop\s+',
            r';\s*delete\s+',
            r';\s*truncate\s+',
            r';\s*alter\s+',
            r';\s*create\s+',
            r'--',
            r'/\*',
            r'\*/',
            r'xp_',
            r'sp_',
        ]

        where_lower = where_clause.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, where_lower):
                logger.warning(f"Potentially dangerous WHERE clause detected: {where_clause}")
                return False

        return True

    @staticmethod
    def validate_row_limit(limit: int, max_limit: int = 10000) -> bool:
        """
        Validate row limit value.

        Args:
            limit: Limit value to validate
            max_limit: Maximum allowed limit

        Returns:
            True if valid, False otherwise
        """
        return 0 < limit <= max_limit

    @staticmethod
    def validate_name_groups(groups: List[str], valid_groups: List[str]) -> bool:
        """
        Validate name groups selection.

        Args:
            groups: Selected groups
            valid_groups: List of valid group names

        Returns:
            True if all groups are valid, False otherwise
        """
        if not groups:
            return False

        if 'all' in groups:
            return True

        return all(group in valid_groups for group in groups)

    @staticmethod
    def validate_distribution_mode(mode: str) -> bool:
        """
        Validate distribution mode.

        Args:
            mode: Distribution mode to validate

        Returns:
            True if valid, False otherwise
        """
        valid_modes = ['equal', 'proportional', 'custom']
        return mode in valid_modes

    @staticmethod
    def validate_name_column_type(column_info: Dict[str, Any]) -> bool:
        """
        Validate that column type is suitable for names.

        Args:
            column_info: Column information dictionary from DESCRIBE

        Returns:
            True if suitable, False otherwise
        """
        col_type = column_info.get('Type', '').lower()

        # Acceptable types for names
        suitable_types = ['varchar', 'char', 'text', 'tinytext', 'mediumtext']

        return any(t in col_type for t in suitable_types)

    @staticmethod
    def validate_gender_column_type(column_info: Dict[str, Any]) -> bool:
        """
        Validate that column type is suitable for gender.

        Args:
            column_info: Column information dictionary from DESCRIBE

        Returns:
            True if suitable, False otherwise
        """
        col_type = column_info.get('Type', '').lower()

        # Acceptable types for gender
        suitable_types = ['varchar', 'char', 'enum', 'tinyint', 'int']

        return any(t in col_type for t in suitable_types)

    @staticmethod
    def sanitize_table_name(table_name: str) -> str:
        """
        Sanitize table name for SQL queries.

        Args:
            table_name: Table name to sanitize

        Returns:
            Sanitized table name
        """
        # Remove dangerous characters, keep only alphanumeric and underscore
        return re.sub(r'[^a-zA-Z0-9_]', '', table_name)

    @staticmethod
    def sanitize_column_name(column_name: str) -> str:
        """
        Sanitize column name for SQL queries.

        Args:
            column_name: Column name to sanitize

        Returns:
            Sanitized column name
        """
        # Remove dangerous characters, keep only alphanumeric and underscore
        return re.sub(r'[^a-zA-Z0-9_]', '', column_name)

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> List[str]:
        """
        Validate complete configuration object.

        Args:
            config: Configuration dictionary

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Required fields
        required_fields = ['table', 'gender_column', 'name_columns', 'target_gender']
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")

        # Validate table name
        if 'table' in config and not Validator.validate_table_name(config['table']):
            errors.append(f"Invalid table name: {config['table']}")

        # Validate columns
        if 'gender_column' in config and not Validator.validate_column_name(config['gender_column']):
            errors.append(f"Invalid gender column name: {config['gender_column']}")

        if 'name_columns' in config:
            for col in config['name_columns']:
                if not Validator.validate_column_name(col):
                    errors.append(f"Invalid name column: {col}")

        # Validate gender
        if 'target_gender' in config and not Validator.validate_gender_value(config['target_gender']):
            errors.append(f"Invalid target gender: {config['target_gender']}")

        # Validate WHERE clause if present
        if 'where_clause' in config and config['where_clause']:
            if not Validator.validate_where_clause(config['where_clause']):
                errors.append("WHERE clause contains potentially dangerous SQL")

        # Validate distribution if present
        if 'distribution' in config and not Validator.validate_distribution_mode(config['distribution']):
            errors.append(f"Invalid distribution mode: {config['distribution']}")

        return errors
