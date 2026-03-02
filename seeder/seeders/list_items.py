"""
Seeder for List Items

Loads data from: seeder/data/list_items.json
Seeds into table: ost_list_items
Dependencies: ost_list (list_id)
Expected count: ~150+ items per RFC S2025_195201

Uses bulk insert for performance optimization with large datasets.
"""

from base import BaseSeeder
from config import Config


class ListItemSeeder(BaseSeeder):
    """Seed osTicket list items (dropdown options)"""
    
    def __init__(self, connection):
        super().__init__(connection)
        self.table_name = 'list_items'
    
    def seed(self) -> dict:
        """Main seeding method for list items"""
        
        # Load data from JSON file
        items_data = self.load_json('seeder/data/list_items.json')
        
        # Validate before inserting
        self._validate_items(items_data)
        
        # Validate all list_ids exist as FK constraint
        list_ids = set()
        for item in items_data:
            list_ids.add(item['list_id'])
        
        for list_id in list_ids:
            self.validate_fk('ost_list', list_id)
        
        # Use bulk insert for performance (150+ records)
        self.bulk_insert_ignore(self.table_name, items_data)
        
        # Return summary
        return self.summary()
    
    def _validate_items(self, items: list) -> None:
        """Validate item data before insertion"""
        for item in items:
            assert 'id' in item, f"Item must have 'id': {item}"
            assert 'list_id' in item, f"Item must have 'list_id': {item}"
            assert 'value' in item, f"Item must have 'value': {item}"
            assert isinstance(item['id'], int), f"Item id must be integer: {item}"
            assert isinstance(item['list_id'], int), f"Item list_id must be integer: {item}"


if __name__ == '__main__':
    config = Config()
    seeder = ListItemSeeder(config)
    results = seeder.seed()
    print(results)
