"""
connection.py - Database connection pooling and management

Provides MySQL connection pooling with support for transactions,
prepared statements, and connection health checks.
"""

import logging
import mysql.connector
from mysql.connector import Error, pooling
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages MySQL connections with pooling."""
    
    _pool: Optional[pooling.MySQLConnectionPool] = None
    
    @classmethod
    def initialize_pool(cls, config: Dict[str, Any]) -> None:
        """Initialize connection pool.
        
        Args:
            config: Database configuration dict with keys:
                - host: MySQL host
                - user: MySQL user
                - password: MySQL password
                - database: Database name
                - pool_size: Connection pool size (default: 5)
                - pool_name: Pool name (default: 'osticket_pool')
        """
        if cls._pool is not None:
            logger.warning("Connection pool already initialized")
            return
        
        try:
            cls._pool = pooling.MySQLConnectionPool(
                pool_name=config.get('pool_name', 'osticket_pool'),
                pool_size=config.get('pool_size', 5),
                pool_reset_session=True,
                host=config['host'],
                user=config['user'],
                password=config['password'],
                database=config['database'],
                autocommit=False,
                charset='utf8mb4'
            )
            logger.info("Database connection pool initialized successfully")
        except Error as e:
            logger.error(f"Failed to initialize connection pool: {str(e)}")
            raise
    
    @classmethod
    def get_connection(cls) -> 'DatabaseConnection':
        """Get a connection instance from pool.
        
        Returns:
            DatabaseConnection instance
        """
        if cls._pool is None:
            raise RuntimeError("Connection pool not initialized. Call initialize_pool() first.")
        
        try:
            conn = cls._pool.get_connection()
            return DatabaseConnection(conn)
        except Error as e:
            logger.error(f"Failed to get connection from pool: {str(e)}")
            raise
    
    def __init__(self, connection):
        """Initialize with raw connection.
        
        Args:
            connection: MySQL connection object from pool
        """
        self.connection = connection
        self._transaction_started = False
    
    def execute(self, query: str, params: tuple = None) -> int:
        """Execute a query (INSERT, UPDATE, DELETE).
        
        Args:
            query: SQL query with %s placeholders
            params: Query parameters
        
        Returns:
            Number of affected rows
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            affected_rows = cursor.rowcount
            logger.debug(f"Query executed: {affected_rows} rows affected")
            return affected_rows
        except Error as e:
            logger.error(f"Query execution failed: {str(e)}")
            logger.error(f"Query: {query}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[tuple]:
        """Fetch single row.
        
        Args:
            query: SQL query with %s placeholders
            params: Query parameters
        
        Returns:
            Single row or None
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            return cursor.fetchone()
        except Error as e:
            logger.error(f"Fetch one failed: {str(e)}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def fetch_all(self, query: str, params: tuple = None) -> list:
        """Fetch all rows.
        
        Args:
            query: SQL query with %s placeholders
            params: Query parameters
        
        Returns:
            List of rows
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Fetch all failed: {str(e)}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def begin_transaction(self) -> None:
        """Begin transaction."""
        if not self._transaction_started:
            self.connection.start_transaction()
            self._transaction_started = True
            logger.debug("Transaction started")
    
    def commit(self) -> None:
        """Commit transaction."""
        if self._transaction_started:
            self.connection.commit()
            self._transaction_started = False
            logger.debug("Transaction committed")
    
    def rollback(self) -> None:
        """Rollback transaction."""
        if self._transaction_started:
            self.connection.rollback()
            self._transaction_started = False
            logger.debug("Transaction rolled back")
    
    def close(self) -> None:
        """Return connection to pool."""
        try:
            if self._transaction_started:
                self.rollback()
            if self.connection.is_connected():
                self.connection.close()
        except Error as e:
            logger.warning(f"Error closing connection: {str(e)}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()


class ConnectionContext:
    """Context manager for database transactions."""
    
    def __init__(self):
        """Initialize context."""
        self.connection = None
    
    def __enter__(self):
        """Get connection and start transaction."""
        self.connection = DatabaseConnection.get_connection()
        self.connection.begin_transaction()
        return self.connection
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Handle cleanup."""
        if exc_type is not None:
            logger.error(f"Exception in transaction: {exc_type.__name__}: {exc_val}")
            if self.connection:
                self.connection.rollback()
            return False
        else:
            if self.connection:
                self.connection.commit()
            return True
        
        if self.connection:
            self.connection.close()
