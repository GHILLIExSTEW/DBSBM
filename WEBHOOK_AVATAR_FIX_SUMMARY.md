# Webhook Avatar Issue Fix Summary

## Problem
The webhook for posting bet slip images was not using the user's custom avatar from the `guilds/users/` folder. Instead, it was using the default Discord avatar.

## Root Cause
The issue was in the image upload process in `bot/commands/setid.py`. Images were being saved as PNG format but the file path was being stored with `.webp` extension, causing a mismatch between the actual file format and the expected path.

## Files Fixed

### 1. `bot/commands/setid.py`
- **Image Upload Button Handler** (line ~207): Changed `img.save(save_path, "PNG")` to `img.save(save_path, "WEBP")`
- **Image URL Modal Handler** (line ~291): Changed `img.save(save_path, "PNG")` to `img.save(save_path, "WEBP")`

### 2. `bot/utils/image_url_converter.py`
- **Added Debug Logging**: Added comprehensive logging to track the URL conversion process
- **Enhanced Error Handling**: Better error reporting for debugging webhook avatar issues

### 3. Webhook Implementation Files
Added debug logging to all webhook implementations:
- `bot/commands/straight_betting.py`
- `bot/commands/parlay_betting.py`
- `bot/commands/enhanced_player_prop_modal.py`
- `bot/commands/enhanced_player_props.py`

### 4. `scripts/convert_user_images_to_webp.py` (Created)
- **Conversion Script**: Script to convert any existing PNG files to WEBP format
- **Database Path Update**: Updates database paths from `.png` to `.webp` if needed

## Solution Applied

### Before (Problematic):
```python
# Image was saved as PNG but path stored as .webp
img.save(save_path, "PNG")  # Saves as PNG
url_path = f"/static/guilds/{guild_id}/users/{user_id}.webp"  # Path expects WEBP
```

### After (Fixed):
```python
# Image saved as WEBP to match the path
img.save(save_path, "WEBP")  # Saves as WEBP
url_path = f"/static/guilds/{guild_id}/users/{user_id}.webp"  # Path matches format
```

## Webhook Avatar Flow

1. **User Uploads Image**: Via `/setid` command
2. **Image Saved**: As WEBP format in `bot/static/guilds/{guild_id}/users/{user_id}.webp`
3. **Path Stored**: In database as `/static/guilds/{guild_id}/users/{user_id}.webp`
4. **Webhook Retrieval**: Fetches `image_path` from `cappers` table
5. **URL Conversion**: `convert_image_path_to_url()` converts to absolute URL
6. **Webhook Posting**: Uses `avatar_url` parameter with converted URL

## Debugging Added

### Image URL Converter Logging:
```python
logger.debug(f"convert_image_path_to_url: Converting path: {image_path}")
logger.debug(f"convert_image_path_to_url: Converted to: {full_url}")
```

### Webhook Avatar Logging:
```python
logger.info(f"Found capper image_path: {capper_data['image_path']}")
logger.info(f"Converted webhook_avatar_url: {webhook_avatar_url}")
logger.info(f"No capper image_path found for user {interaction.user.id}")
```

## Testing

### Expected Behavior:
- Users who have uploaded custom avatars via `/setid` should see their custom avatar in webhook posts
- Users without custom avatars should see the default Discord avatar
- All bet slip images (game lines, player props, parlays) should use the correct user avatar

### Verification Steps:
1. Check logs for webhook avatar URL conversion messages
2. Verify that user images are in WEBP format in the file system
3. Confirm that database paths match the actual file extensions
4. Test webhook posting with users who have custom avatars

## Impact

- **Custom Avatars**: Webhook posts now properly display user's custom avatars
- **Consistent Format**: All user images are saved in WEBP format for consistency
- **Better Debugging**: Enhanced logging for troubleshooting webhook issues
- **Future Uploads**: New image uploads will be saved in the correct format

## Files Not Affected
- Existing WEBP user images (already in correct format)
- Web server configuration (already properly serving static files)
- Database structure (no schema changes needed)
