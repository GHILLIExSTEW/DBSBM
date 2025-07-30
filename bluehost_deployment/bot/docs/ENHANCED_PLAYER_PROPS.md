# Enhanced Player Props System

## 🎯 Overview

The Enhanced Player Props System provides a comprehensive upgrade to your existing player prop betting functionality with improved search, validation, and user experience.

## 🚀 Key Improvements

### 1. **Smart Player Search**
- **Fuzzy Matching**: Find players even with typos or partial names
- **Autocomplete**: Real-time suggestions as you type
- **Popular Players**: Quick access to frequently bet players
- **League Filtering**: Search within specific leagues

### 2. **Prop Type Templates**
- **League-Specific**: Different prop types for NBA, NFL, MLB, NHL
- **Validation**: Automatic validation of line values and bet amounts
- **Grouped Categories**: Props organized by category (Scoring, Defense, etc.)
- **Icons**: Visual indicators for each prop type

### 3. **Enhanced Database Schema**
- **Dedicated Tables**: Separate tables for props, performance, and search cache
- **Performance Indexes**: Optimized queries for fast searches
- **Data Migration**: Automatic migration of existing player prop data

### 4. **Improved Image Generation**
- **Modern Design**: Clean, professional bet slip images
- **Performance Stats**: Show player's recent performance vs the line
- **Visual Indicators**: Icons and colors for over/under bets
- **Comparison Charts**: Visual representation of recent games

## 📁 File Structure

```
betting-bot/
├── config/
│   └── prop_templates.py          # Prop type configurations
├── data/
│   └── player_props_schema.sql    # Database schema
├── services/
│   └── player_search_service.py   # Player search functionality
├── commands/
│   └── enhanced_player_prop_modal.py  # Enhanced modal
├── utils/
│   └── enhanced_player_prop_image_generator.py  # Image generation
├── scripts/
│   └── migrate_player_props.py    # Database migration
└── docs/
    └── ENHANCED_PLAYER_PROPS.md   # This documentation
```

## 🛠️ Installation & Setup

### 1. **Install Dependencies**

Add the new dependencies to your `requirements.txt`:

```bash
# Install enhanced dependencies
pip install -r requirements_enhanced.txt
```

### 2. **Run Database Migration**

```bash
# Run the migration script
python scripts/migrate_player_props.py
```

### 3. **Update Your Bot Code**

Replace your existing player prop modal with the enhanced version:

```python
# Old way
from commands.player_prop_modal import PlayerPropModal

# New way
from commands.enhanced_player_prop_modal import setup_enhanced_player_prop

# In your command handler
view = await setup_enhanced_player_prop(bot, db_manager, league, game_id, team_name)
await interaction.response.send_message("Create a Player Prop Bet", view=view)
```

## 🎮 Usage Guide

### **For Users**

1. **Search Players**: Type player name and get instant suggestions
2. **Select Prop Type**: Choose from league-specific prop types
3. **Enter Line Value**: System validates realistic values
4. **Choose Direction**: Over or Under the line
5. **Set Bet Amount**: Enter your wager
6. **Submit**: Get a beautiful bet slip image

### **For Developers**

#### **Adding New Prop Types**

Edit `config/prop_templates.py`:

```python
"NFL": {
    "new_prop": PropTemplate(
        label="New Prop",
        placeholder="Over/Under X.X New Prop",
        unit="units",
        min_value=0.0,
        max_value=100.0,
        decimal_places=1
    )
}
```

#### **Customizing Search**

Modify `services/player_search_service.py`:

```python
# Adjust search sensitivity
results = await player_search_service.search_players(
    query, league, limit=10, min_confidence=70.0
)
```

#### **Customizing Images**

Edit `utils/enhanced_player_prop_image_generator.py`:

```python
# Add new prop type icons
self.prop_icons['new_prop'] = '🎯'
```

## 🔧 Configuration

### **Prop Type Templates**

Each league has its own prop types with validation rules:

```python
# Example: NBA Points
"points": PropTemplate(
    label="Points",
    placeholder="Over/Under X.X Points",
    unit="points",
    min_value=0.0,
    max_value=100.0,
    decimal_places=1
)
```

