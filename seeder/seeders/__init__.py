"""
osTicket Seeder Package

All seeder classes for populating osTicket database.
Each seeder extends BaseSeeder and implements the seed() method.

Seeding Order (Non-Negotiable FK Dependencies):
1. Roles
2. Departments
3. SLAs
4. Teams
5. Staff (depends on Roles, Departments)
6. Lists
7. List Items (depends on Lists)
8. Form Fields (depends on Lists)
9. Help Topics (depends on Departments, Teams, SLAs)
10. Ticket Statuses
11. Filters (depends on Help Topics)
12. Sequences
13. Demo Tickets (optional)
"""

from .roles import RoleSeeder
from .departments import DepartmentSeeder
from .slas import SLASeeder
from .teams import TeamSeeder
from .staff import StaffSeeder
from .lists import ListSeeder
from .list_items import ListItemSeeder
from .form_fields import FormFieldSeeder
from .help_topics import HelpTopicSeeder
from .statuses import StatusSeeder
from .filters import FilterSeeder
from .sequences import SequenceSeeder

try:
    from .demo_tickets import DemoTicketSeeder
except ImportError:
    DemoTicketSeeder = None

__all__ = [
    'RoleSeeder',
    'DepartmentSeeder',
    'SLASeeder',
    'TeamSeeder',
    'StaffSeeder',
    'ListSeeder',
    'ListItemSeeder',
    'FormFieldSeeder',
    'HelpTopicSeeder',
    'StatusSeeder',
    'FilterSeeder',
    'SequenceSeeder',
    'DemoTicketSeeder',
]
