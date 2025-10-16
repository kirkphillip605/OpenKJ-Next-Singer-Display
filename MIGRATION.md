# Migration Guide

## Upgrading to the New Configuration System

This version introduces a new configuration system that stores files in OS-specific application data directories. This guide helps you migrate from the old system.

## What Changed

**Old System:**
- Config stored in: `config.json.bak` in the application directory
- Media files referenced from their original locations

**New System:**
- Config stored in OS-specific app data directory:
  - Linux: `~/.local/share/OpenKJ-Next-Singer-Display/config.json`
  - macOS: `~/Library/Application Support/OpenKJ-Next-Singer-Display/config.json`
  - Windows: `%APPDATA%\OpenKJ-Next-Singer-Display\config.json`
- Media files (logos, images, videos) automatically copied to `media/` subdirectory

## Automatic Migration

The application will automatically:
1. Create the new directory structure on first run
2. Load default settings if no config exists

However, your old settings from `config.json.bak` are **not** automatically migrated.

## Manual Migration Steps

If you want to preserve your previous settings:

### Step 1: Locate Your Old Config File

Find `config.json.bak` or `config.json` in your application directory where `main.py` is located.

### Step 2: Run the Application Once

Run the new version once to create the directory structure:
```bash
python main.py
```

Close it after the config dialog appears.

### Step 3: Copy Your Settings

#### Option A: Copy the entire config file

1. Open your old `config.json.bak`
2. Copy the contents
3. Navigate to the new config location (see above for your OS)
4. Replace the contents of `config.json` with your old settings
5. Update the file paths for any media files (see Step 4)

#### Option B: Re-configure through the UI

Simply open the config dialog and re-enter your settings. This is the recommended approach as it will automatically:
- Copy media files to the new location
- Validate all settings
- Ensure compatibility with the new features

### Step 4: Update Media File Paths

If you manually copied the config file, you need to update media file paths:

**Old config might have:**
```json
{
    "logo_path": "/home/user/Downloads/logo.png",
    "background_image": "/home/user/Pictures/background.jpg"
}
```

**New approach:**
1. Open the application
2. Go to Settings
3. Re-select your logo file (it will be auto-copied to the media directory)
4. Re-select your background image/video (it will be auto-copied to the media directory)
5. Click "Save Configuration"

## Benefits of the New System

- **Reliability**: Media files won't break if you move/delete originals
- **Organization**: All app data in one central, OS-standard location
- **Portability**: Easier to backup or transfer your configuration
- **Safety**: Original files remain untouched
- **Standards**: Follows OS conventions for application data storage

## Preserving Your Old Setup

If you want to keep the old files as backup:

1. Copy `config.json.bak` to `config.json.bak.backup`
2. Copy any media files to a backup location
3. You can safely delete these after confirming the new setup works

## Reverting to Old Version

If you need to revert to a previous version:

1. Checkout the previous git commit
2. Your old `config.json.bak` should still be in the application directory
3. Note: You'll lose the new features (video backgrounds, sticky buttons, etc.)

## Fresh Start

If you prefer to start fresh with default settings:

Simply run the new version and configure everything from scratch. The old config file will be ignored but not deleted.

## Getting Help

If you encounter issues during migration:
1. Check the [CONFIGURATION.md](CONFIGURATION.md) guide
2. Review the [README.md](README.md) 
3. Open an issue on GitHub with details about your setup
