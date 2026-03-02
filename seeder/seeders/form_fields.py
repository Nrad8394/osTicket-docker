"""
Seeder for Custom Form Fields

Loads data from: seeder/data/form_fields.json
Seeds into table: ost_form_field
Dependencies: ost_list (list_id) - for dropdown references
Expected count: ~10 custom form fields per RFC S2025_195201

CRITICAL: Form field configuration stored as JSON in 'configuration' column
This seeder handles JSON serialization of field configuration.
"""

from base import BaseSeeder
from config import Config
import json


class FormFieldSeeder(BaseSeeder):
    """Seed osTicket custom form fields for ticket details"""
    
    def __init__(self, connection):
        super().__init__(connection)
        self.table_name = 'form_field'
        self.form_id = 2  # Always form_id=2 for Ticket Details form
    
    def seed(self) -> dict:
        """Main seeding method for form fields"""
        
        # Load data from JSON file
        fields_data = self.load_json('seeder/data/form_fields.json')
        
        # Validate before inserting
        self._validate_fields(fields_data)
        
        # Insert or update each form field
        for field in fields_data:
            # Ensure form_id is always 2 (Ticket Details)
            field['form_id'] = self.form_id
            
            # Validate list_id reference if present (for dropdown fields)
            if field.get('configuration', {}).get('list_id'):
                list_id = field['configuration']['list_id']
                self.validate_fk('ost_list', list_id)
            
            # Convert configuration dict to JSON string
            if isinstance(field.get('configuration'), dict):
                field['configuration'] = json.dumps(field['configuration'])
            
            self.insert_or_update(
                table=self.table_name,
                data=field,
                key_cols=['id', 'form_id']
            )
        
        # Return summary
        return self.summary()
    
    def _validate_fields(self, fields: list) -> None:
        """Validate form field data before insertion"""
        valid_types = {
            'text', 'textarea', 'dropdown', 'date', 'checkbox', 
            'radio', 'file', 'phone', 'email', 'url'
        }
        
        for field in fields:
            assert 'id' in field, f"Field must have 'id': {field}"
            assert 'label' in field, f"Field must have 'label': {field}"
            assert 'type' in field, f"Field must have 'type': {field}"
            assert field['type'] in valid_types, \
                f"Field type must be one of {valid_types}: {field}"
            
            # If type is dropdown, configuration must have list_id
            if field['type'] == 'dropdown':
                config = field.get('configuration', {})
                if isinstance(config, str):
                    config = json.loads(config)
                assert 'list_id' in config, \
                    f"Dropdown field must have list_id in configuration: {field}"


if __name__ == '__main__':
    config = Config()
    seeder = FormFieldSeeder(config)
    results = seeder.seed()
    print(results)
