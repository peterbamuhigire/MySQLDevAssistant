"""
Database Manager - Handles MySQL connections and operations
"""

import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any, Optional, Tuple
import logging
from contextlib import contextmanager
import yaml
import os

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and provides safe update operations."""

    def __init__(self, host: str = None, port: int = 3306, user: str = None,
                 password: str = None, database: str = None, config_file: str = None):
        """
        Initialize database manager.

        Args:
            host: MySQL host
            port: MySQL port
            user: MySQL user
            password: MySQL password
            database: Database name
            config_file: Path to YAML config file
        """
        self.connection_params = {}

        # Load from config file if provided
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                self.connection_params = config.get('default_connection', {})

        # Override with explicit parameters
        if host:
            self.connection_params['host'] = host
        if port:
            self.connection_params['port'] = port
        if user:
            self.connection_params['user'] = user
        if password:
            self.connection_params['password'] = password
        if database:
            self.connection_params['database'] = database

        self.connection = None
        self.database = database

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = mysql.connector.connect(**self.connection_params)
            yield conn
        except Error as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn and conn.is_connected():
                conn.close()

    def test_connection(self) -> Tuple[bool, str]:
        """
        Test database connection.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()
                cursor.close()
                return True, f"Connected successfully. MySQL version: {version[0]}"
        except Error as e:
            return False, f"Connection failed: {str(e)}"

    def get_databases(self) -> List[str]:
        """Get list of all databases."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SHOW DATABASES")
                databases = [db[0] for db in cursor.fetchall()]
                cursor.close()
                return databases
        except Error as e:
            logger.error(f"Error fetching databases: {e}")
            return []

    def get_tables(self, database: str = None) -> List[str]:
        """Get list of all tables in database."""
        db = database or self.database
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SHOW TABLES FROM `{db}`")
                tables = [table[0] for table in cursor.fetchall()]
                cursor.close()
                return tables
        except Error as e:
            logger.error(f"Error fetching tables: {e}")
            return []

    def get_table_schema(self, table: str, database: str = None) -> List[Dict[str, Any]]:
        """
        Get table schema information.

        Args:
            table: Table name
            database: Database name (optional)

        Returns:
            List of column dictionaries with field info
        """
        db = database or self.database
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(f"DESCRIBE `{db}`.`{table}`")
                schema = cursor.fetchall()
                cursor.close()
                return schema
        except Error as e:
            logger.error(f"Error fetching schema for {table}: {e}")
            return []

    def detect_gender_column(self, table: str, database: str = None) -> Optional[str]:
        """
        Detect gender column in table.

        Args:
            table: Table name
            database: Database name (optional)

        Returns:
            Column name if found, None otherwise
        """
        schema = self.get_table_schema(table, database)
        gender_keywords = ['gender', 'sex', 'sexo', 'genre']

        for column in schema:
            col_name = column['Field'].lower()
            if any(keyword in col_name for keyword in gender_keywords):
                return column['Field']

        return None

    def detect_name_columns(self, table: str, database: str = None) -> List[str]:
        """
        Detect name columns in table.

        Args:
            table: Table name
            database: Database name (optional)

        Returns:
            List of column names
        """
        schema = self.get_table_schema(table, database)
        name_keywords = ['name', 'first', 'last', 'fname', 'lname', 'firstname',
                        'lastname', 'nombre', 'apellido', 'nom', 'prenom']

        name_columns = []
        for column in schema:
            col_name = column['Field'].lower()
            col_type = column['Type'].lower()

            # Check if it's a text column and contains name keywords
            if any(keyword in col_name for keyword in name_keywords):
                if any(t in col_type for t in ['varchar', 'char', 'text']):
                    name_columns.append(column['Field'])

        return name_columns

    def get_tables_with_gender_columns(self, database: str = None) -> List[Dict[str, Any]]:
        """
        Find all tables that have gender columns.

        Returns:
            List of dicts with table info
        """
        tables = self.get_tables(database)
        result = []

        for table in tables:
            gender_col = self.detect_gender_column(table, database)
            if gender_col:
                name_cols = self.detect_name_columns(table, database)
                result.append({
                    'table': table,
                    'gender_column': gender_col,
                    'name_columns': name_cols
                })

        return result

    def get_sample_data(self, table: str, limit: int = 10,
                       database: str = None) -> List[Dict[str, Any]]:
        """
        Get sample data from table.

        Args:
            table: Table name
            limit: Number of rows to fetch
            database: Database name (optional)

        Returns:
            List of row dictionaries
        """
        db = database or self.database
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(f"SELECT * FROM `{db}`.`{table}` LIMIT {limit}")
                data = cursor.fetchall()
                cursor.close()
                return data
        except Error as e:
            logger.error(f"Error fetching sample data: {e}")
            return []

    def execute_update(self, query: str, params: tuple = None,
                      database: str = None) -> int:
        """
        Execute an UPDATE query safely.

        Args:
            query: SQL query
            params: Query parameters
            database: Database name (optional)

        Returns:
            Number of affected rows
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                affected_rows = cursor.rowcount
                conn.commit()
                cursor.close()
                return affected_rows
        except Error as e:
            logger.error(f"Error executing update: {e}")
            raise

    def execute_batch_update(self, queries: List[Tuple[str, tuple]],
                           database: str = None) -> int:
        """
        Execute multiple UPDATE queries in a transaction.

        Args:
            queries: List of (query, params) tuples
            database: Database name (optional)

        Returns:
            Total number of affected rows
        """
        total_affected = 0
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                for query, params in queries:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    total_affected += cursor.rowcount

                conn.commit()
                cursor.close()
                return total_affected
        except Error as e:
            logger.error(f"Error in batch update: {e}")
            if conn:
                conn.rollback()
            raise

    def get_row_count(self, table: str, where_clause: str = None,
                     database: str = None) -> int:
        """
        Get count of rows in table.

        Args:
            table: Table name
            where_clause: Optional WHERE clause (without WHERE keyword)
            database: Database name (optional)

        Returns:
            Row count
        """
        db = database or self.database
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = f"SELECT COUNT(*) FROM `{db}`.`{table}`"
                if where_clause:
                    query += f" WHERE {where_clause}"

                cursor.execute(query)
                count = cursor.fetchone()[0]
                cursor.close()
                return count
        except Error as e:
            logger.error(f"Error getting row count: {e}")
            return 0
