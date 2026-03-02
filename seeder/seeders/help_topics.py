#!/usr/bin/env python3
"""
Help Topic Seeder Implementation
Generates and seeds ~89 help topics programmatically

This is the most complex seeder because it needs to:
1. Generate parent topics for each system
2. Generate child topics for each type/severity combination
3. Add special topics (Change Management, DB Intervention, Security)
4. Link everything to departments, teams, and SLAs
"""

import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from base import BaseSeeder


@dataclass
class System:
    """Represents an ICT system"""
    id: int
    name: str
    code: str
    ispublic: int = 1


@dataclass
class IssueType:
    """Represents an issue type with routing info"""
    name: str
    code: str
    dept_id: int
    team_id: int
    sla_base: int  # Base SLA ID (Minor offset, Medium +1, Major +2)
    ispublic: int = 1


class HelpTopicGenerator:
    """Generate~89 help topics from system/type/severity matrix"""
    
    # Define all ICT systems
    SYSTEMS = [
        System(id=10, name="iTax", code="ITAX"),
        System(id=11, name="iCMS", code="ICMS"),
        System(id=12, name="iBid", code="IBID"),
        System(id=13, name="iSCAN", code="ISCAN"),
        System(id=14, name="WIMS", code="WIMS"),
        System(id=15, name="eCustoms Mobile App", code="ECUSTOMS"),
        System(id=16, name="eTIMS", code="ETIMS"),
        System(id=17, name="General ICT Issues", code="OTHER"),
    ]
    
    # Define issue types (routing rules)
    ISSUE_TYPES = [
        IssueType(
            name="Bug",
            code="BUG",
            dept_id=10,  # BAS
            team_id=10,  # BAS-Analysts
            sla_base=10,  # SLAs 10, 11, 12 (Minor, Medium, Major)
            ispublic=1
        ),
        IssueType(
            name="Enhancement",
            code="ENH",
            dept_id=11,  # BSD
            team_id=11,  # BSD-Developers
            sla_base=13,  # SLAs 13, 14, 15
            ispublic=1
        ),
        IssueType(
            name="DB Intervention",
            code="DBI",
            dept_id=13,  # SA&DM
            team_id=13,  # SA&DM-Officers
            sla_base=16,  # SLAs 16, 17, 18
            ispublic=0  # Not visible to external users
        ),
    ]
    
    # Severity levels (offset from sla_base)
    SEVERITIES = [
        {"name": "Minor", "code": "MINOR", "offset": 0},
        {"name": "Medium", "code": "MEDIUM", "offset": 1},
        {"name": "Major", "code": "MAJOR", "offset": 2},
    ]
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def generate_all_topics(self) -> List[Dict[str, Any]]:
        """
        Generate all ~89 help topics
        
        Returns:
            List of topic dicts, ready for insertion
        """
        topics = []
        
        # 1. Parent topics (8 systems)
        topics.extend(self._generate_parent_topics())
        
        # 2. Child topics (8 systems × 3 types × 3 severities = 72)
        topics.extend(self._generate_child_topics())
        
        # 3. Special topics (3 non-system topics)
        topics.extend(self._generate_special_topics())
        
        self.logger.info(f"Generated {len(topics)} help topics")
        return topics
    
    def _generate_parent_topics(self) -> List[Dict[str, Any]]:
        """
        Generate top-level system topics (8 topics)
        These serve as category headers for the child topics
        """
        topics = []
        
        for system in self.SYSTEMS:
            topic = {
                'topic_id': system.id,
                'topic_pid': 0,  # Top-level (no parent)
                'topic': f"{system.name} Issues",
                'dept_id': 10,  # BAS as default intake
                'staff_id': 0,  # No specific staff assignment
                'team_id': 10,  # BAS-Analysts triage all incoming
                'sla_id': 19,  # Default SLA (48-hour fallback)
                'page_id': 0,  # No custom thank-you page
                'sequence_id': 0,  # Use default numbering
                'ispublic': system.ispublic,
                'noautoresp': 0,  # Send auto-response
                'flags': 0,  # No special flags
                'status_id': 0,  # Use ticket status default
                'priority_id': 0,  # Use priority default
                'notes': f"Parent category for {system.name} system issues",
                'number_format': None,  # Use default format
                'sort': system.id,
            }
            topics.append(topic)
        
        return topics
    
    def _generate_child_topics(self) -> List[Dict[str, Any]]:
        """
        Generate type/severity combinations (8 systems × 3 types × 3 severities = 72 topics)
        
        Each child topic is:
        - A child of a parent system topic
        - Routes to the appropriate department/team
        - Assigned the appropriate SLA based on type + severity
        """
        topics = []
        topic_id = 100  # Start numbering child topics at 100
        
        for system in self.SYSTEMS:
            for issue_type in self.ISSUE_TYPES:
                for severity in self.SEVERITIES:
                    
                    # Calculate SLA ID: base + offset
                    sla_id = issue_type.sla_base + severity['offset']
                    
                    # Build topic name
                    topic_name = f"{system.name} — {issue_type.name} / {severity['name']}"
                    
                    topic = {
                        'topic_id': topic_id,
                        'topic_pid': system.id,  # Child of system parent topic
                        'topic': topic_name,
                        'dept_id': issue_type.dept_id,  # Route to appropriate dept
                        'staff_id': 0,  # No specific staff assignment
                        'team_id': issue_type.team_id,  # Assign to appropriate team
                        'sla_id': sla_id,  # Apply appropriate SLA
                        'page_id': 0,  # No custom thank-you page
                        'sequence_id': 0,  # Use default numbering
                        'ispublic': issue_type.ispublic if issue_type.code != 'DBI' else 0,
                        'noautoresp': 0,  # Send auto-response
                        'flags': 0,  # No special flags
                        'status_id': 0,  # Use ticket status default
                        'priority_id': 0,  # Use priority default
                        'sort': topic_id,
                        'notes': f"Auto-routes {system.code} {issue_type.code} {severity['code']} to {issue_type.name}",
                        'number_format': None,  # Use default format
                    }
                    topics.append(topic)
                    topic_id += 1
        
        return topics
    
    def _generate_special_topics(self) -> List[Dict[str, Any]]:
        """
        Generate special non-system-specific topics:
        - Change Management (RFC approvals)
        - DB Intervention (special manual process)
        - Security Incidents (ISS oversight)
        """
        return [
            {
                'topic_id': 18,
                'topic_pid': 0,  # Top-level
                'topic': "Change Management / RFC",
                'dept_id': 15,  # Change Management dept (S&C)
                'staff_id': 0,
                'team_id': 14,  # Change-Management team (WIMS)
                'sla_id': 14,  # Enhancement-Medium SLA (5 days)
                'page_id': 0,
                'sequence_id': 0,
                'ispublic': 0,  # Internal only
                'noautoresp': 0,
                'flags': 0,
                'status_id': 0,
                'priority_id': 0,
                'notes': "RFC reviews and change approvals",
                'number_format': None,
                'sort': 18,
            },
            {
                'topic_id': 19,
                'topic_pid': 0,  # Top-level
                'topic': "DB Intervention Request",
                'dept_id': 13,  # SA&DM
                'staff_id': 0,
                'team_id': 13,  # SA&DM-Officers (iSCAN)
                'sla_id': 17,  # DB-Medium SLA (same-day)
                'page_id': 0,
                'sequence_id': 0,
                'ispublic': 0,  # Internal only
                'noautoresp': 0,
                'flags': 0,
                'status_id': 0,
                'priority_id': 0,
                'notes': "Direct database intervention requests",
                'number_format': None,
                'sort': 19,
            },
            {
                'topic_id': 20,
                'topic_pid': 0,  # Top-level
                'topic': "Security Incidents (ISS)",
                'dept_id': 16,  # Information System Security (TS)
                'staff_id': 0,
                'team_id': 10,  # BAS-Analysts for initial triage (iTax)
                'sla_id': 12,  # Bug-Major SLA (4 hours — critical)
                'page_id': 0,
                'sequence_id': 0,
                'ispublic': 0,  # Internal only
                'noautoresp': 0,
                'flags': 0,
                'status_id': 0,
                'priority_id': 0,
                'notes': "Security incidents requiring ISS investigation",
                'number_format': None,
                'sort': 20,
            },
        ]
    
    def validate_topics(self, topics: List[Dict[str, Any]]) -> bool:
        """
        Validate topic list for consistency
        
        Checks:
        - No duplicate topic_ids
        - All parent topic_ids exist
        - All dept_ids exist
        - All team_ids exist
        - All sla_ids exist (should be 1-10)
        """
        errors = []
        
        # Check for duplicate IDs
        ids = [t['topic_id'] for t in topics]
        if len(ids) != len(set(ids)):
            errors.append("Duplicate topic IDs found")
        
        # Check parent references
        valid_ids = set(ids)
        for topic in topics:
            if topic['topic_pid'] not in valid_ids and topic['topic_pid'] != 0:
                errors.append(f"Topic {topic['topic_id']}: invalid parent {topic['topic_pid']}")
        
        # Check dept_id/team_id/sla_id ranges (basic validation)
        for topic in topics:
            if topic['dept_id'] < 10 or topic['dept_id'] > 17:
                errors.append(f"Topic {topic['topic_id']}: invalid dept_id {topic['dept_id']}")
            if topic['team_id'] < 10 or topic['team_id'] > 16:
                errors.append(f"Topic {topic['topic_id']}: invalid team_id {topic['team_id']}")
            if topic['sla_id'] < 10 or topic['sla_id'] > 19:
                errors.append(f"Topic {topic['topic_id']}: invalid sla_id {topic['sla_id']}")
        
        if errors:
            for error in errors:
                self.logger.error(error)
            return False
        
        self.logger.info(f"[OK] All {len(topics)} topics validated successfully")
        return True


