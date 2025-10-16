# Enhanced Settings Dialog - User Guide

This guide explains how to use the new enhanced settings dialog and all the customization features added to OpenKJ Next Singer Display.

## Opening the Settings Dialog

You can open the settings dialog in two ways:
1. Right-click anywhere on the display window and select "Show Config"
2. If no database is configured, the settings dialog opens automatically

## Settings Dialog Tabs

The settings dialog is organized into 4 tabs for easy navigation:

### 1. General Settings Tab

**Basic Settings:**
- **Rotation Title**: The main title displayed at the top of the rotation screen
- **Venue Name**: Your venue name (shown with "Welcome to...")
- **Number of Up Next**: How many upcoming singers to display (1-6)
- **Refresh Interval**: How often to check for database updates (5-20 seconds)
- **Accepting Requests**: Toggle whether you're currently accepting song requests

**Database Settings:**
- **OpenKJ Database**: Location of your OpenKJ database file
  - Click "Locate OpenKJ DB" to auto-detect the database on macOS/Windows
  - Or browse manually to select the file

**Logo Settings:**
- **Logo**: Your venue logo image file
  - Click "Browse" to select an image file (PNG, JPG, etc.)

### 2. Background Settings Tab

Choose how your display background looks:

**Background Type:**
- **Solid Color**: A single color background
  - Click "Choose Color" to pick any color
  - Preview shows the selected color

- **Image**: Use an image as the background
  - Click "Browse" to select an image file
  - Image will be centered and scaled appropriately

- **Gradient**: A smooth color transition
  - Click "Choose Start Color" for the beginning color
  - Click "Choose End Color" for the ending color
  - Select Direction:
    - **Vertical**: Top to bottom
    - **Horizontal**: Left to right
    - **Diagonal**: Top-left to bottom-right

### 3. Fonts Settings Tab

Customize the appearance of each text element individually:

**Available Elements:**
1. **Display Title** - The main rotation heading
2. **Venue Name** - Your venue's welcome message
3. **Current Singer Name** - The performer currently on stage
4. **Current Song** - The song currently being performed
5. **Up Next Singer Name** - Names of upcoming performers
6. **Up Next Song** - Songs that will be performed next

**For Each Element:**
- **Font Family**: Choose from all installed system fonts
- **Font Size**: Set the text size (8-144 pixels)
- **Font Style**: 
  - Check **Bold** for bold text
  - Check **Italic** for italic text

### 4. Singer Change Overlay Tab

Configure the notification that appears when the current singer changes:

**Settings:**
- **Enable Singer Change Overlay**: Turn the feature on/off
- **Overlay Duration**: How long to show the overlay (5-60 seconds, default 20)

**How It Works:**
When enabled, the overlay:
1. Detects when the current singer changes to a new performer
2. Shows a full-screen notification with:
   - "The next performer is" (centered at top)
   - New singer's name (larger, centered below)
   - Song title and artist
3. Automatically hides after the configured duration
4. Returns to the normal rotation display

This gives everyone in the venue a clear, prominent notification of who's performing next.

## Buttons

**Save Configuration:**
- Saves all your settings to the configuration file
- Immediately applies the changes to the display window
- Settings persist across application restarts

**Reset to Default:**
- Restores all settings to their original default values
- Does NOT reset the database path
- Useful if you want to start over with a clean configuration
- Shows a confirmation dialog before resetting

## Tips and Best Practices

### Background Selection
- **Solid colors** work best for readability
- **Dark backgrounds** (#161619 is the default) provide good contrast
- If using an **image**, choose one that's not too busy
- **Gradients** can add visual interest without being distracting

### Font Settings
- Keep fonts **readable** from a distance
- **Larger fonts** (40-60px) for current singer and title
- **Smaller fonts** (20-30px) for up next list
- **Bold** text helps important information stand out
- Use **similar font families** for consistency

### Singer Change Overlay
- Default 20 seconds is usually sufficient
- Increase duration for larger venues where people need more time to see
- Decrease for smaller venues or faster-paced shows
- Disable if you prefer a more minimal display

### Performance
- Shorter refresh intervals (5 seconds) provide more responsive updates
- Longer intervals (10-20 seconds) reduce system load
- 5-10 seconds is recommended for most uses

## Troubleshooting

**Settings not saving:**
- Check file permissions on config.json.bak
- Ensure the application has write access to its directory

**Fonts not displaying correctly:**
- Verify the selected font is installed on your system
- Try a common font like Arial or Times New Roman
- Restart the application after changing fonts

**Background image not showing:**
- Check the image file exists at the specified path
- Supported formats: PNG, JPG, JPEG, BMP, GIF
- Try a different image file

**Overlay not appearing:**
- Ensure "Enable Singer Change Overlay" is checked
- Verify singers are actually changing in the rotation
- Check that the database is being updated

## Configuration File

All settings are stored in `config.json.bak` in the application directory. The file includes:
- All general settings
- Background configuration
- Font settings for each element
- Overlay preferences

You can manually edit this file if needed, but use the settings dialog for the best experience.

## Keyboard Shortcuts

While viewing the display:
- **Right-click**: Open context menu
- **F11**: Toggle fullscreen (on some systems)
- Context menu options:
  - Make Fullscreen / Make Windowed
  - Show Config
  - Close

## Default Values

For reference, here are the default settings:

**Background:**
- Type: Solid Color
- Color: #161619 (dark gray)

**Fonts:**
- Display Title: Arial 48px Bold
- Venue Name: Arial 32px Bold
- Current Singer: Arial 38px
- Current Song: Arial 24px
- Up Next Singer: Arial 30px Bold
- Up Next Song: Arial 20px Italic

**Overlay:**
- Enabled: Yes
- Duration: 20 seconds

**General:**
- Number of Up Next: 5
- Refresh Interval: 5 seconds
- Accepting Requests: Yes
