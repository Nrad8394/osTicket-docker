"""
Seeder for Support Teams

Loads data from: seeder/data/teams.json
Seeds into table: ost_team
Dependencies: None
Expected count: ~7 teams per RFC S2025_195201
"""

from base import BaseSeeder
from config import Config


class TeamSeeder(BaseSeeder):
    """Seed osTicket support teams"""
    
    def __init__(self, connection):
        super().__init__(connection)
        self.table_name = 'team'
    
    def seed(self) -> dict:
        """Main seeding method for teams"""
        
        # Load data from JSON file
        teams_data = self.load_json('seeder/data/teams.json')
        
        # Validate before inserting
        self._validate_teams(teams_data)
        
        # Insert or update each team
        for team in teams_data:
            self.insert_or_update(
                table=self.table_name,
                data=team,
                key_cols=['team_id']
            )
        
        # Return summary
        return self.summary()
    
    def _validate_teams(self, teams: list) -> None:
        """Validate team data before insertion"""
        for team in teams:
            assert 'team_id' in team, f"Team must have 'team_id': {team}"
            assert 'name' in team, f"Team must have 'name': {team}"
            assert isinstance(team['team_id'], int), f"Team team_id must be integer: {team}"
            assert isinstance(team['name'], str), f"Team name must be string: {team}"


if __name__ == '__main__':
    config = Config()
    seeder = TeamSeeder(config)
    results = seeder.seed()
    print(results)
