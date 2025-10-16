# Quick Reference: New Features

## Sticky Buttons in Config Dialog

**What**: Save and Reset buttons stay visible at the bottom  
**Benefit**: No more scrolling to find buttons  
**How to use**: Just scroll through settings - buttons are always there!

---

## Config File Location

### Where is my config stored?

- **Linux**: `~/.local/share/OpenKJ-Next-Singer-Display/`
- **macOS**: `~/Library/Application Support/OpenKJ-Next-Singer-Display/`
- **Windows**: `%APPDATA%\OpenKJ-Next-Singer-Display\`

The app creates this automatically - you don't need to do anything!

---

## Video Backgrounds

### Quick Start

1. Open Settings (right-click → Show Config)
2. Go to "Background" tab
3. Select "Video" from dropdown
4. Click "Browse" and pick your video
5. Click "Save Configuration"

### Requirements

```bash
pip install PyQt6-Multimedia
```

### Video Features

- ✓ Loops continuously
- ✓ Limited to 20 seconds
- ✓ No audio (video only)
- ✓ Stretches to fit window
- ✓ Auto-copied to app directory

### Supported Formats

MP4, AVI, MOV, MKV, WEBM, GIF

---

## Background Options Quick Guide

| Type | What | When to Use |
|------|------|-------------|
| **Solid Color** | Single color | Clean, simple look |
| **Image** | Static image or GIF | Brand logo, theme image |
| **Video** | Moving video | Dynamic, eye-catching |
| **Gradient** | Color blend | Smooth, professional |

---

## Media Files

### What happens when I select a file?

1. File is **copied** to app directory
2. Original file can be moved/deleted safely
3. App uses the copied version

### Where are copied files?

In the `media/` folder inside your config directory:
```
config directory/
└── media/
    ├── logo_yourlogo.png
    ├── bg_image_yourimage.jpg
    └── bg_video_yourvideo.mp4
```

---

## Troubleshooting

### Video not playing?

1. Check if PyQt6-Multimedia is installed
2. Try a different video format (MP4 works best)
3. Check console for error messages

### Buttons not visible?

This shouldn't happen anymore! If it does:
- Try resizing the window
- Report as a bug

### Config not saving?

- Check folder permissions
- See [CONFIGURATION.md](CONFIGURATION.md) for details

---

## Upgrading from Old Version?

See [MIGRATION.md](MIGRATION.md) for step-by-step guide.

**Quick version**: Just re-configure through the Settings dialog. The app will copy files to the new location.

---

## Getting Help

- **Full Guide**: [CONFIGURATION.md](CONFIGURATION.md)
- **Migration**: [MIGRATION.md](MIGRATION.md)
- **Technical**: [IMPLEMENTATION_DETAILS.md](IMPLEMENTATION_DETAILS.md)
- **General**: [README.md](README.md)
