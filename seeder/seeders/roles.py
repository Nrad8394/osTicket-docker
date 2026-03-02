"""
Seeder for Staff Roles

Loads data from: seeder/data/roles.json
Seeds into table: ost_role
Dependencies: None
Expected count: ~10 roles per RFC S2025_195201
"""

from base import BaseSeeder
from config import Config
import json


class RoleSeeder(BaseSeeder):
    """Seed osTicket staff roles with permissions"""
    
    def __init__(self, connection):
        super().__init__(connection)
        self.table_name = 'role'
    
    def seed(self) -> dict:
        """Main seeding method for roles"""
        
        # Load data from JSON file
        roles_data = self.load_json('seeder/data/roles.json')
        
        # Validate before inserting
        self._validate_roles(roles_data)
        
        # Insert or update each role
        for role in roles_data:
            # Ensure permissions is JSON string
            if isinstance(role.get('permissions'), dict):
                role['permissions'] = json.dumps(role['permissions'])
            
            self.insert_or_update(
                table=self.table_name,
                data=role,
                key_cols=['id']
            )
        
        # Return summary
        return self.summary()
    
    def _validate_roles(self, roles: list) -> None:
        """Validate role data before insertion"""
        for role in roles:
            assert 'id' in role, f"Role must have 'id': {role}"
            assert 'name' in role, f"Role must have 'name': {role}"
            assert isinstance(role['id'], int), f"Role id must be integer: {role}"
            assert isinstance(role['name'], str), f"Role name must be string: {role}"


if __name__ == '__main__':
    config = Config()
    seeder = RoleSeeder(config)
    results = seeder.seed()
    print(results)
