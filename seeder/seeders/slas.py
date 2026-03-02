"""
Seeder for Service Level Agreements (SLAs)

Loads data from: seeder/data/slas.json
Seeds into table: ost_sla
Dependencies: None
Expected count: ~10 SLA plans per RFC S2025_195201
"""

from base import BaseSeeder
from config import Config


class SLASeeder(BaseSeeder):
    """Seed osTicket SLA (Service Level Agreement) plans"""
    
    def __init__(self, connection):
        super().__init__(connection)
        self.table_name = 'sla'
    
    def seed(self) -> dict:
        """Main seeding method for SLAs"""
        
        # Load data from JSON file
        slas_data = self.load_json('seeder/data/slas.json')
        
        # Validate before inserting
        self._validate_slas(slas_data)
        
        # Insert or update each SLA
        for sla in slas_data:
            self.insert_or_update(
                table=self.table_name,
                data=sla,
                key_cols=['id']
            )
        
        # Return summary
        return self.summary()
    
    def _validate_slas(self, slas: list) -> None:
        """Validate SLA data before insertion"""
        for sla in slas:
            assert 'id' in sla, f"SLA must have 'id': {sla}"
            assert 'name' in sla, f"SLA must have 'name': {sla}"
            assert 'grace_period' in sla, f"SLA must have 'grace_period': {sla}"
            assert isinstance(sla['id'], int), f"SLA id must be integer: {sla}"
            assert isinstance(sla['grace_period'], (int, str)), f"SLA grace_period must be int or string: {sla}"


if __name__ == '__main__':
    config = Config()
    seeder = SLASeeder(config)
    results = seeder.seed()
    print(results)
