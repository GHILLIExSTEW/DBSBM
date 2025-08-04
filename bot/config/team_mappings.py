"""Team name mappings for logo file naming.

This module has been refactored into a modular structure for better maintainability.
The original large file has been split into separate files by sport/league.
"""

# Import from the new modular structure
from .team_mappings import TEAM_MAPPINGS, normalize_team_name

# Re-export for backward compatibility
__all__ = ["TEAM_MAPPINGS", "normalize_team_name"]
