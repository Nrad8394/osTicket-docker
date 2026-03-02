#!/usr/bin/env python3
"""
main.py - Master orchestration script for seeding osTicket database
Phase 2C: Seeding Orchestration

Executes all seeders in strict dependency order with transaction management,
error handling, and comprehensive reporting.

Seeding Order (Non-Negotiable):
1. Roles (no deps)
2. Departments (no deps)
3. SLAs (no deps)
4. Teams (no deps)
5. Staff (depends: roles, departments)
6. Lists (no deps)
7. List Items (depends: lists)
8. Form Fields (depends: lists)
9. Help Topics (depends: departments, teams, slas) [Phase 1]
10. Ticket Statuses (no deps)
11. Filters (depends: help_topics)
12. Sequences (no deps)
13. Demo Tickets (optional, depends: all above)
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add seeder package to path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from config import Config
from connection import DatabaseConnection
from seeders import (
    RoleSeeder,
    DepartmentSeeder,
    SLASeeder,
    TeamSeeder,
    ListSeeder,
    ListItemSeeder,
    StaffSeeder,
    FormFieldSeeder,
    StatusSeeder,
    HelpTopicSeeder,
    FilterSeeder,
    SequenceSeeder,
    DemoTicketSeeder
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(SCRIPT_DIR / 'logs' / 'main.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SeedingOrchestrator:
    """
    Orchestrates the execution of all seeders in dependency order.
    
    Manages:
    - Transaction boundaries
    - Error handling and rollback
    - Progress tracking
    - Summary reporting
    """
    
    def __init__(self, config: Config, demo_mode: bool = False):
        """Initialize orchestrator.
        
        Args:
            config: Configuration object for database connection
            demo_mode: If True, includes demo_tickets seeder
        """
        self.config = config
        self.demo_mode = demo_mode
        self.results: Dict[str, Any] = {}
        self.start_time = None
        self.end_time = None
        
        # Define seeding order with dependencies documented
        self.seeding_steps = [
            {
                'name': 'Roles',
                'seeder': RoleSeeder,
                'depends_on': [],
                'critical': True
            },
            {
                'name': 'Departments',
                'seeder': DepartmentSeeder,
                'depends_on': [],
                'critical': True
            },
            {
                'name': 'SLAs',
                'seeder': SLASeeder,
                'depends_on': [],
                'critical': True
            },
            {
                'name': 'Teams',
                'seeder': TeamSeeder,
                'depends_on': [],
                'critical': True
            },
            {
                'name': 'Staff',
                'seeder': StaffSeeder,
                'depends_on': ['Roles', 'Departments'],
                'critical': True
            },
            {
                'name': 'Lists',
                'seeder': ListSeeder,
                'depends_on': [],
                'critical': True
            },
            {
                'name': 'List Items',
                'seeder': ListItemSeeder,
                'depends_on': ['Lists'],
                'critical': True
            },
            {
                'name': 'Form Fields',
                'seeder': FormFieldSeeder,
                'depends_on': ['Lists'],
                'critical': True
            },
            {
                'name': 'Help Topics',
                'seeder': HelpTopicSeeder,
                'depends_on': ['Departments', 'Teams', 'SLAs'],
                'critical': True
            },
            {
                'name': 'Ticket Statuses',
                'seeder': StatusSeeder,
                'depends_on': [],
                'critical': True
            },
            {
                'name': 'Filters',
                'seeder': FilterSeeder,
                'depends_on': ['Help Topics'],
                'critical': False
            },
            {
                'name': 'Sequences',
                'seeder': SequenceSeeder,
                'depends_on': [],
                'critical': True
            },
        ]
        
        # Add demo tickets if enabled
        if self.demo_mode:
            self.seeding_steps.append({
                'name': 'Demo Tickets',
                'seeder': DemoTicketSeeder,
                'depends_on': ['Staff', 'Departments', 'Help Topics'],
                'critical': False
            })
    
    def validate_dependencies(self) -> bool:
        """Validate that all dependencies are resolvable.
        
        Returns:
            True if dependencies are valid, False otherwise
        """
        seeder_names = {step['name'] for step in self.seeding_steps}
        
        for step in self.seeding_steps:
            for dep in step['depends_on']:
                if dep not in seeder_names:
                    logger.error(f"Invalid dependency: {step['name']} depends on {dep} (not found)")
                    return False
        
        return True
    
    def execute(self) -> bool:
        """Execute all seeders in order.
        
        Returns:
            True if all critical seeders succeeded, False otherwise
        """
        self.start_time = datetime.now()
        logger.info("=" * 70)
        logger.info("OSTICKET SEEDING ORCHESTRATION STARTED")
        logger.info(f"Start Time: {self.start_time}")
        logger.info(f"Demo Mode: {self.demo_mode}")
        logger.info("=" * 70)
        
        # Validate dependencies first
        if not self.validate_dependencies():
            logger.error("Dependency validation failed. Aborting.")
            return False
        
        # Initialize database connection pool
        try:
            db_config_dict = {
                'host': self.config.db_config.host,
                'user': self.config.db_config.user,
                'password': self.config.db_config.password,
                'database': self.config.db_config.database,
                'pool_size': 5,
                'pool_name': 'osticket_seeder_pool'
            }
            DatabaseConnection.initialize_pool(db_config_dict)
            connection = DatabaseConnection.get_connection()
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.critical(f"Failed to initialize database connection: {str(e)}")
            return False
        
        try:
            # Execute each seeder in order
            for i, step in enumerate(self.seeding_steps, 1):
                step_name = step['name']
                seeder_class = step['seeder']
                is_critical = step['critical']
                
                logger.info("")
                logger.info(f"[{i}/{len(self.seeding_steps)}] {step_name}")
                logger.info(f"Dependencies: {', '.join(step['depends_on']) or 'None'}")
                logger.info(f"Critical: {is_critical}")
                logger.info("-" * 70)
                
                try:
                    # Instantiate and execute seeder (pass connection, not config)
                    seeder = seeder_class(connection)
                    result = seeder.seed()
                    
                    self.results[step_name] = {
                        'status': 'SUCCESS',
                        'records': result.get('inserted', 0) if isinstance(result, dict) else 0,
                        'updated': result.get('updated', 0) if isinstance(result, dict) else 0,
                        'message': result.get('summary', 'Seeding completed') if isinstance(result, dict) else 'Seeding completed'
                    }
                    
                    logger.info(f"[OK] {step_name} seeded successfully")
                    logger.info(f"  Inserted: {result.get('inserted', 0) if isinstance(result, dict) else 0}, "
                              f"Updated: {result.get('updated', 0) if isinstance(result, dict) else 0}")
                
                except Exception as e:
                    logger.error(f"[FAIL] {step_name} seeding failed: {str(e)}")
                    
                    self.results[step_name] = {
                        'status': 'FAILED',
                        'error': str(e)
                    }
                    
                    if is_critical:
                        logger.critical(f"Critical seeder failed. Aborting remaining seeders.")
                        self.end_time = datetime.now()
                        self._print_summary()
                        return False
            
            self.end_time = datetime.now()
            self._print_summary()
            return True
        
        except Exception as e:
            logger.critical(f"Orchestration failed: {str(e)}")
            self.end_time = datetime.now()
            self._print_summary()
            return False
    
    def _print_summary(self) -> None:
        """Print execution summary."""
        logger.info("")
        logger.info("=" * 70)
        logger.info("SEEDING ORCHESTRATION SUMMARY")
        logger.info("=" * 70)
        
        total_steps = len(self.seeding_steps)
        successful = sum(1 for r in self.results.values() if r['status'] == 'SUCCESS')
        failed = sum(1 for r in self.results.values() if r['status'] == 'FAILED')
        
        total_inserted = sum(r.get('records', 0) for r in self.results.values() if r['status'] == 'SUCCESS')
        total_updated = sum(r.get('updated', 0) for r in self.results.values() if r['status'] == 'SUCCESS')
        
        logger.info(f"Total Steps: {total_steps}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Total Records Inserted: {total_inserted}")
        logger.info(f"Total Records Updated: {total_updated}")
        
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            logger.info(f"Duration: {duration:.2f} seconds")
        
        logger.info("")
        logger.info("Detailed Results:")
        logger.info("-" * 70)
        
        for step_name, result in self.results.items():
            status = result['status']
            if status == 'SUCCESS':
                logger.info(f"✓ {step_name}: {result['message']}")
            else:
                logger.error(f"✗ {step_name}: {result.get('error', 'Unknown error')}")
        
        logger.info("=" * 70)
        logger.info(f"End Time: {self.end_time}")
        logger.info("=" * 70)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='osTicket Database Seeding Orchestration'
    )
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Include demo tickets in seeding'
    )
    parser.add_argument(
        '--mode',
        type=str,
        default='partial',
        choices=['full', 'partial', 'reset', 'validate', 'rollback'],
        help='Seeding mode (default: partial)'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Create backup before seeding'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test without committing changes'
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration with arguments
        config = Config(
            env='docker',
            env_file='.env',
            mode=args.mode,
            backup=args.backup,
            verbose=args.verbose,
            dry_run=args.dry_run
        )
        
        # Create and execute orchestrator
        orchestrator = SeedingOrchestrator(config, demo_mode=args.demo)
        success = orchestrator.execute()
        
        return 0 if success else 1
    
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
