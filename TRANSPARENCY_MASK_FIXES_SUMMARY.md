# Transparency Mask Fixes Summary

## Problem
The Discord bot was experiencing "bad transparency mask" errors when generating bet slip images. This was caused by improper handling of image transparency when pasting logos and icons onto bet slip images.

## Root Cause
The issue occurred when using PIL's `image.paste()` method with the same image as both the source and the mask parameter. This can cause transparency mask errors when the image format or alpha channel isn't properly handled.

## Files Fixed

### 1. `bot/utils/game_line_image_generator.py`
- **Fixed paste operations for:**
  - League logo paste operation (line ~339)
  - Team logo paste operations in all sections (manual, darts/tennis/golf/f1, normal sports)
  - Lock icon paste operations (lines ~574, ~584)

### 2. `bot/utils/player_prop_image_generator.py`
- **Fixed paste operations for:**
  - League logo paste operation (line ~303)
  - Team logo paste operation (line ~327)
  - Player image paste operation (line ~338)
  - Lock icon paste operations (lines ~447, ~457)

### 3. `bot/utils/parlay_bet_image_generator.py`
- **Fixed paste operations for:**
  - Team logo paste operations in game line bets (line ~218)
  - Opponent logo paste operations (line ~238)
  - Team logo paste operations in player prop bets (line ~272)
  - Player image paste operations (line ~293)
  - Fallback logo paste operations (line ~300)
  - Lock icon paste operations (lines ~439, ~446)

## Solution Applied
For each paste operation, the fix involved:

1. **Checking image mode**: Verify if the image is in RGBA mode
2. **Extracting alpha channel**: Use `image.split()[-1]` to get the alpha channel as the mask
3. **Proper paste operation**: Use the alpha channel as the mask instead of the image itself
4. **Fallback handling**: If the image is not in RGBA mode, paste without a mask

### Code Pattern Applied:
```python
# Before (problematic):
image.paste(logo, (x, y), logo)

# After (fixed):
if logo.mode == 'RGBA':
    alpha = logo.split()[-1]
    image.paste(logo, (x, y), alpha)
else:
    image.paste(logo, (x, y))
```

## Additional Improvements
- **Lock icon handling**: Added proper RGBA conversion for lock icons before resizing
- **Consistent pattern**: Applied the same fix pattern across all image generators
- **Error prevention**: Added fallback handling for non-RGBA images

## Testing
These fixes should resolve the "bad transparency mask" errors that were occurring during:
- Game line bet slip generation
- Player prop bet slip generation  
- Parlay bet slip generation
- Preview image generation

## Impact
- **Eliminates transparency mask errors** in bet slip image generation
- **Maintains visual quality** of logos and icons with proper transparency
- **Improves reliability** of the betting workflow
- **No breaking changes** to existing functionality

## Files Not Affected
- `bot/utils/enhanced_player_prop_image_generator.py` - No paste operations found
- `bot/utils/parlay_image_generator.py` - No paste operations found

## Next Steps
1. Test bet slip generation for all bet types
2. Verify that logos and icons display correctly with transparency
3. Monitor logs for any remaining transparency-related errors 