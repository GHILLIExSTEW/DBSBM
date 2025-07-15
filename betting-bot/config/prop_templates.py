"""
Prop Type Templates Configuration
Defines available prop types for each league with labels, placeholders, and validation rules.
"""

from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class PropTemplate:
    """Template for a specific prop type."""
    label: str
    placeholder: str
    unit: str
    min_value: float = 0.0
    max_value: float = 999.9
    decimal_places: int = 1
    validation_regex: str = r'^\d+(\.\d+)?$'

# Prop type templates for each league
PROP_TEMPLATES: Dict[str, Dict[str, PropTemplate]] = {
    "NBA": {
        "points": PropTemplate(
            label="Points",
            placeholder="Over/Under X.X Points",
            unit="points",
            min_value=0.0,
            max_value=100.0,
            decimal_places=1
        ),
        "rebounds": PropTemplate(
            label="Rebounds",
            placeholder="Over/Under X.X Rebounds",
            unit="rebounds",
            min_value=0.0,
            max_value=30.0,
            decimal_places=1
        ),
        "assists": PropTemplate(
            label="Assists",
            placeholder="Over/Under X.X Assists",
            unit="assists",
            min_value=0.0,
            max_value=20.0,
            decimal_places=1
        ),
        "threes": PropTemplate(
            label="3-Pointers Made",
            placeholder="Over/Under X.X 3-Pointers",
            unit="3-pointers",
            min_value=0.0,
            max_value=15.0,
            decimal_places=1
        ),
        "steals": PropTemplate(
            label="Steals",
            placeholder="Over/Under X.X Steals",
            unit="steals",
            min_value=0.0,
            max_value=10.0,
            decimal_places=1
        ),
        "blocks": PropTemplate(
            label="Blocks",
            placeholder="Over/Under X.X Blocks",
            unit="blocks",
            min_value=0.0,
            max_value=10.0,
            decimal_places=1
        ),
        "turnovers": PropTemplate(
            label="Turnovers",
            placeholder="Over/Under X.X Turnovers",
            unit="turnovers",
            min_value=0.0,
            max_value=10.0,
            decimal_places=1
        ),
        "minutes": PropTemplate(
            label="Minutes Played",
            placeholder="Over/Under X.X Minutes",
            unit="minutes",
            min_value=0.0,
            max_value=48.0,
            decimal_places=1
        )
    },
    
    "NFL": {
        "passing_yards": PropTemplate(
            label="Passing Yards",
            placeholder="Over/Under XXX.X Yards",
            unit="yards",
            min_value=0.0,
            max_value=600.0,
            decimal_places=1
        ),
        "rushing_yards": PropTemplate(
            label="Rushing Yards",
            placeholder="Over/Under XX.X Yards",
            unit="yards",
            min_value=0.0,
            max_value=200.0,
            decimal_places=1
        ),
        "receiving_yards": PropTemplate(
            label="Receiving Yards",
            placeholder="Over/Under XXX.X Yards",
            unit="yards",
            min_value=0.0,
            max_value=300.0,
            decimal_places=1
        ),
        "receptions": PropTemplate(
            label="Receptions",
            placeholder="Over/Under X.X Receptions",
            unit="receptions",
            min_value=0.0,
            max_value=20.0,
            decimal_places=1
        ),
        "touchdowns": PropTemplate(
            label="Touchdowns",
            placeholder="Over/Under X.X TDs",
            unit="touchdowns",
            min_value=0.0,
            max_value=5.0,
            decimal_places=1
        ),
        "passing_touchdowns": PropTemplate(
            label="Passing TDs",
            placeholder="Over/Under X.X Passing TDs",
            unit="touchdowns",
            min_value=0.0,
            max_value=5.0,
            decimal_places=1
        ),
        "rushing_touchdowns": PropTemplate(
            label="Rushing TDs",
            placeholder="Over/Under X.X Rushing TDs",
            unit="touchdowns",
            min_value=0.0,
            max_value=3.0,
            decimal_places=1
        ),
        "interceptions": PropTemplate(
            label="Interceptions",
            placeholder="Over/Under X.X INTs",
            unit="interceptions",
            min_value=0.0,
            max_value=5.0,
            decimal_places=1
        )
    },
    
    "MLB": {
        "hits": PropTemplate(
            label="Hits",
            placeholder="Over/Under X.X Hits",
            unit="hits",
            min_value=0.0,
            max_value=6.0,
            decimal_places=1
        ),
        "home_runs": PropTemplate(
            label="Home Runs",
            placeholder="Over/Under X.X Home Runs",
            unit="home runs",
            min_value=0.0,
            max_value=3.0,
            decimal_places=1
        ),
        "rbis": PropTemplate(
            label="RBIs",
            placeholder="Over/Under X.X RBIs",
            unit="RBIs",
            min_value=0.0,
            max_value=8.0,
            decimal_places=1
        ),
        "runs": PropTemplate(
            label="Runs",
            placeholder="Over/Under X.X Runs",
            unit="runs",
            min_value=0.0,
            max_value=5.0,
            decimal_places=1
        ),
        "strikeouts": PropTemplate(
            label="Strikeouts",
            placeholder="Over/Under X.X Strikeouts",
            unit="strikeouts",
            min_value=0.0,
            max_value=15.0,
            decimal_places=1
        ),
        "walks": PropTemplate(
            label="Walks",
            placeholder="Over/Under X.X Walks",
            unit="walks",
            min_value=0.0,
            max_value=5.0,
            decimal_places=1
        ),
        "innings_pitched": PropTemplate(
            label="Innings Pitched",
            placeholder="Over/Under X.X Innings",
            unit="innings",
            min_value=0.0,
            max_value=9.0,
            decimal_places=1
        )
    },
    
    "NHL": {
        "goals": PropTemplate(
            label="Goals",
            placeholder="Over/Under X.X Goals",
            unit="goals",
            min_value=0.0,
            max_value=5.0,
            decimal_places=1
        ),
        "assists": PropTemplate(
            label="Assists",
            placeholder="Over/Under X.X Assists",
            unit="assists",
            min_value=0.0,
            max_value=5.0,
            decimal_places=1
        ),
        "points": PropTemplate(
            label="Points",
            placeholder="Over/Under X.X Points",
            unit="points",
            min_value=0.0,
            max_value=8.0,
            decimal_places=1
        ),
        "shots": PropTemplate(
            label="Shots on Goal",
            placeholder="Over/Under X.X Shots",
            unit="shots",
            min_value=0.0,
            max_value=10.0,
            decimal_places=1
        ),
        "saves": PropTemplate(
            label="Saves",
            placeholder="Over/Under X.X Saves",
            unit="saves",
            min_value=0.0,
            max_value=50.0,
            decimal_places=1
        ),
        "penalty_minutes": PropTemplate(
            label="Penalty Minutes",
            placeholder="Over/Under X.X PIM",
            unit="minutes",
            min_value=0.0,
            max_value=10.0,
            decimal_places=1
        )
    }
}