### **Search Settings**

Configure search behavior in `PlayerSearchService`:

```python
# Cache TTL (seconds)
self._cache_ttl = 300

# Minimum confidence for search results
min_confidence: float = 60.0
```

### **Image Generation**

Customize image appearance:

```python
# Color scheme
self.colors = {
    'background': '#1a1a1a',
    'card_bg': '#2d2d2d',
    'text_primary': '#ffffff',
    'accent': '#4CAF50',
    'over_green': '#4CAF50',
    'under_red': '#f44336'
}
```

## 📊 Database Schema

### **New Tables**

1. **`player_props`**: Available prop lines
2. **`player_performance`**: Historical performance data
3. **`player_search_cache`**: Search optimization

### **Enhanced `bets` Table**

Added columns for better prop tracking:
- `player_prop_type`: Type of prop (points, rebounds, etc.)
- `player_prop_line`: The line value
- `player_prop_direction`: Over or under
- `player_prop_result`: Actual result

## 🎨 Image Features

### **Enhanced Bet Slips**

- **Player Images**: Circular player photos
- **Team Logos**: High-quality team branding
- **Prop Icons**: Visual indicators for prop types
- **Performance Stats**: Recent game data
- **Modern Design**: Clean, professional appearance

### **Comparison Charts**

- **Recent Games**: Bar chart of last 10 games
- **Line Reference**: Visual line showing the prop value
- **Color Coding**: Green for over, red for under

## 🔍 Search Features

### **Fuzzy Matching**

Uses `rapidfuzz` library for intelligent matching:
- **Partial Matches**: Find "LeBron" when searching "LeBron James"
- **Typos**: Handle "Steph Curry" vs "Steph Currie"
- **Abbreviations**: Match "KD" to "Kevin Durant"

### **Autocomplete**

Real-time suggestions as users type:
- **Popular Players**: Most frequently bet players first
- **League Filtering**: Only show relevant players
- **Usage Tracking**: Learn from user behavior

### **Performance Optimization**

- **In-Memory Cache**: 5-minute TTL for recent searches
- **Database Indexes**: Optimized for fast queries
- **Usage Analytics**: Track popular players

## 🧪 Testing

### **Unit Tests**

```bash
# Run player prop tests
python -m pytest tests/test_player_props.py -v
```

### **Integration Tests**

```bash
# Test search functionality
python -m pytest tests/test_player_search.py -v

# Test image generation
python -m pytest tests/test_image_generation.py -v
```

## 🚀 Performance Tips

### **Database Optimization**

1. **Indexes**: All search queries are indexed
2. **Caching**: In-memory cache for frequent searches
3. **Connection Pooling**: Efficient database connections

### **Image Generation**

1. **Async Processing**: Non-blocking image creation
2. **Caching**: Cache generated images
3. **Optimization**: Compressed PNG output

### **Search Performance**

1. **Fuzzy Matching**: Fast string matching algorithms
2. **Result Limiting**: Limit results to prevent overload
3. **Background Updates**: Update cache in background

## 🔮 Future Enhancements

### **Planned Features**

1. **Live Odds**: Real-time prop line updates
2. **Performance Analytics**: Advanced player statistics
3. **Social Features**: Share bets and results
4. **Mobile Optimization**: Better mobile experience

### **API Integration**

1. **Player Stats APIs**: Real-time performance data
2. **Odds APIs**: Live prop line feeds
3. **Image APIs**: Player photo services

## 🐛 Troubleshooting

### **Common Issues**

1. **Search Not Working**
   - Check database connection
   - Verify migration completed
   - Check player_search_cache table

2. **Images Not Generating**
   - Verify PIL/Pillow installation
   - Check font files exist
   - Verify asset paths

3. **Validation Errors**
   - Check prop type exists in templates
   - Verify line value within range
   - Check bet amount format

### **Debug Mode**

Enable debug logging:

```python
import logging
logging.getLogger('player_props').setLevel(logging.DEBUG)
```

## 📞 Support

For issues or questions:
1. Check this documentation
2. Review error logs
3. Test with minimal configuration
4. Create issue with detailed error information

---

**🎉 Enjoy your enhanced player props system!**
