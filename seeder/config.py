#!/usr/bin/env python3
"""
KRA osTicket Seeder Configuration Management
Handles environment detection, config loading, and validation
"""

import os
import json
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any


class Environment(Enum):
    """Supported deployment environments"""
    LOCAL = "local"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    AZURE = "azure"


class SeederMode(Enum):
    """Seeding operation modes"""
    FULL = "full"           # INSERT/UPDATE all records (non-destructive)
    PARTIAL = "partial"     # INSERT IGNORE (safe, skips duplicates)
    RESET = "reset"         # Reserved for future use
    VALIDATE = "validate"   # Check only, don't modify
    ROLLBACK = "rollback"   # Restore from backup


@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str
    port: int
    user: str
    password: str
    database: str
    prefix: str = "ost_"
    
    def connection_string(self) -> str:
        """Return DSN for debugging"""
        return f"mysql://{self.user}:***@{self.host}:{self.port}/{self.database}"


@dataclass
class SeedingConfig:
    """Complete seeding configuration"""
    db_config: DatabaseConfig
    env: Environment
    mode: SeederMode
    dry_run: bool = False
    backup: bool = False
    verbose: bool = False
    backup_dir: Optional[str] = None
    log_file: Optional[str] = None
    
    @property
    def table_prefix(self) -> str:
        return self.db_config.prefix


class EnvironmentDetector:
    """Detect the deployment environment"""
    
    @staticmethod
    def detect() -> Environment:
        """Auto-detect current environment"""
        if os.environ.get('DOCKER_HOST') or os.path.exists('/.dockerenv'):
            return Environment.DOCKER
        elif os.environ.get('KUBERNETES_SERVICE_HOST'):
            return Environment.KUBERNETES
        elif os.environ.get('AZURE_SUBSCRIPTION_ID') or os.environ.get('AZURE_TENANT_ID'):
            return Environment.AZURE
        else:
            return Environment.LOCAL