class HelpTopicSeeder(BaseSeeder):
    """Seeds help topics to database using the generator"""
    
    def seed(self) -> Dict[str, Any]:
        """
        Seed all help topics
        
        Returns:
            Dict with success status and counts
        """
        try:
            self.log_info("Generating help topics...")
            
            # Generate topics
            generator = HelpTopicGenerator(self.logger)
            topics = generator.generate_all_topics()
            
            # Validate before inserting
            if not generator.validate_topics(topics):
                raise ValueError("Help topic validation failed")
            
            # Insert topics
            self.log_info(f"Inserting {len(topics)} help topics...")
            
            for topic in topics:
                # Add timestamps
                topic['created'] = 'NOW()'
                topic['updated'] = 'NOW()'
                
                # Prepare SQL with proper timestamp handling
                cols = list(topic.keys())
                vals = list(topic.values())
                
                # Build placeholders, use NOW() for timestamps
                placeholders = []
                clean_vals = []
                for col, val in zip(cols, vals):
                    if val == 'NOW()':
                        placeholders.append('NOW()')
                    else:
                        placeholders.append('%s')
                        clean_vals.append(val)
                
                sql = f"""
                    INSERT INTO {self.table('help_topic')} ({', '.join(cols)})
                    VALUES ({', '.join(placeholders)})
                    ON DUPLICATE KEY UPDATE
                        topic=VALUES(topic),
                        dept_id=VALUES(dept_id),
                        team_id=VALUES(team_id),
                        sla_id=VALUES(sla_id),
                        updated=NOW()
                """
                
                result = self.conn.execute(sql, clean_vals)
                if result.rowcount > 0:
                    if result.lastrowid > 0:
                        self._inserted_ids.append(result.lastrowid)
                    else:
                        self._updated_ids.append(topic['topic_id'])
            
            self.log_info(f"[OK] Help topics seeding complete: {len(self._inserted_ids)} inserted, {len(self._updated_ids)} updated")
            
            return {
                'success': True,
                'inserted': len(self._inserted_ids),
                'updated': len(self._updated_ids),
                'total': len(topics),
                'errors': self._errors,
            }
        
        except Exception as e:
            self.log_error(f"Help topic seeding failed: {e}")
            self._errors.append(str(e))
            return {
                'success': False,
                'inserted': len(self._inserted_ids),
                'updated': len(self._updated_ids),
                'errors': self._errors,
            }


