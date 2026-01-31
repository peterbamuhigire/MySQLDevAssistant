"""
Tests for Validator module
"""

import pytest
from src.core.validator import Validator


class TestValidator:
    """Test cases for Validator class."""

    def test_validate_table_name_valid(self):
        """Test valid table name validation."""
        assert Validator.validate_table_name('employees') is True
        assert Validator.validate_table_name('user_accounts') is True
        assert Validator.validate_table_name('data123') is True

    def test_validate_table_name_invalid(self):
        """Test invalid table name validation."""
        assert Validator.validate_table_name('table-name') is False
        assert Validator.validate_table_name('table name') is False
        assert Validator.validate_table_name('table;DROP') is False
        assert Validator.validate_table_name('') is False

    def test_validate_column_name_valid(self):
        """Test valid column name validation."""
        assert Validator.validate_column_name('first_name') is True
        assert Validator.validate_column_name('col123') is True

    def test_validate_column_name_invalid(self):
        """Test invalid column name validation."""
        assert Validator.validate_column_name('col-name') is False
        assert Validator.validate_column_name('col name') is False
        assert Validator.validate_column_name('') is False

    def test_validate_gender_value(self):
        """Test gender value validation."""
        # Valid values
        assert Validator.validate_gender_value('male') is True
        assert Validator.validate_gender_value('female') is True
        assert Validator.validate_gender_value('M') is True
        assert Validator.validate_gender_value('F') is True
        assert Validator.validate_gender_value('both') is True

        # Invalid values
        assert Validator.validate_gender_value('invalid') is False
        assert Validator.validate_gender_value('') is False

    def test_normalize_gender(self):
        """Test gender normalization."""
        assert Validator.normalize_gender('male') == 'male'
        assert Validator.normalize_gender('Male') == 'male'
        assert Validator.normalize_gender('M') == 'male'
        assert Validator.normalize_gender('m') == 'male'
        assert Validator.normalize_gender('1') == 'male'

        assert Validator.normalize_gender('female') == 'female'
        assert Validator.normalize_gender('Female') == 'female'
        assert Validator.normalize_gender('F') == 'female'
        assert Validator.normalize_gender('f') == 'female'
        assert Validator.normalize_gender('2') == 'female'

        assert Validator.normalize_gender('both') == 'both'
        assert Validator.normalize_gender('invalid') is None

    def test_validate_where_clause(self):
        """Test WHERE clause validation."""
        # Safe clauses
        assert Validator.validate_where_clause("age > 18") is True
        assert Validator.validate_where_clause("department = 'Sales'") is True
        assert Validator.validate_where_clause("created_at > '2025-01-01'") is True

        # Dangerous clauses
        assert Validator.validate_where_clause("; DROP TABLE users") is False
        assert Validator.validate_where_clause("1=1 -- comment") is False
        assert Validator.validate_where_clause("/* comment */") is False

    def test_validate_row_limit(self):
        """Test row limit validation."""
        assert Validator.validate_row_limit(100) is True
        assert Validator.validate_row_limit(10000) is True
        assert Validator.validate_row_limit(0) is False
        assert Validator.validate_row_limit(-1) is False
        assert Validator.validate_row_limit(20000) is False

    def test_validate_name_groups(self):
        """Test name groups validation."""
        valid_groups = ['English', 'Arabic', 'Asian', 'African']

        assert Validator.validate_name_groups(['English'], valid_groups) is True
        assert Validator.validate_name_groups(['English', 'Arabic'], valid_groups) is True
        assert Validator.validate_name_groups(['all'], valid_groups) is True

        assert Validator.validate_name_groups([], valid_groups) is False
        assert Validator.validate_name_groups(['Invalid'], valid_groups) is False

    def test_validate_distribution_mode(self):
        """Test distribution mode validation."""
        assert Validator.validate_distribution_mode('equal') is True
        assert Validator.validate_distribution_mode('proportional') is True
        assert Validator.validate_distribution_mode('custom') is True
        assert Validator.validate_distribution_mode('invalid') is False

    def test_sanitize_table_name(self):
        """Test table name sanitization."""
        assert Validator.sanitize_table_name('employees') == 'employees'
        assert Validator.sanitize_table_name('user-accounts') == 'useraccounts'
        assert Validator.sanitize_table_name('table; DROP') == 'tableDROP'

    def test_sanitize_column_name(self):
        """Test column name sanitization."""
        assert Validator.sanitize_column_name('first_name') == 'first_name'
        assert Validator.sanitize_column_name('col-name') == 'colname'
        assert Validator.sanitize_column_name('col; DROP') == 'colDROP'

    def test_validate_config(self):
        """Test complete configuration validation."""
        # Valid config
        valid_config = {
            'table': 'employees',
            'gender_column': 'gender',
            'name_columns': ['first_name', 'last_name'],
            'target_gender': 'female',
            'name_groups': ['English', 'Arabic'],
            'distribution': 'proportional'
        }

        errors = Validator.validate_config(valid_config)
        assert len(errors) == 0

        # Missing required field
        invalid_config = {
            'table': 'employees',
            # missing gender_column
            'name_columns': ['first_name'],
            'target_gender': 'female'
        }

        errors = Validator.validate_config(invalid_config)
        assert len(errors) > 0
        assert any('gender_column' in err for err in errors)

        # Invalid table name
        invalid_config = {
            'table': 'table; DROP',
            'gender_column': 'gender',
            'name_columns': ['first_name'],
            'target_gender': 'female'
        }

        errors = Validator.validate_config(invalid_config)
        assert len(errors) > 0
        assert any('table name' in err.lower() for err in errors)