class ConfigLoader:
    """Load configuration from environment or .env file"""
    
    @staticmethod
    def load_env_file(path: str = ".env") -> Dict[str, str]:
        """Load environment variables from .env file
        
        Attempts to load from:
        1. Specified path (e.g., 'seeder/.env')
        2. Parent directory fallback (e.g., '../.env') for centralized config
        3. Returns empty dict if neither exists
        """
        env_vars = {}
        
        # Try primary path first
        paths_to_try = [path]
        
        # Add parent directory fallback for centralized .env
        if path == ".env":
            parent_env = os.path.join('..', '.env')
            paths_to_try.append(parent_env)
        
        for env_path in paths_to_try:
            if os.path.exists(env_path):
                with open(env_path, encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip().strip('"').strip("'")
                # Successfully loaded, don't try other paths
                print(f"✓ Loaded configuration from: {env_path}")
                break
        
        return env_vars
    
    @staticmethod
    def get_db_config(env: Environment, env_vars: Optional[Dict] = None) -> DatabaseConfig:
        """Get database config for the current environment"""
        if env_vars is None:
            env_vars = ConfigLoader.load_env_file()
        
        if env == Environment.DOCKER:
            return DatabaseConfig(
                host=env_vars.get('MYSQL_HOST', os.environ.get('MYSQL_HOST', 'mysql')),
                port=int(env_vars.get('MYSQL_PORT', os.environ.get('MYSQL_PORT', 3306))),
                user=env_vars.get('MYSQL_USER', os.environ.get('MYSQL_USER', 'osticket')),
                password=env_vars.get('MYSQL_PASSWORD', os.environ.get('MYSQL_PASSWORD', '')),
                database=env_vars.get('MYSQL_DATABASE', os.environ.get('MYSQL_DATABASE', 'osticket')),
                prefix=env_vars.get('MYSQL_PREFIX', os.environ.get('MYSQL_PREFIX', 'ost_')),
            )
        
        elif env == Environment.KUBERNETES:
            # Read from K8s Secrets mounted as files
            return DatabaseConfig(
                host=ConfigLoader._read_k8s_secret('db-host'),
                port=int(ConfigLoader._read_k8s_secret('db-port', '3306')),
                user=ConfigLoader._read_k8s_secret('db-user'),
                password=ConfigLoader._read_k8s_secret('db-password'),
                database=ConfigLoader._read_k8s_secret('db-name', 'osticket'),
                prefix=ConfigLoader._read_k8s_secret('db-prefix', 'ost_'),
            )
        
        elif env == Environment.AZURE:
            # Read from environment variables (set by Azure)
            return DatabaseConfig(
                host=os.environ.get('DB_HOST', ''),
                port=int(os.environ.get('DB_PORT', 3306)),
                user=os.environ.get('DB_USER', ''),
                password=os.environ.get('DB_PASSWORD', ''),
                database=os.environ.get('DB_NAME', 'osticket'),
                prefix=os.environ.get('DB_PREFIX', 'ost_'),
            )
        
        else:  # LOCAL
            return DatabaseConfig(
                host=env_vars.get('DB_HOST', os.environ.get('DB_HOST', 'localhost')),
                port=int(env_vars.get('DB_PORT', os.environ.get('DB_PORT', 3306))),
                user=env_vars.get('DB_USER', os.environ.get('DB_USER', 'osticket')),
                password=env_vars.get('DB_PASS', os.environ.get('DB_PASS', '0sT1ck3tPass!')),
                database=env_vars.get('DB_NAME', os.environ.get('DB_NAME', 'osticket')),
                prefix=env_vars.get('DB_PREFIX', os.environ.get('DB_PREFIX', 'ost_')),
            )
    
    @staticmethod
    def _read_k8s_secret(name: str, default: str = '') -> str:
        """Read Kubernetes secret from mounted volume"""
        secret_path = f'/var/run/secrets/kubernetes.io/serviceaccount/{name}'
        if os.path.exists(secret_path):
            with open(secret_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return default


class Config:
    """Unified configuration management"""
    
    def __init__(self,
                 env: Optional[str] = None,
                 mode: str = "partial",
                 dry_run: bool = False,
                 backup: bool = False,
                 verbose: bool = False,
                 env_file: str = ".env"):
        
        # Determine environment
        if env is None:
            self._env = EnvironmentDetector.detect()
        else:
            self._env = Environment(env)
        
        # Load environment variables
        self._env_vars = ConfigLoader.load_env_file(env_file)
        
        # Get database config
        self._db_config = ConfigLoader.get_db_config(self._env, self._env_vars)
        
        # Parse mode
        try:
            self._mode = SeederMode(mode)
        except ValueError:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {[m.value for m in SeederMode]}")
        
        # Store other settings
        self._dry_run = dry_run
        self._backup = backup
        self._verbose = verbose
        self._backup_dir = self._env_vars.get('BACKUP_DIR', './backups')
        self._log_file = self._env_vars.get('LOG_FILE', f'seeding_{os.getpid()}.log')
    
    @property
    def env(self) -> Environment:
        return self._env
    
    @property
    def mode(self) -> SeederMode:
        return self._mode
    
    @property
    def db_config(self) -> DatabaseConfig:
        return self._db_config
    
    @property
    def dry_run(self) -> bool:
        return self._dry_run
    
    @property
    def backup(self) -> bool:
        return self._backup
    
    @property
    def verbose(self) -> bool:
        return self._verbose
    
    @property
    def backup_dir(self) -> str:
        return self._backup_dir
    
    @property
    def log_file(self) -> str:
        return self._log_file
    
    def summary(self) -> Dict[str, Any]:
        """Return configuration summary"""
        return {
            'environment': self._env.value,
            'mode': self._mode.value,
            'database': self._db_config.connection_string(),
            'table_prefix': self._db_config.prefix,
            'dry_run': self._dry_run,
            'backup': self._backup,
            'verbose': self._verbose,
        }
    
    def __str__(self) -> str:
        return json.dumps(self.summary(), indent=2)


if __name__ == '__main__':
    # Test configuration loading
    config = Config(verbose=True)
    print("Configuration loaded successfully:")
    print(config)
