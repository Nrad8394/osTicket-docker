"""
Seeder for Ticket Statuses

Loads data from: seeder/data/statuses.json
Seeds into table: ost_ticket_status
Dependencies: None
Expected count: ~16 custom statuses per RFC S2025_195201
"""

from base import BaseSeeder
from config import Config


class StatusSeeder(BaseSeeder):
    """Seed osTicket custom ticket statuses"""
    
    def __init__(self, connection):
        super().__init__(connection)
        self.table_name = 'ticket_status'
    
    def seed(self) -> dict:
        """Main seeding method for ticket statuses"""
        
        # Load data from JSON file
        statuses_data = self.load_json('seeder/data/statuses.json')
        
        # Validate before inserting
        self._validate_statuses(statuses_data)
        
        # Insert or update each status
        for status in statuses_data:
            self.insert_or_update(
                table=self.table_name,
                data=status,
                key_cols=['id']
            )
        
        # Return summary
        return self.summary()
    
    def _validate_statuses(self, statuses: list) -> None:
        """Validate status data before insertion"""
        valid_states = {'open', 'closed', 'resolved'}
        
        for status in statuses:
            assert 'id' in status, f"Status must have 'id': {status}"
            assert 'name' in status, f"Status must have 'name': {status}"
            assert 'state' in status, f"Status must have 'state': {status}"
            assert status['state'] in valid_states, f"Status state must be one of {valid_states}: {status}"
            assert isinstance(status['id'], int), f"Status id must be integer: {status}"


if __name__ == '__main__':
    config = Config()
    seeder = StatusSeeder(config)
    results = seeder.seed()
    print(results)
