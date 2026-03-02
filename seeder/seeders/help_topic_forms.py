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
                sql = f"""
                    INSERT INTO {self.table('help_topic_form')} (topic_id, form_id)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE form_id=VALUES(form_id)
                """
                result = self.conn.execute(sql, [topic_id, 2])
                
                if result.rowcount > 0:
                    if result.lastrowid > 0:
                        inserted += 1
                    else:
                        updated += 1
            
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