# League-specific prop type groupings
LEAGUE_PROP_GROUPS: Dict[str, Dict[str, List[str]]] = {
    "NBA": {
        "Scoring": ["points", "threes"],
        "Rebounding": ["rebounds"],
        "Playmaking": ["assists", "turnovers"],
        "Defense": ["steals", "blocks"],
        "Playing Time": ["minutes"]
    },
    "NFL": {
        "Passing": ["passing_yards", "passing_touchdowns", "interceptions"],
        "Rushing": ["rushing_yards", "rushing_touchdowns"],
        "Receiving": ["receiving_yards", "receptions"],
        "Scoring": ["touchdowns"]
    },
    "MLB": {
        "Batting": ["hits", "home_runs", "rbis", "runs", "walks"],
        "Pitching": ["strikeouts", "innings_pitched"]
    },
    "NHL": {
        "Scoring": ["goals", "assists", "points"],
        "Shooting": ["shots"],
        "Goaltending": ["saves"],
        "Penalties": ["penalty_minutes"]
    }
}

def get_prop_templates_for_league(league: str) -> Dict[str, PropTemplate]:
    """Get prop templates for a specific league."""
    return PROP_TEMPLATES.get(league.upper(), {})

def get_prop_groups_for_league(league: str) -> Dict[str, List[str]]:
    """Get prop type groups for a specific league."""
    return LEAGUE_PROP_GROUPS.get(league.upper(), {})

def validate_prop_value(league: str, prop_type: str, value: float) -> bool:
    """Validate a prop value against the template constraints."""
    templates = get_prop_templates_for_league(league)
    if prop_type not in templates:
        return False
    
    template = templates[prop_type]
    return template.min_value <= value <= template.max_value

def format_prop_line(league: str, prop_type: str, value: float) -> str:
    """Format a prop line value according to the template."""
    templates = get_prop_templates_for_league(league)
    if prop_type not in templates:
        return str(value)
    
    template = templates[prop_type]
    return f"{value:.{template.decimal_places}f} {template.unit}" 