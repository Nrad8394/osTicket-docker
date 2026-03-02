"""
Seeder for Ticket Number Sequences

Loads data from: seeder/data/sequences.json
Seeds into table: ost_sequence
Dependencies: None
Expected count: ~1-2 sequences per RFC S2025_195201

Defines ticket numbering format (e.g., KRA-%Y%M-{num})
"""

from base import BaseSeeder
from config import Config


class SequenceSeeder(BaseSeeder):
    """Seed osTicket ticket numbering sequences"""
    
    # ost_sequence table doesn't have 'created' field, only 'updated'
    auto_add_created = False
    
    def __init__(self, connection):
        super().__init__(connection)
        self.table_name = 'sequence'
    
    def seed(self) -> dict:
        """Main seeding method for sequences"""
        
        # Load data from JSON file
        sequences_data = self.load_json('seeder/data/sequences.json')
        
        # Validate before inserting
        self._validate_sequences(sequences_data)
        
        # Insert or update each sequence
        for seq in sequences_data:
            # Remove unsupported fields (pattern, description, created don't exist in table)
            seq.pop('pattern', None)
            seq.pop('description', None)
            seq.pop('created', None)
            
            # Add default values for required fields if not present
            if 'next' not in seq:
                seq['next'] = 1
            if 'increment' not in seq:
                seq['increment'] = 1
            if 'padding' not in seq:
                seq['padding'] = '0'
            
            self.insert_or_update(
                table=self.table_name,
                data=seq,
                key_cols=['id', 'name']
            )
        
        # Return summary
        return self.summary()
    
    def _validate_sequences(self, sequences: list) -> None:
        """Validate sequence data before insertion"""
        for seq in sequences:
            assert 'id' in seq, f"Sequence must have 'id': {seq}"
            assert 'name' in seq, f"Sequence must have 'name': {seq}"
            assert isinstance(seq['id'], int), f"Sequence id must be integer: {seq}"


if __name__ == '__main__':
    config = Config()
    seeder = SequenceSeeder(config)
    results = seeder.seed()
    print(results)
