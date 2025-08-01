# Migration 019: Guild Customization Tables

## Overview
This migration creates tables for guild customization features, allowing Discord servers to customize their betting bot pages with custom branding, images, and content.

## Tables Created

### 1. `guild_customization`
Stores customization settings for each guild:
- **Page Settings**: Title, description, welcome message
- **Branding**: Primary, secondary, and accent colors
- **Images**: Hero, logo, and background image paths
- **Content**: About, features, and rules sections
- **Social Links**: Discord invite, website, Twitter URLs
- **Display Options**: Toggle for leaderboard, recent bets, stats visibility
- **Access Control**: Public/private access setting

### 2. `guild_images`
Manages custom images uploaded by guilds:
- **Image Types**: Hero, logo, background, gallery
- **File Management**: Original filename, file size, MIME type
- **Metadata**: Alt text, display order, upload tracking
- **Status**: Active/inactive image management

### 3. `guild_page_templates`
Predefined page templates for quick setup:
- **Modern**: Gradient design with animations
- **Classic**: Clean, traditional layout
- **Gaming**: Dark theme for gaming communities

## Default Templates
The migration automatically inserts three default templates:
1. **Modern** (default): `{"layout": "hero-stats-leaderboard", "style": "modern", "animations": true}`
2. **Classic**: `{"layout": "header-content-sidebar", "style": "classic", "animations": false}`
3. **Gaming**: `{"layout": "full-width", "style": "gaming", "animations": true}`

## Running the Migration

### Option 1: Python Script (Cross-platform)
```bash
python scripts/run_migration_019.py
```

### Option 2: PowerShell Script (Windows)
```powershell
.\scripts\run_migration_019.ps1
```

### Option 3: Bash Script (Linux/Mac)
```bash
./scripts/run_migration_019.sh
```

## Prerequisites
- MySQL database connection
- `mysql-connector-python` package installed
- Environment variables set:
  - `MYSQL_HOST`
  - `MYSQL_USER`
  - `MYSQL_PASSWORD`
  - `MYSQL_DB`
  - `MYSQL_PORT` (optional, defaults to 3306)

## Environment Variables
The script uses the following environment variables for database connection:
- `MYSQL_HOST`: Database host (default: localhost)
- `MYSQL_USER`: Database username (default: dbsbm)
- `MYSQL_PASSWORD`: Database password (default: empty)
- `MYSQL_DB`: Database name (default: dbsbm)
- `MYSQL_PORT`: Database port (default: 3306)

## Dependencies
- `mysql-connector-python`: For MySQL database connectivity
- Python 3.6+: For script execution

## Rollback
To rollback this migration, you can drop the created tables:
```sql
DROP TABLE IF EXISTS guild_customization;
DROP TABLE IF EXISTS guild_images;
DROP TABLE IF EXISTS guild_page_templates;
```

## Usage Examples
After running the migration, guilds can customize their pages:

```sql
-- Set custom branding for a guild
INSERT INTO guild_customization (guild_id, page_title, primary_color, welcome_message)
VALUES (123456789, 'My Betting Community', '#FF6B6B', 'Welcome to our betting community!');

-- Upload a custom logo
INSERT INTO guild_images (guild_id, image_type, filename, original_filename, file_size, mime_type)
VALUES (123456789, 'logo', 'guild_123456789_logo.webp', 'my_logo.png', 102400, 'image/webp');
```

## Indexes
The migration creates several indexes for optimal performance:
- `idx_guild_customization_guild_id`: For guild-specific queries
- `idx_guild_customization_public_access`: For public page filtering
- `idx_guild_images_guild_id`: For guild image queries
- `idx_guild_images_image_type`: For image type filtering
- `idx_guild_images_is_active`: For active image filtering
- `idx_guild_page_templates_is_default`: For default template queries 