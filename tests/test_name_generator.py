"""
Tests for Name Generator module
"""

import pytest
from pathlib import Path
from src.tools.name_generator import NameRandomizer


class TestNameRandomizer:
    """Test cases for NameRandomizer class."""

    @pytest.fixture
    def randomizer(self):
        """Create NameRandomizer instance for testing."""
        # Use test database credentials
        return NameRandomizer(
            host='localhost',
            user='root',
            password='test',
            database='test_db'
        )

    def test_load_names(self, randomizer):
        """Test name loading from CSV files."""
        assert randomizer.female_names is not None
        assert randomizer.male_names is not None
        assert len(randomizer.female_names) > 0
        assert len(randomizer.male_names) > 0

    def test_get_available_groups(self, randomizer):
        """Test getting available name groups."""
        female_groups = randomizer.get_available_groups('female')
        male_groups = randomizer.get_available_groups('male')
        all_groups = randomizer.get_available_groups('both')

        assert len(female_groups) > 0
        assert len(male_groups) > 0
        assert len(all_groups) >= len(female_groups)

    def test_get_random_name_female(self, randomizer):
        """Test getting random female name."""
        name = randomizer.get_random_name('female', groups=['English'])
        assert isinstance(name, str)
        assert len(name) > 0

    def test_get_random_name_male(self, randomizer):
        """Test getting random male name."""
        name = randomizer.get_random_name('male', groups=['English'])
        assert isinstance(name, str)
        assert len(name) > 0

    def test_get_random_name_all_groups(self, randomizer):
        """Test getting random name from all groups."""
        name = randomizer.get_random_name('female', groups=['all'])
        assert isinstance(name, str)
        assert len(name) > 0

    def test_get_random_name_multiple_groups(self, randomizer):
        """Test getting random name from multiple groups."""
        name = randomizer.get_random_name(
            'female',
            groups=['English', 'Arabic'],
            distribution='equal'
        )
        assert isinstance(name, str)
        assert len(name) > 0

    def test_get_random_name_proportional(self, randomizer):
        """Test proportional distribution."""
        name = randomizer.get_random_name(
            'male',
            groups=['English', 'Arabic'],
            distribution='proportional'
        )
        assert isinstance(name, str)
        assert len(name) > 0

    # Integration tests would require actual database connection
    # These should be run separately with test database setup

    @pytest.mark.integration
    def test_preview_changes(self, randomizer):
        """Test preview changes generation."""
        # This requires actual database connection
        pytest.skip("Integration test - requires database")

    @pytest.mark.integration
    def test_execute_update_dry_run(self, randomizer):
        """Test execute update in dry run mode."""
        # This requires actual database connection
        pytest.skip("Integration test - requires database")
