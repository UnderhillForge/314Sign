# Slideshow Media Directory

This directory contains media files (images and videos) used in slideshows.

## Purpose
- Centralized storage for slideshow media assets
- Separate from the main `/media` directory which is used for system assets (logos, backgrounds)
- Used by both the slideshow editor and the SVG editor

## Supported File Types
- **Images**: JPG, PNG, GIF, WebP, SVG, AVIF
- **Videos**: MP4, WebM, MOV (QuickTime)

## Upload Limits
- **Images**: Max 10 MB per file
- **Videos**: Max 150 MB per file

## API Endpoints
- **List media**: `GET /api/slideshows/media/list`
- **Upload media**: `POST /slideshows/upload-media.php`
- **Access media**: `GET /slideshow-media/{filename}`

## Usage in SVG Editor
The SVG editor dropdown menu provides:
- **Load from Server**: Browse and load SVG files from this directory
- **Import Image**: Import images from desktop into the current SVG

## Directory Structure
```
slideshow-media/
├── README.md (this file)
└── [uploaded media files]
```

## File Naming Convention
Uploaded files are automatically renamed with the pattern:
`slide_YYYYMMDD_HHMMSS_[random].[ext]`

This ensures:
- No filename collisions
- Chronological sorting
- Security (original filenames not exposed)

## Permissions
This directory should be writable by the web server user (typically `www-data` or `pi`).
Run `./permissions.sh` from the parent directory to set correct permissions.
