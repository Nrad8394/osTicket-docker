"""
Seeder for Staff Accounts

Loads data from: seeder/data/staff.json
Seeds into table: ost_staff
Dependencies: ost_role (role_id), ost_department (dept_id)
Expected count: ~12 staff accounts per RFC S2025_195201

CRITICAL: Passwords are hashed using bcrypt (passlib)
"""

from base import BaseSeeder
from config import Config
from passlib.context import CryptContext
import json


class StaffSeeder(BaseSeeder):
    """Seed osTicket staff accounts with bcrypt password hashing"""
    
    def __init__(self, connection):
        super().__init__(connection)
        self.table_name = 'staff'
        
        # Initialize password hasher with bcrypt
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12,
            bcrypt__truncate_error=False  # Auto-truncate passwords > 72 bytes
        )
    
    def seed(self) -> dict:
        """Main seeding method for staff"""
        
        # Load data from JSON file
        staff_data = self.load_json('seeder/data/staff.json')
        
        # Validate before inserting
        self._validate_staff(staff_data)
        
        # Insert or update each staff member
        for staff in staff_data:
            # Note: FK validation skipped - assuming dependencies already seeded
            # if 'role_id' in staff and staff['role_id']:
            #     self.validate_fk('role', staff['role_id'])
            # if 'dept_id' in staff and staff['dept_id']:
            #     self.validate_fk('department', staff['dept_id'])
            
            # Transform 'id' to 'staff_id' for database compatibility
            if 'id' in staff:
                staff['staff_id'] = staff['id']
                del staff['id']
            
            # Transform 'name' to 'firstname' and 'lastname'
            if 'name' in staff:
                name_parts = staff['name'].split(' ', 1)
                staff['firstname'] = name_parts[0]
                staff['lastname'] = name_parts[1] if len(name_parts) > 1 else ''
                del staff['name']
            
            # Add default signature if not present (required by database)
            if 'signature' not in staff:
                staff['signature'] = ''
            
            # Hash the password if present (and temp or plain password provided)
            # Note: bcrypt has 72-byte limit
            if 'temp_password' in staff and staff['temp_password']:
                # Ensure password is not too long for bcrypt (72 bytes max)
                # Simple truncation to 50 chars to be safe for multi-byte chars
                password = staff['temp_password'][:50]
                staff['passwd'] = self.pwd_context.hash(password)
                del staff['temp_password']  # Remove temp_password from insert
            elif 'password' in staff and staff['password']:
                # Ensure password is not too long for bcrypt (72 bytes max)
                # Simple truncation to 50 chars to be safe for multi-byte chars
                password = staff['password'][:50]
                staff['passwd'] = self.pwd_context.hash(password)
                del staff['password']
            
            self.insert_or_update(
                table=self.table_name,
                data=staff,
                key_cols=['staff_id']
            )
        
        # Return summary
        return self.summary()
    
    def _validate_staff(self, staff_list: list) -> None:
        """Validate staff data before insertion"""
        for staff in staff_list:
            assert 'id' in staff, f"Staff must have 'id': {staff}"
            assert 'name' in staff, f"Staff must have 'name': {staff}"
            assert 'email' in staff, f"Staff must have 'email': {staff}"
            assert 'role_id' in staff, f"Staff must have 'role_id': {staff}"
            assert 'dept_id' in staff, f"Staff must have 'dept_id': {staff}"
            assert ('temp_password' in staff or 'password' in staff), \
                f"Staff must have 'temp_password' or 'password': {staff}"


if __name__ == '__main__':
    config = Config()
    seeder = StaffSeeder(config)
    results = seeder.seed()
    print(results)
