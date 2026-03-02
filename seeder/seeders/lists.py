"""
Seeder for Custom Lists

Loads data from: seeder/data/lists.json
Seeds into table: ost_list
Dependencies: None
Expected count: ~5 custom lists per RFC S2025_195201
"""

from base import BaseSeeder
from config import Config


class ListSeeder(BaseSeeder):
    """Seed osTicket custom lists (used for form field dropdowns)"""
    
    def __init__(self, connection):
        super().__init__(connection)
        self.table_name = 'list'
    
    def seed(self) -> dict:
        """Main seeding method for custom lists"""
        
        # Load data from JSON file
        lists_data = self.load_json('seeder/data/lists.json')
        
        # Validate before inserting
        self._validate_lists(lists_data)
        
        # Insert or update each list
        for list_record in lists_data:
            self.insert_or_update(
                table=self.table_name,
                data=list_record,
                key_cols=['id']
            )
        
        # Return summary
        return self.summary()
    
    def _validate_lists(self, lists: list) -> None:
        """Validate list data before insertion"""
        for list_record in lists:
            assert 'id' in list_record, f"List must have 'id': {list_record}"
            assert 'name' in list_record, f"List must have 'name': {list_record}"
            assert isinstance(list_record['id'], int), f"List id must be integer: {list_record}"
            assert isinstance(list_record['name'], str), f"List name must be string: {list_record}"


if __name__ == '__main__':
    config = Config()
    seeder = ListSeeder(config)
    results = seeder.seed()
    print(results)
