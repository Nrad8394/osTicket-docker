#!/usr/bin/env python3
"""
Help Topic Forms Association Seeder
Assigns forms to help topics for custom field visibility in the portal
"""

from typing import Dict, Any, List
from base import BaseSeeder


class HelpTopicFormSeeder(BaseSeeder):
    """Associates forms with help topics"""
    
    def seed(self) -> Dict[str, Any]:
        """
        Assign the Ticket Details form to all help topics
        
        In osTicket:
        - Form ID 1: User Contact form (guest info)
        - Form ID 2: Ticket Details form (custom fields like Priority, System, etc.)
        
        All public help topics should have form_id=2 so users see custom fields
        
        Returns:
            Dict with success status and counts
        """
        try:
            self.log_info("Assigning forms to help topics...")
            
            # Get all public help topics that should have forms
            sql = """
                SELECT topic_id FROM ost_help_topic 
                WHERE ispublic=1 AND flags=2
            """
            help_topic_ids = self.conn.fetch_all(sql)
            topic_ids = [row[0] for row in help_topic_ids] if help_topic_ids else []
            
            if not topic_ids:
                self.log_warn("No public help topics found to assign forms to")
                return {
                    'success': True,
                    'inserted': 0,
                    'updated': 0,
                    'total': 0,
                    'errors': [],
                }
            
            self.log_info(f"Found {len(topic_ids)} public help topics")
            
            inserted = 0
            updated = 0
            
            # Assign Ticket Details form (form_id=2) to each help topic
            for topic_id in topic_ids:
                # Idempotent: check if the exact association already exists
                check_sql = f"SELECT 1 FROM {self.table('help_topic_form')} WHERE topic_id=%s AND form_id=%s LIMIT 1"
                exists = self.conn.fetch_one(check_sql, (topic_id, 2))

                if exists:
                    # association already present; skip
                    continue

                # If association for this topic exists with a different form_id,
                # update it to the Ticket Details form; otherwise insert new row.
                # Check for any existing row for topic_id
                any_sql = f"SELECT id, form_id FROM {self.table('help_topic_form')} WHERE topic_id=%s LIMIT 1"
                any_row = self.conn.fetch_one(any_sql, (topic_id,))

                if any_row:
                    # Update existing association to form_id=2
                    update_sql = f"UPDATE {self.table('help_topic_form')} SET form_id=%s WHERE id=%s"
                    self.conn.execute(update_sql, (2, any_row[0]))
                    updated += 1
                else:
                    # Insert new association
                    insert_sql = f"INSERT INTO {self.table('help_topic_form')} (topic_id, form_id) VALUES (%s, %s)"
                    result = self.conn.execute(insert_sql, (topic_id, 2))
                    if result.rowcount > 0:
                        inserted += 1
            
            self.log_info(f"[OK] Help topic forms assigned: {inserted} inserted, {updated} updated")
            
            return {
                'success': True,
                'inserted': inserted,
                'updated': updated,
                'total': len(topic_ids),
                'errors': [],
            }
        
        except Exception as e:
            self.log_error(f"Help topic forms seeding failed: {e}")
            return {
                'success': False,
                'inserted': 0,
                'updated': 0,
                'errors': [str(e)],
            }
