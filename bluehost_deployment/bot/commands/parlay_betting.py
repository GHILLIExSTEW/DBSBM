"""Parlay betting functionality - Modular implementation.

This module has been refactored into a modular structure for better maintainability.
The original large file has been split into separate modules:

- parlay_betting/commands.py - Main command and cog
- parlay_betting/workflow.py - Workflow view and logic
- parlay_betting/ui_components.py - UI components and buttons
- parlay_betting/modals.py - Modal dialogs
- parlay_betting/constants.py - Constants and configuration
- parlay_betting/utils.py - Utility functions
"""

# Import from the modular structure
from .parlay_betting import ParlayCog, setup

# Re-export for backward compatibility
__all__ = ["ParlayCog", "setup"]
