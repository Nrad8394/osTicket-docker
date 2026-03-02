"""
validators/schema_validation.py - Database schema validation

Validates that osTicket database schema matches expected structure
for seeding operations.
"""

import logging
from typing import Dict, List, Any, Optional
from connection import DatabaseConnection

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validates osTicket database schema."""
    
    # Expected table structures
    EXPECTED_TABLES = {
        'ost_role': ['id', 'name', 'permissions'],
        'ost_department': ['id', 'name'],
        'ost_sla': ['id', 'name', 'grace_period'],
        'ost_team': ['id', 'name'],
        'ost_staff': ['id', 'name', 'email', 'username', 'passwd', 'role_id', 'dept_id'],
        'ost_list': ['id', 'name'],
        'ost_list_items': ['id', 'list_id', 'value', 'sort_order'],
        'ost_form_field': ['id', 'form_id', 'label', 'type', 'configuration'],
        'ost_help_topic': ['id', 'topic', 'dept_id'],
        'ost_ticket_status': ['id', 'name', 'state'],
        'ost_filter': ['id', 'name', 'rule_match', 'action_data'],
        'ost_sequence': ['id', 'name', 'pattern'],
        'ost_ticket': ['id', 'number', 'email', 'name', 'dept_id'],
    }
    
    def __init__(self, connection: DatabaseConnection):
        """Initialize validator.
        
        Args:
            connection: Database connection
        """
        self.connection = connection
    
    def validate_schema(self) -> bool:
        """Validate entire schema.
        
        Returns:
            True if schema is valid, False otherwise
        """
        logger.info("Validating osTicket database schema...")
        
        all_valid = True
        for table_name, expected_columns in self.EXPECTED_TABLES.items():
            if not self._validate_table(table_name, expected_columns):
                all_valid = False
        
        if all_valid:
            logger.info("✓ Schema validation passed")
        else:
            logger.error("✗ Schema validation failed")
        
        return all_valid
    
    def _validate_table(self, table_name: str, expected_columns: List[str]) -> bool:
        """Validate single table exists with expected columns.
        
        Args:
            table_name: Table name
            expected_columns: Expected column names
        
        Returns:
            True if table is valid, False otherwise
        """
        try:
            # Get actual columns
            query = f"SHOW COLUMNS FROM {table_name}"
            rows = self.connection.fetch_all(query)
            
            if not rows:
                logger.warning(f"  ✗ Table {table_name} does not exist")
                return False
            
            actual_columns = {row[0] for row in rows}
            
            # Check if expected columns exist
            missing = set(expected_columns) - actual_columns
            if missing:
                logger.warning(f"  ✗ Table {table_name} missing columns: {', '.join(missing)}")
                return False
            
            logger.info(f"  ✓ Table {table_name} is valid")
            return True
        
        except Exception as e:
            logger.error(f"  ✗ Error validating {table_name}: {str(e)}")
            return False
    
    def check_table_contents(self, table_name: str) -> int:
        """Get row count for table.
        
        Args:
            table_name: Table name
        
        Returns:
            Number of rows in table
        """
        try:
            query = f"SELECT COUNT(*) FROM {table_name}"
            result = self.connection.fetch_one(query)
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error checking {table_name} contents: {str(e)}")
            return -1
    
    def get_pre_seeding_state(self) -> Dict[str, int]:
        """Get state of all tables before seeding.
        
        Returns:
            Dict of table names and row counts
        """
        state = {}
        for table_name in self.EXPECTED_TABLES.keys():
            state[table_name] = self.check_table_contents(table_name)
        return state
    
    def validate_foreign_keys(self) -> bool:
        """Validate foreign key relationships exist.
        
        Returns:
            True if all FKs are valid, False otherwise
        """
        logger.info("Validating foreign key relationships...")
        
        # Expected FK relationships
        fk_checks = [
            ('ost_staff', 'role_id', 'ost_role', 'id'),
            ('ost_staff', 'dept_id', 'ost_department', 'id'),
            ('ost_list_items', 'list_id', 'ost_list', 'id'),
            ('ost_form_field', 'form_id', 'ost_form', 'id'),
            ('ost_help_topic', 'dept_id', 'ost_department', 'id'),
            ('ost_ticket', 'dept_id', 'ost_department', 'id'),
        ]
        
        all_valid = True
        for table, column, ref_table, ref_column in fk_checks:
            if not self._check_fk_constraint(table, column, ref_table, ref_column):
                all_valid = False
        
        return all_valid
    
    def _check_fk_constraint(self, table: str, column: str,
                           ref_table: str, ref_column: str) -> bool:
        """Check if FK constraint exists.
        
        Args:
            table: Table name
            column: Column name
            ref_table: Referenced table
            ref_column: Referenced column
        
        Returns:
            True if FK exists, False otherwise
        """
        try:
            query = """
                SELECT CONSTRAINT_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_NAME = %s AND COLUMN_NAME = %s
                AND REFERENCED_TABLE_NAME = %s AND REFERENCED_COLUMN_NAME = %s
            """
            result = self.connection.fetch_one(query, (table, column, ref_table, ref_column))
            
            if result:
                logger.info(f"  ✓ FK: {table}.{column} → {ref_table}.{ref_column}")
                return True
            else:
                logger.warning(f"  ✗ FK missing: {table}.{column} → {ref_table}.{ref_column}")
                return False
        
        except Exception as e:
            logger.error(f"Error checking FK: {str(e)}")
            return False
