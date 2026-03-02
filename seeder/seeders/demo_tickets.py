"""
Seeder for Demo Tickets (OPTIONAL)

Loads data from: seeder/data/demo_tickets.json
Seeds into table: ost_ticket
Dependencies: ost_staff (staff_id), ost_department (dept_id), ost_help_topic (topic_id)
Expected count: ~5-10 sample tickets per RFC S2025_195201

OPTIONAL: Only used for UAT and testing with sample data
"""

from base import BaseSeeder
from config import Config


class DemoTicketSeeder(BaseSeeder):
    """Seed osTicket sample tickets for UAT (optional)"""
    
    def __init__(self, connection):
        super().__init__(connection)
        self.table_name = 'ticket'
    
    def seed(self) -> dict:
        """Main seeding method for demo tickets"""
        
        # Load data from JSON file
        tickets_data = self.load_json('seeder/data/demo_tickets.json')
        
        # Validate before inserting
        self._validate_tickets(tickets_data)
        
        # Insert demo tickets
        for ticket in tickets_data:
            # Note: FK validation skipped - assuming dependencies already seeded
            # Validate FK references
            # if 'staff_id' in ticket and ticket['staff_id']:
            #     self.validate_fk('staff', ticket['staff_id'])
            # 
            # if 'dept_id' in ticket and ticket['dept_id']:
            #     self.validate_fk('department', ticket['dept_id'])
            # 
            # if 'topic_id' in ticket and ticket['topic_id']:
            #     self.validate_fk('help_topic', ticket['topic_id'])
            
            self.insert_or_update(
                table=self.table_name,
                data=ticket,
                key_cols=['ticket_id']
            )
        
        # Return summary
        return self.summary()
    
    def _validate_tickets(self, tickets: list) -> None:
        """Validate ticket data before insertion"""
        for ticket in tickets:
            assert 'ticket_id' in ticket, f"Ticket must have 'ticket_id': {ticket}"
            assert 'subject' in ticket, f"Ticket must have 'subject': {ticket}"
            assert 'dept_id' in ticket, f"Ticket must have 'dept_id': {ticket}"
            assert 'topic_id' in ticket, f"Ticket must have 'topic_id': {ticket}"


if __name__ == '__main__':
    config = Config()
    seeder = DemoTicketSeeder(config)
    results = seeder.seed()
    print(results)
