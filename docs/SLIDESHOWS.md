# Slideshow Guide

Create multimedia presentations with images, videos, and text overlays.

## Creating Slideshows

### 1. Access Slideshow Editor
Navigate to: `http://your-pi.local/slideshows/`

### 2. Create New Slideshow Set
- Click "Create New Set"
- Enter a descriptive name
- Choose display duration per slide

### 3. Add Media Files
```bash
# Supported formats:
# Images: JPG, PNG, GIF, AVIF
# Videos: MP4, WebM (recommended)
# Maximum file size: 50MB per file
```

### 4. Configure Slides
For each slide, you can set:
- **Display duration** (seconds)
- **Transition effect** (fade, slide, zoom)
- **Text overlay** (optional)
- **Background music** (optional)

## Slide Configuration

### Text Overlays
```
Title: Welcome to Our Restaurant!
Subtitle: Fresh ingredients, great service
Footer: Open 7 days a week
```

### Transition Effects
- **Fade**: Smooth crossfade between slides
- **Slide**: Horizontal sliding transition
- **Zoom**: Scale and zoom effect
- **None**: Instant transition

### Timing Options
- **Auto-advance**: Automatic progression
- **Manual control**: Click to advance
- **Loop mode**: Continuous playback
- **Random order**: Shuffle slide order

## Advanced Features

### Scheduled Playback
Combine slideshows with rules for time-based display:
- Breakfast slideshow (6-11 AM)
- Lunch slideshow (11 AM-3 PM)
- Dinner slideshow (5-10 PM)
- Happy hour promotions

### Remote Display Integration
Slideshows work with remote viewers:
- Mirror main display
- Show different content per location
- Synchronized or independent timing

## File Management

### Upload Process
1. Click "Upload Media"
2. Select files from device
3. Wait for upload completion
4. Files appear in media library

### Organization
- Media stored in `slideshows/media/`
- Automatic thumbnail generation
- File type validation
- Duplicate detection

### Cleanup
- Unused files can be deleted
- Automatic cleanup of orphaned files
- Bulk media management

## Best Practices

### Performance
- Optimize image sizes (<2MB per image)
- Use MP4 for video (most compatible)
- Limit text overlays to 2-3 lines
- Test on target display hardware

### Content
- Consistent branding across slides
- High contrast text for readability
- Appropriate file formats for web
- Regular content updates

### Timing
- 8-15 seconds per slide (typical)
- Shorter for busy environments
- Longer for detailed information
- Test timing with actual audience

## Troubleshooting

### Slideshow Won't Load
- Check file permissions: `./permissions.sh /var/www/html`
- Verify media files exist
- Check browser console for errors
- Clear browser cache

### Videos Don't Play
- Ensure MP4/WebM format
- Check file corruption
- Verify browser video support
- Test with smaller file sizes

### Timing Issues
- Check PM2 logs: `pm2 logs 314sign`
- Verify slideshow configuration
- Test with different browsers
- Check system performance

## API Integration

### Programmatic Control
```bash
# Get slideshow sets
GET /api/slideshows

# Upload media
POST /api/upload/media

# Create slideshow set
POST /api/slideshows

# Update set configuration
PUT /api/slideshows/:id
```

### JSON Configuration
```json
{
  "name": "Daily Specials",
  "slides": [
    {
      "media": "pasta.jpg",
      "duration": 10,
      "transition": "fade",
      "text": {
        "title": "Pasta Special",
        "subtitle": "$12.95",
        "footer": "Limited time offer"
      }
    }
  ],
  "loop": true,
  "random": false
}
```

## Integration with Rules

### Time-Based Display
Create rules that automatically switch to slideshows:

```json
{
  "name": "Happy Hour",
  "timeStart": "16:00",
  "timeEnd": "18:00",
  "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
  "action": "slideshow",
  "slideshowId": "happy-hour-drinks"
}
```

### Menu Integration
Slideshows can complement menu displays:
- Product photography
- Chef specials
- Seasonal promotions
- Behind-the-scenes content

## Performance Optimization

### File Optimization
- Resize images to display resolution
- Compress videos for web delivery
- Use appropriate quality settings
- Batch process media files

### System Resources
- Monitor CPU usage during playback
- Limit concurrent slideshows
- Use efficient transition effects
- Regular maintenance and cleanup

## Accessibility

### Text Alternatives
- Provide text descriptions for images
- Use high contrast colors
- Ensure readable font sizes
- Test with screen readers

### Timing Controls
- Respect user timing preferences
- Provide pause/play controls
- Allow adjustable timing
- Avoid flashing content
