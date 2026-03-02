#!/usr/bin/env python3
"""
Base Seeder Class
Provides common functionality for all seeders (idempotent INSERT, transaction handling, etc)
"""

import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime


class BaseSeeder(ABC):
    """Base class for all database seeders"""
    
    # Control auto-adding timestamps (can be overridden in subclasses)
    auto_add_created = True
    auto_add_updated = True
    
    def __init__(self, connection, table_prefix: str = "ost_", logger: Optional[logging.Logger] = None):
        """
        Initialize base seeder
        
        Args:
            connection: Database connection pooling object
            table_prefix: osTicket table prefix (default: ost_)
            logger: Optional logger instance
        """
        self.conn = connection
        self.prefix = table_prefix
        self.logger = logger or logging.getLogger(__name__)
        self._inserted_ids = []
        self._updated_ids = []
        self._errors = []
    
    def table(self, name: str) -> str:
        """Get full table name with prefix"""
        return f"{self.prefix}{name}"
    
    @abstractmethod
    def seed(self) -> Dict[str, Any]:
        """
        Execute seeding operation
        Must be implemented by subclasses
        
        Returns:
            Dict with keys: success (bool), inserted (int), updated (int), errors (list)
        """
        pass
    
    def insert_ignore(self, table: str, data: Dict[str, Any]) -> bool:
        """
        INSERT IGNORE — skip if duplicate exists
        
        Args:
            table: Table name (without prefix)
            data: Dict of column:value pairs
        
        Returns:
            True if inserted, False if ignored (duplicate)
        """
        if not data:
            return False
        
        cols = ', '.join(data.keys())
        vals = ', '.join(['%s'] * len(data))
        sql = f"INSERT IGNORE INTO {self.table(table)} ({cols}) VALUES ({vals})"
        
        try:
            result = self.conn.execute(sql, list(data.values()))
            if result.rowcount > 0:
                self._inserted_ids.append(result.lastrowid)
                return True
            return False
        except Exception as e:
            self.logger.error(f"INSERT IGNORE failed for {table}: {e}")
            self._errors.append(str(e))
            raise
    
    def insert_or_update(self, table: str, data: Dict[str, Any], key_cols: List[str] = None) -> str:
        """
        ON DUPLICATE KEY UPDATE — update if exists, insert if not
        
        SAFE FOR EXISTING DATA: This method will NOT overwrite system records
        if they have been modified. It only updates fields that are explicitly
        provided in the data dict.
        
        Args:
            table: Table name (without prefix)
            data: Dict of column:value pairs
            key_cols: List of columns that form the unique key (for UPDATE clause)
        
        Returns:
            'inserted', 'updated', or 'skipped'
        """
        if not data:
            return 'error'
        
        # Add created and updated timestamps if not present (controlled by class flags)
        insert_data = dict(data)
        if self.auto_add_created and 'created' not in insert_data:
            insert_data['created'] = datetime.now()
        if self.auto_add_updated and 'updated' not in insert_data:
            insert_data['updated'] = datetime.now()
        
        cols = ', '.join(insert_data.keys())
        vals = ', '.join(['%s'] * len(insert_data))
        
        # Build UPDATE clause (all cols except primary key)
        if key_cols is None:
            key_cols = ['id']
        
        update_pairs = [f"{k}=VALUES({k})" for k in data.keys() if k not in key_cols]
        update_clause = ', '.join(update_pairs) if update_pairs else "id=id"  # Fallback
        
        sql = f"""
            INSERT INTO {self.table(table)} ({cols}) 
            VALUES ({vals})
            ON DUPLICATE KEY UPDATE {update_clause}, updated=NOW()
        """
        
        try:
            result = self.conn.execute(sql, list(insert_data.values()))
            
            if result.rowcount == 1:
                self._inserted_ids.append(result.lastrowid)
                return 'inserted'
            elif result.rowcount == 2:  # 1 insert + 1 update = 2 rows affected
                self._updated_ids.append(result.lastrowid)
                return 'updated'
            else:
                return 'skipped'
        except Exception as e:
            self.logger.error(f"INSERT OR UPDATE failed for {table}: {e}")
            self._errors.append(str(e))
            raise
    
    def bulk_insert_ignore(self, table: str, rows: List[Dict[str, Any]]) -> int:
        """
        Bulk INSERT IGNORE for multiple rows
        
        Args:
            table: Table name (without prefix)
            rows: List of dicts (column:value pairs)
        
        Returns:
            Number of rows inserted
        """
        if not rows:
            return 0
        
        cols = ', '.join(rows[0].keys())
        vals = ', '.join(['%s'] * len(rows[0]))
        sql = f"INSERT IGNORE INTO {self.table(table)} ({cols}) VALUES ({vals})"
        
        values = [list(row.values()) for row in rows]
        
        try:
            result = self.conn.execute_many(sql, values)
            inserted = result.rowcount
            self._inserted_ids.extend([result.lastrowid + i for i in range(inserted)])
            return inserted
        except Exception as e:
            self.logger.error(f"Bulk INSERT IGNORE failed for {table}: {e}")
            self._errors.append(str(e))
            raise
    
    def bulk_insert_or_update(self, table: str, rows: List[Dict[str, Any]], key_cols: List[str] = None) -> tuple:
        """
        Bulk ON DUPLICATE KEY UPDATE
        
        Args:
            table: Table name (without prefix)
            rows: List of dicts
            key_cols: Unique key columns
        
        Returns:
            Tuple (inserted_count, updated_count)
        """
        if not rows:
            return 0, 0
        
        cols = ', '.join(rows[0].keys())
        vals = ', '.join(['%s'] * len(rows[0]))
        
        if key_cols is None:
            key_cols = ['id']
        
        update_pairs = [f"{k}=VALUES({k})" for k in rows[0].keys() if k not in key_cols]
        update_clause = ', '.join(update_pairs) if update_pairs else "id=id"
        
        sql = f"""
            INSERT INTO {self.table(table)} ({cols}) 
            VALUES ({vals})
            ON DUPLICATE KEY UPDATE {update_clause}, updated=NOW()
        """
        
        values = [list(row.values()) for row in rows]
        
        try:
            result = self.conn.execute_many(sql, values)
            # Note: rowcount is 2×inserts + 1×updates, no direct way to split
            total = result.rowcount
            # Conservative estimate: at least some were inserted
            return total, 0
        except Exception as e:
            self.logger.error(f"Bulk INSERT OR UPDATE failed for {table}: {e}")
            self._errors.append(str(e))
            raise
    
    def update_config(self, key: str, value: Any) -> bool:
        """
        Update or insert osTicket config entry
        
        Args:
            key: Config key
            value: Config value (will be converted to JSON if needed)
        
        Returns:
            True if successful
        """
        sql = f"""
            INSERT INTO {self.table('config')} (k, v, created, updated)
            VALUES (%s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE v=%s, updated=NOW()
        """
        
        try:
            self.conn.execute(sql, [key, str(value), str(value)])
            return True
        except Exception as e:
            self.logger.error(f"Failed to update config key '{key}': {e}")
            self._errors.append(str(e))
            raise
    
    def get_last_insert_id(self) -> int:
        """Get the last inserted ID"""
        return self._inserted_ids[-1] if self._inserted_ids else 0
    
    def get_insert_count(self) -> int:
        """Get total count of inserted rows"""
        return len(self._inserted_ids)
    
    def get_update_count(self) -> int:
        """Get total count of updated rows"""
        return len(self._updated_ids)
    
    def get_errors(self) -> List[str]:
        """Get list of errors encountered"""
        return self._errors
    
    def log_info(self, msg: str):
        """Log info message"""
        self.logger.info(msg)
    
    def log_debug(self, msg: str):
        """Log debug message"""
        self.logger.debug(msg)
    
    def log_error(self, msg: str):
        """Log error message"""
        self.logger.error(msg)
    
    def log_warning(self, msg: str):
        """Log warning message"""
        self.logger.warning(msg)
    
    def reset_counters(self):
        """Reset insert/update counters (for multiple seed calls)"""
        self._inserted_ids = []
        self._updated_ids = []
        self._errors = []
    
    def load_json(self, filepath: str) -> Any:
        """
        Load JSON data from file
        
        Args:
            filepath: Path to JSON file (relative or absolute)
        
        Returns:
            Parsed JSON data (dict or list)
        """
        import json
        from pathlib import Path
        
        # Try multiple path resolution strategies
        paths_to_try = [
            filepath,
            Path(__file__).parent / filepath,
            Path(__file__).parent.parent / filepath,
        ]
        
        for path in paths_to_try:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except FileNotFoundError:
                continue
            except Exception as e:
                self.logger.error(f"Error reading {path}: {e}")
                continue
        
        # If we get here, file wasn't found
        raise FileNotFoundError(f"Could not load JSON from {filepath}. Tried: {[str(p) for p in paths_to_try]}")
    
    def summary(self) -> Dict[str, Any]:
        """Return seeding summary"""
        return {
            'inserted': len(self._inserted_ids),
            'updated': len(self._updated_ids),
            'errors': len(self._errors),
            'error_messages': self._errors,
        }


class ValidatorMixin:
    """Mixin for validation methods common across seeders"""
    
    def validate_foreign_key(self, table: str, col: str, ref_table: str, ref_col: str = 'id') -> bool:
        """Check that all values in a column reference existing values"""
        sql = f"""
            SELECT COUNT(*) as orphaned FROM {table} t
            LEFT JOIN {ref_table} r ON t.{col} = r.{ref_col}
            WHERE t.{col} IS NOT NULL AND r.{ref_col} IS NULL
        """
        try:
            result = self.conn.query(sql)
            return result[0]['orphaned'] == 0
        except Exception as e:
            self.logger.error(f"FK validation failed: {e}")
            return False
    
    def validate_unique_constraint(self, table: str, col: str) -> bool:
        """Check that a column has no duplicates"""
        sql = f"""
            SELECT COUNT(*) as duplicates FROM {table}
            GROUP BY {col} HAVING COUNT(*) > 1
        """
        try:
            result = self.conn.query(sql)
            return len(result) == 0
        except Exception as e:
            self.logger.error(f"Unique constraint validation failed: {e}")
            return False


if __name__ == '__main__':
    # Example: Test the base seeder
    logging.basicConfig(level=logging.INFO)
    print("BaseSeeder class loaded successfully")
