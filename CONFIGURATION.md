# Configuration Guide

This document provides detailed information about configuring OpenKJ Next Singer Display, including the new features for video backgrounds, sticky buttons, and OS-specific application data directories.

## Table of Contents

1. [Application Data Directory](#application-data-directory)
2. [Configuration Dialog](#configuration-dialog)
3. [Background Options](#background-options)
4. [Media File Management](#media-file-management)
5. [Troubleshooting](#troubleshooting)

## Application Data Directory

Starting with this version, all configuration files and media resources are stored in OS-specific application data directories. This ensures your configuration is stored in the proper location and persists across application updates.

### Directory Locations

- **Linux**: `~/.local/share/OpenKJ-Next-Singer-Display/`
- **macOS**: `~/Library/Application Support/OpenKJ-Next-Singer-Display/`
- **Windows**: `%APPDATA%\OpenKJ-Next-Singer-Display\`

### Directory Structure

```
OpenKJ-Next-Singer-Display/
├── config.json          # Application configuration
└── media/               # Copied media files
    ├── logo_*           # Logo images
    ├── bg_image_*       # Background images
    └── bg_video_*       # Background videos
```

The application automatically creates these directories on first run if they don't exist.

## Configuration Dialog

### Sticky Buttons

The configuration dialog now features sticky Save and Reset buttons at the bottom of the window. These buttons remain visible at all times, even when scrolling through the various settings tabs. This ensures you can always access these important functions without needing to scroll.

**Features:**
- **Save Configuration**: Saves all settings and closes the dialog
- **Reset to Default**: Restores all settings to default values (except database path)
- Both buttons are always visible in a fixed bar at the bottom
- No scrolling required to access buttons
- Visual separation from content with a styled button bar

### Settings Tabs

The configuration dialog is organized into four tabs:

1. **General**: Basic settings like venue name, title, database location
2. **Background**: Choose and configure your background type
3. **Fonts**: Customize fonts for all display elements
4. **Singer Change Overlay**: Configure the notification overlay

## Background Options

### 1. Solid Color

Choose a solid color for the background using the color picker.

**How to use:**
1. Select "Solid Color" from Background Type dropdown
2. Click "Choose Color" button
3. Select your desired color
4. Click "Save Configuration"

### 2. Image Background

Use an image file as the background. Supports animated GIFs.

**Supported formats:** PNG, JPG, JPEG, BMP, GIF

**How to use:**
1. Select "Image" from Background Type dropdown
2. Click "Browse" next to Background Image
3. Select your image file
4. The image will be automatically copied to the media directory
5. Click "Save Configuration"

**Features:**
- Images are stretched to fill the entire window
- Animated GIFs are supported and will loop
- Original file is copied to app directory for reliability

### 3. Video Background

Use a video file as an animated background.

**Supported formats:** MP4, AVI, MOV, MKV, WEBM, GIF

**Requirements:** PyQt6-Multimedia must be installed
```bash
pip install PyQt6-Multimedia
```

**How to use:**
1. Select "Video" from Background Type dropdown
2. Click "Browse" next to Background Video
3. Select your video file
4. The video will be automatically copied to the media directory
5. Click "Save Configuration"

**Video Features:**
- **Automatic 20-second limit**: Videos longer than 20 seconds will loop back to the start at the 20-second mark
- **Continuous looping**: Video plays in a seamless loop
- **Audio muted**: Only the visual component is used
- **Stretched to fit**: Video is scaled to fill the entire window
- **Automatic copy**: Video file is copied to app directory

**Best Practices:**
- Use videos optimized for your display resolution
- Keep video file sizes reasonable (under 50MB recommended)
- Test with your specific video format to ensure compatibility
- Consider using videos with smooth transitions for better looping

### 4. Gradient Background

Create a smooth color gradient.

**How to use:**
1. Select "Gradient" from Background Type dropdown
2. Click "Choose Start Color" and select your starting color
3. Click "Choose End Color" and select your ending color
4. Choose direction: Vertical, Horizontal, or Diagonal
5. Click "Save Configuration"

## Media File Management

### Automatic Copy on Selection

When you select a logo, background image, or background video through the configuration dialog, the application automatically:

1. Copies the selected file to the media directory in the app data directory
2. Renames the file with a prefix (`logo_`, `bg_image_`, or `bg_video_`)
3. Updates the configuration to point to the copied file
4. Shows a confirmation message

### Benefits

- **Reliability**: Files remain available even if original location changes
- **Portability**: All media is stored in one central location
- **Organization**: Media files are clearly named and separated by type
- **Safety**: Original files are not modified

### Manual Media Management

If you need to manually manage media files:

1. Navigate to the media directory for your OS (see above)
2. Files are named with prefixes:
   - `logo_*`: Logo images
   - `bg_image_*`: Background images
   - `bg_video_*`: Background videos
3. You can delete unused media files to save space
4. Don't delete files that are currently configured in the app

## Troubleshooting

### Video Background Not Playing

**Problem**: Video background is selected but not displaying

**Solutions:**
1. Check if PyQt6-Multimedia is installed:
   ```bash
   pip install PyQt6-Multimedia
   ```
2. Verify the video file exists in the media directory
3. Try a different video format (MP4 is most reliable)
4. Check console output for error messages
5. Ensure video file isn't corrupted

### Configuration Not Saving

**Problem**: Settings don't persist after closing the application

**Solutions:**
1. Check write permissions for the app data directory
2. Verify the directory exists and is accessible
3. Look for file system errors in console output
4. Try running the application with appropriate permissions

### Media Files Not Found

**Problem**: Background images/videos not displaying

**Solutions:**
1. Check that files were successfully copied to media directory
2. Verify files exist in the app data directory
3. Re-select the media file in settings to trigger a fresh copy
4. Check file format compatibility

### Buttons Not Visible in Config Dialog

**Problem**: Can't see Save or Reset buttons

**Solutions:**
1. This should no longer occur with sticky buttons
2. Try resizing the window
3. If issue persists, there may be a display scaling issue

### Video Plays With Audio

**Problem**: Video background has audio playing

**Solutions:**
1. This should not occur as audio is automatically muted
2. Check if another media player is running
3. Verify the correct media player instance is being used

## Advanced Configuration

### Manual Config File Editing

While not recommended, you can manually edit the `config.json` file if needed:

1. Close the application
2. Navigate to the app data directory
3. Edit `config.json` with a text editor
4. Ensure valid JSON syntax
5. Restart the application

**Example config.json structure:**
```json
{
    "db_path": "/path/to/openkj.sqlite",
    "num_singers": 5,
    "display_title": "Karaoke Singer Rotation",
    "venue_name": "Your Venue",
    "background_type": "video",
    "background_video": "/path/to/app/media/bg_video_yourfile.mp4",
    "background_color": "#161619",
    "background_image": null,
    ...
}
```

### Resetting to Defaults

To completely reset the application:

1. Close the application
2. Delete or rename the app data directory
3. Restart the application
4. Configure from scratch

Alternatively, use the "Reset to Default" button in the config dialog to reset settings while keeping your database path.

## Support

For additional help:
- Check the main [README.md](README.md)
- Review the [USER_GUIDE.md](USER_GUIDE.md)
- Check the [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for technical details
