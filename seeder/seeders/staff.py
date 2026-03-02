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
            bcrypt__rounds=12
        )
    
    def seed(self) -> dict:
        """Main seeding method for staff"""
        
        # Load data from JSON file
        staff_data = self.load_json('seeder/data/staff.json')
        
        # Validate before inserting
        self._validate_staff(staff_data)
        
        # Insert or update each staff member
        for staff in staff_data:
            # Validate FK references exist
            if 'role_id' in staff and staff['role_id']:
                self.validate_fk('ost_role', staff['role_id'])
            
            if 'dept_id' in staff and staff['dept_id']:
                self.validate_fk('ost_department', staff['dept_id'])
            
            # Hash the password if present (and temp or plain password provided)
            if 'temp_password' in staff and staff['temp_password']:
                staff['passwd'] = self.pwd_context.hash(staff['temp_password'])
                del staff['temp_password']  # Remove temp_password from insert
            elif 'password' in staff and staff['password']:
                staff['passwd'] = self.pwd_context.hash(staff['password'])
                del staff['password']
            
            self.insert_or_update(
                table=self.table_name,
                data=staff,
                key_cols=['id']
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
