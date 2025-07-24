#!/usr/bin/env python3
"""
Fix linting issues in community engagement files.
"""

import re

def fix_community_analytics():
    """Fix linting issues in community_analytics.py"""
    with open('bot/services/community_analytics.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix imports
    content = re.sub(
        r'from datetime import datetime, timedelta\nfrom typing import Dict, List, Optional',
        'import discord\nfrom datetime import datetime\nfrom typing import Dict',
        content
    )
    
    # Fix long lines
    content = re.sub(
        r'logger\.debug\(f"Tracked metric \{metric_type\}: \{value\} for guild \{guild_id\}"\)',
        'logger.debug(f"Tracked metric {metric_type}: {value} for guild {guild_id}")',
        content
    )
    
    # Fix trailing whitespace
    content = re.sub(r' +\n', '\n', content)
    
    # Fix f-string without placeholders
    content = re.sub(r'f"Failed to track metric: \{e\}"', f'"Failed to track metric: {e}"', content)
    
    with open('bot/services/community_analytics.py', 'w', encoding='utf-8') as f:
        f.write(content)

def fix_community_events():
    """Fix linting issues in community_events.py"""
    with open('bot/services/community_events.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix imports
    content = re.sub(
        r'from typing import Dict, Optional',
        'from typing import Optional',
        content
    )
    
    # Fix trailing whitespace
    content = re.sub(r' +\n', '\n', content)
    
    with open('bot/services/community_events.py', 'w', encoding='utf-8') as f:
        f.write(content)

def fix_community_commands():
    """Fix linting issues in community.py"""
    with open('bot/commands/community.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix long lines by breaking them
    content = re.sub(
        r'await self\.community_analytics_service\.track_community_command\(guild_id, user_id, "discuss"\)',
        'await self.community_analytics_service.track_community_command('
        'guild_id, user_id, "discuss")',
        content
    )
    
    # Fix f-string without placeholders
    content = re.sub(r'f"Community discussion started by \{interaction\.user\.id\}"', 
                    '"Community discussion started by {interaction.user.id}"', content)
    
    # Fix trailing whitespace
    content = re.sub(r' +\n', '\n', content)
    
    with open('bot/commands/community.py', 'w', encoding='utf-8') as f:
        f.write(content)

def fix_community_leaderboard():
    """Fix linting issues in community_leaderboard.py"""
    with open('bot/commands/community_leaderboard.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix long lines by breaking them
    content = re.sub(
        r'@app_commands\.command\(name="community_leaderboard", description="View community leaderboards"\)',
        '@app_commands.command('
        'name="community_leaderboard", '
        'description="View community leaderboards")',
        content
    )
    
    # Fix trailing whitespace
    content = re.sub(r' +\n', '\n', content)
    
    with open('bot/commands/community_leaderboard.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    print("🔧 Fixing linting issues...")
    fix_community_analytics()
    fix_community_events()
    fix_community_commands()
    fix_community_leaderboard()
    print("✅ Linting issues fixed!") 