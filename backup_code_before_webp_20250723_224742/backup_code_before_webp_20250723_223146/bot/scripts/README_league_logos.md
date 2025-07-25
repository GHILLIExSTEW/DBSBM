# League Logo Collection Scripts

This collection of scripts helps download and collect league logos for Golf, Tennis, and F1 to work with the same logo system as Darts.

## 📁 Directory Structure

Logos will be saved in the following structure:
```
static/logos/leagues/
├── TENNIS/
│   ├── ATP/
│   │   ├── atp_tour.png
│   │   └── atp.png
│   └── WTA/
│       ├── wta_tour.png
│       └── wta.png
├── GOLF/
│   ├── PGA/
│   │   ├── pga_tour.png
│   │   └── pga.png
│   ├── LPGA/
│   │   ├── lpga_tour.png
│   │   └── lpga.png
│   ├── EUROPEAN_TOUR/
│   │   ├── european_tour.png
│   │   └── european_tour.png
│   ├── LIV_GOLF/
│   │   ├── liv_golf.png
│   │   └── liv_golf.png
│   ├── KORN_FERRY/
│   │   └── korn_ferry.png
│   ├── CHAMPIONS_TOUR/
│   │   └── champions_tour.png
│   ├── RYDER_CUP/
│   │   └── ryder_cup.png
│   ├── PRESIDENTS_CUP/
│   │   └── presidents_cup.png
│   ├── SOLHEIM_CUP/
│   │   └── solheim_cup.png
│   └── OLYMPIC_GOLF/
│       └── olympic_golf.png
└── RACING/
    └── FORMULA1/
        ├── formula_1.png
        └── formula1.png
```

## 🚀 Usage

### Option 1: API-Based Logo Downloader

The `download_league_logos.py` script attempts to download logos from the API-Sports API:

```bash
# Run the API-based logo downloader
python scripts/download_league_logos.py
```

**Features:**
- Downloads logos from API-Sports API
- Handles rate limiting and retries
- Automatically resizes images to 200x200 pixels
- Saves in PNG format with transparency
- Skips existing logos

**Requirements:**
- Valid API_KEY in environment variables
- API-Sports subscription with access to tennis, golf, and formula-1 APIs

### Option 2: Manual Logo Collector

The `manual_logo_collector.py` script downloads logos from predefined sources (Wikipedia, etc.):

```bash
# Run the manual logo collector
python scripts/manual_logo_collector.py
```

**Features:**
- Downloads logos from Wikipedia and other public sources
- No API key required
- Handles SVG to PNG conversion
- Automatically resizes images
- Skips existing logos

### Option 3: Combined Approach

Run both scripts to maximize logo coverage:

```bash
# First try API-based download
python scripts/download_league_logos.py

# Then fill in any missing logos with manual collection
python scripts/manual_logo_collector.py
```

## 📋 Supported Leagues

### Tennis
- **ATP Tour** - Men's professional tennis
- **WTA Tour** - Women's professional tennis

### Golf
- **PGA Tour** - Men's professional golf
- **LPGA Tour** - Women's professional golf
- **European Tour** - European professional golf
- **LIV Golf** - LIV Golf League
- **Korn Ferry Tour** - PGA Tour developmental circuit
- **Champions Tour** - Senior professional golf
- **Ryder Cup** - Team competition (US vs Europe)
- **Presidents Cup** - Team competition (US vs International)
- **Solheim Cup** - Women's team competition
- **Olympic Golf** - Olympic golf competition

### Formula 1
- **Formula 1** - Formula One World Championship

## 🔧 Configuration

### Environment Variables

For the API-based downloader, ensure you have:
```bash
API_KEY=your_api_sports_key_here
```

### Customizing Logo Sources

To add more logo sources to the manual collector, edit the `MANUAL_LOGO_URLS` dictionary in `manual_logo_collector.py`:

```python
MANUAL_LOGO_URLS = {
    "sport_name": {
        "LEAGUE_CODE": {
            "url": "https://example.com/logo.png",
            "name": "League Display Name"
        }
    }
}
```

## 📊 Logging

Both scripts provide detailed logging:

- **Console output** - Real-time progress and status
- **Log files** - Detailed logs saved to:
  - `league_logo_download.log` (API downloader)
  - Console only (Manual collector)

## 🎯 Naming Conventions

The scripts follow the same naming conventions as the existing Darts system:

1. **Normalized Name Pattern**: `{normalized_league_name}.png`
   - Example: `pga_tour.png`, `formula_1.png`

2. **League Code Pattern**: `{league_code.lower()}.png`
   - Example: `pga.png`, `formula1.png`

The asset loader will try both patterns to find the appropriate logo.

## 🔍 Troubleshooting

### Common Issues

1. **API Key Issues**
   ```
   ERROR: API_KEY not found in environment variables!
   ```
   - Ensure your `.env` file contains a valid API_KEY
   - Check that your API key has access to the required sports

2. **Rate Limiting**
   ```
   WARNING: Rate limited, waiting X seconds...
   ```
   - The script automatically handles rate limiting
   - Increase `REQUEST_DELAY_SECONDS` if needed

3. **Missing Logos**
   ```
   WARNING: Could not find league info for League Name
   ```
   - Try the manual collector as a fallback
   - Check if the league name matches exactly

4. **Image Processing Errors**
   ```
   ERROR: Invalid image format for League Name
   ```
   - The script will try alternative sources
   - Check the source URL manually

### Manual Logo Placement

If scripts fail, you can manually place logo files:

1. Create the appropriate directory structure
2. Save logo as PNG format (200x200px recommended)
3. Use the correct naming convention
4. Ensure transparency is preserved

## 📈 Success Metrics

After running the scripts, you should see:
- Logos saved in the correct directory structure
- Consistent naming across all sports
- Proper integration with the asset loader system
- Logos displaying correctly in the application

## 🔄 Integration

The collected logos will automatically work with:
- `AssetLoader.load_league_logo()` method
- Image generation for bet slips
- League display in the UI
- All existing logo functionality

## 📝 Notes

- All logos are automatically resized to 200x200 pixels maximum
- Images are saved in PNG format with transparency
- The system supports both API-based and manual logo collection
- Existing logos are preserved and not overwritten
- The scripts are designed to be run multiple times safely
