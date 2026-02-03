"""
Location Randomizer Tool - Randomizes latitude/longitude using AI-interpreted location descriptions
"""

import random
import re
import json
from typing import List, Dict, Any, Tuple, Optional
import logging
import os

try:
    import requests
except ImportError:
    requests = None

from ..core.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class LocationRandomizer:
    """Manages location randomization for database tables using AI-interpreted descriptions."""

    def __init__(self, host: str = None, port: int = 3306, user: str = None,
                 password: str = None, database: str = None, config_file: str = None):
        """
        Initialize Location Randomizer.

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

    def get_numeric_columns(self, table: str, database: str = None) -> List[Dict[str, str]]:
        """
        Get all numeric columns from a table (suitable for lat/long).

        Args:
            table: Table name
            database: Database name

        Returns:
            List of dictionaries with column info
        """
        numeric_types = ['decimal', 'float', 'double', 'numeric']
        schema = self.db_manager.get_table_schema(table, database)

        numeric_cols = []
        for col in schema:
            col_type = col['Type'].lower()
            if any(num_type in col_type for num_type in numeric_types):
                numeric_cols.append({
                    'name': col['Field'],
                    'type': col['Type'],
                    'nullable': col['Null'] == 'YES'
                })

        return numeric_cols

    def interpret_location_description(self, description: str, api_key: str) -> Dict[str, float]:
        """
        Use DeepSeek AI to interpret location description and get coordinate bounds.

        Args:
            description: Natural language description of location
            api_key: DeepSeek API key

        Returns:
            Dictionary with min_lat, max_lat, min_lng, max_lng
        """
        if requests is None:
            raise ImportError(
                "The 'requests' library is required for Location Randomizer. "
                "Please install it with: pip install requests"
            )

        try:
            if not api_key or not api_key.strip():
                raise ValueError("DeepSeek API key is required")

            # DeepSeek API endpoint
            url = "https://api.deepseek.com/v1/chat/completions"

            prompt = f"""You are a geographic coordinate expert. Given a location description, provide the approximate coordinate bounds.

Location description: "{description}"

Please provide ONLY a JSON object with the coordinate bounds in this exact format (no other text):
{{
  "min_lat": <minimum latitude>,
  "max_lat": <maximum latitude>,
  "min_lng": <minimum longitude>,
  "max_lng": <maximum longitude>,
  "description": "<brief description of the area>"
}}

Example for "Northern Uganda near urban centers":
{{
  "min_lat": 2.5,
  "max_lat": 3.8,
  "min_lng": 31.5,
  "max_lng": 33.5,
  "description": "Northern Uganda region including Gulu, Lira, and surrounding urban areas"
}}

Provide accurate coordinates based on real geography. Return ONLY the JSON object."""

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.3
            }

            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            response_data = response.json()
            response_text = response_data['choices'][0]['message']['content'].strip()

            # Try to find JSON in the response
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)

            result = json.loads(response_text)

            # Validate the result
            required_keys = ['min_lat', 'max_lat', 'min_lng', 'max_lng']
            if not all(key in result for key in required_keys):
                raise ValueError(f"AI response missing required keys: {required_keys}")

            # Validate coordinate ranges
            if not (-90 <= result['min_lat'] <= 90 and -90 <= result['max_lat'] <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= result['min_lng'] <= 180 and -180 <= result['max_lng'] <= 180):
                raise ValueError("Longitude must be between -180 and 180")
            if result['min_lat'] >= result['max_lat']:
                raise ValueError("min_lat must be less than max_lat")
            if result['min_lng'] >= result['max_lng']:
                raise ValueError("min_lng must be less than max_lng")

            # Log the AI's interpretation
            ai_description = result.get('description', 'N/A')
            logger.info(f"AI interpreted location: {ai_description}")
            logger.info(f"Coordinates: Lat {result['min_lat']} to {result['max_lat']}, "
                       f"Lng {result['min_lng']} to {result['max_lng']}")

            # Add interpretation info to result for UI display
            result['ai_interpretation'] = ai_description

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API request failed: {e}")
            raise ValueError(f"Failed to connect to DeepSeek API: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            raise ValueError(f"AI returned invalid response format: {str(e)}")
        except Exception as e:
            logger.error(f"Error interpreting location description: {e}")
            raise ValueError(f"Failed to interpret location: {str(e)}")

    def generate_random_coordinate(self, min_val: float, max_val: float,
                                   precision: int = 6) -> float:
        """
        Generate a random coordinate within bounds.

        Args:
            min_val: Minimum value
            max_val: Maximum value
            precision: Decimal precision (default 6 for ~10cm accuracy)

        Returns:
            Random coordinate value
        """
        random_val = random.uniform(min_val, max_val)
        return round(random_val, precision)

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
        lat_column = config['lat_column']
        lng_column = config['lng_column']
        location_description = config['location_description']
        api_key = config['api_key']
        where_clause = config.get('where_clause', None)

        # Interpret location description
        bounds = self.interpret_location_description(location_description, api_key)

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

                    old_lat = row.get(lat_column)
                    old_lng = row.get(lng_column)

                    new_lat = self.generate_random_coordinate(bounds['min_lat'], bounds['max_lat'])
                    new_lng = self.generate_random_coordinate(bounds['min_lng'], bounds['max_lng'])

                    preview_row['updated'][lat_column] = new_lat
                    preview_row['updated'][lng_column] = new_lng

                    preview_row['changes'].append({
                        'column': lat_column,
                        'old': old_lat,
                        'new': new_lat
                    })
                    preview_row['changes'].append({
                        'column': lng_column,
                        'old': old_lng,
                        'new': new_lng
                    })

                    sample_data.append(preview_row)

                cursor.close()

        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            raise

        return sample_data

    def execute_update(self, config: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute location randomization update.

        Args:
            config: Configuration dictionary
            dry_run: If True, don't actually update database

        Returns:
            Results dictionary with statistics
        """
        table = config['table']
        lat_column = config['lat_column']
        lng_column = config['lng_column']
        location_description = config['location_description']
        api_key = config['api_key']
        where_clause = config.get('where_clause', None)
        batch_size = config.get('batch_size', 1000)
        preserve_null = config.get('preserve_null', False)

        # Interpret location description
        bounds = self.interpret_location_description(location_description, api_key)

        results = {
            'total_rows': 0,
            'updated_rows': 0,
            'skipped_rows': 0,
            'errors': [],
            'dry_run': dry_run,
            'bounds': bounds
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
                                    results['skipped_rows'] += 1
                                    continue

                            # Check if should preserve NULL
                            if preserve_null and (row.get(lat_column) is None or row.get(lng_column) is None):
                                results['skipped_rows'] += 1
                                continue

                            # Generate random coordinates
                            new_lat = self.generate_random_coordinate(bounds['min_lat'], bounds['max_lat'])
                            new_lng = self.generate_random_coordinate(bounds['min_lng'], bounds['max_lng'])

                            # Execute update
                            if not dry_run:
                                update_query = f"""
                                    UPDATE `{table}`
                                    SET `{lat_column}` = %s, `{lng_column}` = %s
                                    WHERE `{pk_col}` = %s
                                """
                                cursor.execute(update_query, (new_lat, new_lng, pk_value))

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
