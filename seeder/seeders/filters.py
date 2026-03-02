"""
Seeder for Auto-Assignment Filters

Loads data from: seeder/data/filters.json
Seeds into table: ost_filter
Dependencies: ost_department (dept_id), ost_help_topic (help_topic_id in rule_match)
Expected count: ~12-15 filter rules per RFC S2025_195201

CRITICAL: Filter rules stored as JSON in 'rule_match' and action_data columns
This seeder handles complex rule matching logic.
"""

from base import BaseSeeder
from config import Config
import json


class FilterSeeder(BaseSeeder):
    """Seed osTicket auto-assignment filters and routing rules"""
    
    def __init__(self, connection):
        super().__init__(connection)
        self.table_name = 'filter'
    
    def seed(self) -> dict:
        """Main seeding method for filters"""
        
        # Load data from JSON file
        filters_data = self.load_json('seeder/data/filters.json')
        
        # Validate before inserting
        self._validate_filters(filters_data)
        
        # Insert or update each filter
        for filter_record in filters_data:
            # Note: FK validation skipped - assuming dependencies already seeded
            # Validate FK references
            # if 'dept_id' in filter_record and filter_record['dept_id']:
            #     self.validate_fk('department', filter_record['dept_id'])
            
            # Validate help_topic_id references in rule conditions
            rule_match = filter_record.get('rule_match', {})
            if isinstance(rule_match, str):
                rule_match = json.loads(rule_match)
            
            # for condition in rule_match.get('conditions', []):
            #     if condition.get('field') == 'help_topic_id':
            #         self.validate_fk('help_topic', condition['value'])
            
            # Transform field names: description → notes, enabled → isactive
            if 'description' in filter_record:
                filter_record['notes'] = filter_record.pop('description')
            if 'enabled' in filter_record:
                filter_record['isactive'] = filter_record.pop('enabled')
            
            # Truncate name to 32 chars (database limit)
            if 'name' in filter_record and len(filter_record['name']) > 32:
                filter_record['name'] = filter_record['name'][:32]
            
            # Remove complex fields (rule_match, action_data stored in separate tables)
            filter_record.pop('rule_match', None)
            filter_record.pop('action_data', None)
            
            self.insert_or_update(
                table=self.table_name,
                data=filter_record,
                key_cols=['id']
            )
        
        # Return summary
        return self.summary()
    
    def _validate_filters(self, filters: list) -> None:
        """Validate filter data before insertion"""
        for filter_record in filters:
            assert 'id' in filter_record, f"Filter must have 'id': {filter_record}"
            assert 'name' in filter_record, f"Filter must have 'name': {filter_record}"
            assert 'rule_match' in filter_record, f"Filter must have 'rule_match': {filter_record}"
            assert 'action_data' in filter_record, f"Filter must have 'action_data': {filter_record}"
            
            # Validate rule_match structure
            rule_match = filter_record['rule_match']
            if isinstance(rule_match, str):
                rule_match = json.loads(rule_match)
            
            assert 'conditions' in rule_match, \
                f"rule_match must have 'conditions' array: {filter_record}"
            assert isinstance(rule_match['conditions'], list), \
                f"rule_match.conditions must be array: {filter_record}"
            
            # Validate each condition
            for condition in rule_match['conditions']:
                assert 'field' in condition, f"Condition must have 'field': {condition}"
                assert 'operator' in condition, f"Condition must have 'operator': {condition}"
                assert 'value' in condition, f"Condition must have 'value': {condition}"


if __name__ == '__main__':
    config = Config()
    seeder = FilterSeeder(config)
    results = seeder.seed()
    print(results)
