"""
Seeder for Support Departments

Loads data from: seeder/data/departments.json
Seeds into table: ost_department
Dependencies: None
Expected count: ~8 departments per RFC S2025_195201
"""

from base import BaseSeeder
from config import Config


class DepartmentSeeder(BaseSeeder):
    """Seed osTicket support departments"""
    
    def __init__(self, connection):
        super().__init__(connection)
        self.table_name = 'department'
    
    def seed(self) -> dict:
        """Main seeding method for departments"""
        
        # Load data from JSON file
        depts_data = self.load_json('seeder/data/departments.json')
        
        # Validate before inserting
        self._validate_departments(depts_data)
        
        # Insert or update each department
        for dept in depts_data:
            self.insert_or_update(
                table=self.table_name,
                data=dept,
                key_cols=['id']
            )
        
        # Return summary
        return self.summary()
    
    def _validate_departments(self, depts: list) -> None:
        """Validate department data before insertion"""
        for dept in depts:
            assert 'id' in dept, f"Department must have 'id': {dept}"
            assert 'name' in dept, f"Department must have 'name': {dept}"
            assert isinstance(dept['id'], int), f"Department id must be integer: {dept}"
            assert isinstance(dept['name'], str), f"Department name must be string: {dept}"


if __name__ == '__main__':
    config = Config()
    seeder = DepartmentSeeder(config)
    results = seeder.seed()
    print(results)
