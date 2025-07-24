# Wikipedia Player Image Downloader

This collection of scripts downloads player images from Wikipedia for darts, tennis, and golf. The images are saved in PNG format with consistent sizing (200x200 pixels) and organized in the same directory structure as your existing player images.

## 📁 Directory Structure

Images will be saved in the following structure:
```
static/logos/players/
├── tennis/
│   ├── ATP/
│   │   ├── novak_djokovic.webp
│   │   ├── carlos_alcaraz.webp
│   │   └── ...
│   └── WTA/
│       ├── iga_swiatek.webp
│       ├── aryna_sabalenka.webp
│       └── ...
├── darts/
│   ├── PDC/
│   │   ├── luke_humphries.webp
│   │   ├── michael_van_gerwen.webp
│   │   └── ...
│   └── BDO/
│       ├── glen_durrant.webp
│       ├── scott_waites.webp
│       └── ...
└── golf/
    ├── PGA/
    │   ├── scottie_scheffler.webp
    │   ├── rory_mcilroy.webp
    │   └── ...
    └── LPGA/
        ├── lilia_vu.webp
        ├── celine_boutier.webp
        └── ...
```

## 🚀 Usage

### Download All Sports
```bash
python scripts/download_all_player_images.py
```

### Download Specific Sport
```bash
# Download only tennis players
python scripts/download_all_player_images.py --sport tennis

# Download only darts players
python scripts/download_all_player_images.py --sport darts

# Download only golf players
python scripts/download_all_player_images.py --sport golf
```

### Skip Existing Images
```bash
# Skip sports that already have downloaded images
python scripts/download_all_player_images.py --skip-existing
```

### Individual Sport Scripts
You can also run individual sport scripts directly:

```bash
# Tennis players
python scripts/download_tennis_players.py

# Darts players
python scripts/download_darts_players.py

# Golf players
python scripts/download_golf_players.py
```

## 📋 Player Lists

The scripts include curated lists of top players for each sport:

### Tennis
- **ATP**: Novak Djokovic, Carlos Alcaraz, Daniil Medvedev, Jannik Sinner, etc.
- **WTA**: Iga Świątek, Aryna Sabalenka, Coco Gauff, Elena Rybakina, etc.

### Darts
- **PDC**: Luke Humphries, Michael van Gerwen, Michael Smith, Nathan Aspinall, etc.
- **BDO**: Glen Durrant, Scott Waites, Scott Mitchell, Mark McGeeney, etc.

### Golf
- **PGA**: Scottie Scheffler, Rory McIlroy, Jon Rahm, Viktor Hovland, etc.
- **LPGA**: Lilia Vu, Celine Boutier, Ruoning Yin, Atthaya Thitikul, etc.

## ⚙️ Configuration

### Player Lists
You can modify the player lists by editing the JSON file:
```bash
# Edit player lists
nano scripts/player_lists.json
```

### Image Settings
- **Size**: 200x200 pixels (same as your existing logo size)
- **Format**: PNG with RGBA support
- **Optimization**: Enabled for smaller file sizes

### Rate Limiting
- **Delay**: 1 second between requests to be respectful to Wikipedia's servers
- **Timeout**: 10-15 seconds for API requests

## 📊 Results

Each script generates a results file with detailed information:

- `tennis_download_results.json`
- `darts_download_results.json`
- `golf_download_results.json`

These files contain:
- Successfully downloaded players
- Failed downloads
- Players not found on Wikipedia
- Wikipedia page URLs for each player

## 🔧 Troubleshooting

### Common Issues

1. **Network Errors**
   - Check your internet connection
   - Wikipedia may be temporarily unavailable
   - Try running the script again

2. **Players Not Found**
   - Some players may not have Wikipedia pages
   - Names might be spelled differently
   - Check the results file for details

3. **Permission Errors**
   - Ensure you have write permissions to the `static/logos/players/` directory
   - Create the directory structure if it doesn't exist

### Logs
All scripts generate detailed logs:
- Console output shows real-time progress
- Log files are saved in the scripts directory
- Check logs for specific error messages

## 📝 Adding New Players

To add new players to the download lists:

1. Edit the appropriate script file (e.g., `download_tennis_players.py`)
2. Add player names to the `tennis_players` dictionary
3. Run the script again

Example:
```python
self.tennis_players = {
    'ATP': [
        'Novak Djokovic',
        'Carlos Alcaraz',
        # Add new player here
        'New Player Name',
        # ... rest of list
    ]
}
```

## ⚠️ Important Notes

- **Rate Limiting**: The scripts include delays to be respectful to Wikipedia's servers
- **Image Quality**: Images are resized to 200x200 pixels for consistency
- **File Names**: Special characters are removed and spaces replaced with underscores
- **Overwriting**: Existing images will be overwritten if you run the script again
- **Legal**: Images are downloaded from Wikipedia under their respective licenses

## 🎯 Success Rates

Typical success rates:
- **Tennis**: ~85-90% (most top players have Wikipedia pages)
- **Darts**: ~70-80% (some players may not have pages)
- **Golf**: ~80-85% (most PGA/LPGA players have pages)

Players not found will be listed in the results file for manual review.

## 📞 Support

If you encounter issues:
1. Check the log files for error messages
2. Verify your internet connection
3. Ensure all required Python packages are installed
4. Check that the directory structure exists and is writable

Required packages:
- `requests`
- `Pillow` (PIL)
- `pathlib` (built-in)
- `urllib` (built-in)