# CLI support
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Profile: Generate and display all topics
    generator = HelpTopicGenerator()
    topics = generator.generate_all_topics()
    
    print(f"\nGenerated {len(topics)} topics:\n")
    
    # Show parent topics
    parents = [t for t in topics if t['topic_pid'] == 0]
    print(f"Parent topics ({len(parents)}):")
    for p in parents:
        print(f"  {p['topic_id']:3d} — {p['topic']:40s} (Dept: {p['dept_id']}, SLA: {p['sla_id']})")
    
    # Show sample child topics
    children = [t for t in topics if t['topic_pid'] > 0 and t['topic_pid'] <= 17]
    print(f"\nChild topics (first 10 of {len(children)}):")
    for c in children[:10]:
        print(f"  {c['topic_id']:3d} — {c['topic']:50s} (Parent: {c['topic_pid']}, Dept: {c['dept_id']}, SLA: {c['sla_id']})")
    
    # Summary
    print(f"\nTopic Distribution:")
    print(f"  • Parent topics (systems):    {len(parents)}")
    print(f"  • Child topics (matrix):      {len([t for t in topics if t['topic_pid'] > 0 and t['topic_pid'] <= 17])}")
    print(f"  • Special topics:             {len([t for t in topics if t['topic_id'] > 17])}")
    print(f"  • Total:                      {len(topics)}")
