# Slideshow Guide

314Sign includes a powerful slideshow system that lets you create multimedia presentations with images, videos, and text overlays. Perfect for advertising upcoming events, displaying promotional content, or showing informational slides when your business is closed.

## Quick Start

1. **Access the Editor**: Navigate to `http://your-pi.local/slideshows/` or use the Start page
2. **Create a Set**: Click "+ New Set" to create a slideshow collection
3. **Add Slides**: Click "+ Add Slide" and choose your content type
4. **Configure & Preview**: Edit slide settings and see live preview
5. **Save**: Click "💾 Save Slideshow"
6. **Schedule**: Use Rules editor to play slideshow during specific hours

## Slide Types

### Text Slides
Display formatted text with custom backgrounds.

**Features:**
- Markdown support (headings, bold, italic, lists)
- Color tags (`{r}`, `{y}`, `{g}`, `{b}`, `{o}`, `{p}`, `{w}`)
- Custom background images
- Font and size control
- Perfect for announcements, menus, specials

**Example:**
```markdown
# Weekend Special! 🎉

{y}50% OFF{/y} all appetizers

**Saturday & Sunday**
{g}5pm - 10pm
```

### Image Slides
Display photos with optional captions.

**Features:**
- Upload images directly from phone/computer
- Supported formats: JPG, PNG, GIF, WebP
- Optional caption with positioning (top/bottom/center)
- Automatic scaling to fit screen
- Great for event photos, product showcases, promotions

**Use Cases:**
- Featured dish photos
- Event announcements
- Staff highlights
- Promotional offers

### Video Slides
Play video content with full control.

**Features:**
- Supported formats: MP4, WebM, MOV
- Loop option for continuous play
- Mute control
- Auto-advance after video ends
- Ideal for commercials, tutorials, entertainment

**Settings:**
- **Duration 0**: Video plays to completion, then advances
- **Duration > 0**: Video stops after specified milliseconds
- **Loop**: Video repeats continuously during its duration
- **Muted**: Silent playback (recommended for background ambiance)

## Transitions

Choose from 6 transition effects:

- **Fade**: Smooth opacity transition (default, safest choice)
- **Slide Left**: New slide enters from right
- **Slide Right**: New slide enters from left
- **Slide Up**: New slide enters from bottom
- **Slide Down**: New slide enters from top
- **Zoom**: New slide scales from 80% to 100%
- **None**: Instant cut (no transition)

**Tip**: Use fade for most slides; use directional slides for emphasis.

## Creating a Slideshow Set

### Step 1: Plan Your Content
- Decide on your message and audience
- Gather images, videos, and text content
- Determine slide order and timing
- Choose appropriate durations (5-7 seconds per slide typical)

### Step 2: Create the Set
1. Click "+ New Set"
2. Enter a descriptive name (e.g., "summer-specials", "closed-hours-ads")
3. Add optional description
4. Click "Create"

### Step 3: Add Slides
For each slide:
1. Click "+ Add Slide"
2. Select slide type (Text/Image/Video)
3. Set duration (milliseconds): 5000 = 5 seconds
4. Choose transition effect
5. Fill in type-specific content:
   - **Text**: Background image, markdown content, font, size
   - **Image**: Upload or specify path, caption, caption position
   - **Video**: Upload or specify path, loop, muted
6. Click "Update Slide"
7. Preview appears on right

### Step 4: Reorder & Refine
- Use ↑↓ buttons to change slide order
- Edit any slide by clicking it
- Delete unwanted slides with × button
- Preview adjusts in real-time

### Step 5: Save
Click "💾 Save Slideshow" to persist changes.

### Step 6: Test
Click "▶️ Test" to preview slideshow in new window.

## Scheduling Slideshows

Use the Rules editor (`/rules/`) to automatically play slideshows:

1. **Open Rules Editor**: `http://your-pi.local/rules/`
2. **Create/Edit Rule**: Click "+ Add Rule" or edit existing
3. **Choose Content Type**: Select "Slideshow" from dropdown
4. **Enter Path**: `slideshows/sets/your-file.json`
5. **Set Schedule**: Days and time range
6. **Save Rules**: Click "Save Schedule"

**Example Use Case:**
```json
{
  "name": "Closed - Show Ads",
  "days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
  "startTime": "22:00",
  "endTime": "07:00",
  "slideshow": "slideshows/sets/upcoming-events.json"
}
```

When your business is closed (10pm-7am), the kiosk automatically plays your "upcoming-events" slideshow instead of menus.

## File Structure

```
slideshows/
├── index.html              # Editor interface
├── upload-media.php        # Media upload backend
├── media/                  # Uploaded images and videos
│   ├── slide_20251204_140532.jpg
│   ├── slide_20251204_141203.mp4
│   └── ...
└── sets/                   # Slideshow JSON files
    ├── example.json
    ├── upcoming-events.json
    ├── summer-specials.json
    └── ...
```

## JSON Structure

Each slideshow is a JSON file in `slideshows/sets/`:

```json
{
  "name": "Example Slideshow",
  "description": "Demo slideshow showing all features",
  "defaultDuration": 5000,
  "defaultTransition": "fade",
  "slides": [
    {
      "type": "text",
      "duration": 5000,
      "transition": "fade",
      "background": "../bg/default1.jpg",
      "content": "# Welcome!\n\nCheck out our **upcoming events**",
      "font": "Lato, sans-serif",
      "fontSize": 8
    },
    {
      "type": "image",
      "duration": 7000,
      "transition": "slide-left",
      "media": "media/slide_20251204_140532.jpg",
      "caption": "Amazing Event This Weekend!",
      "captionPosition": "bottom"
    },
    {
      "type": "video",
      "duration": 0,
      "transition": "fade",
      "media": "media/slide_20251204_141203.mp4",
      "loop": false,
      "muted": false
    }
  ]
}
```

**Field Reference:**

### Global Settings
- `name`: Slideshow display name
- `description`: Optional description
- `defaultDuration`: Default milliseconds per slide (overridden per-slide)
- `defaultTransition`: Default transition effect

### Slide Fields (All Types)
- `type`: "text", "image", or "video"
- `duration`: Milliseconds to show slide (0 = video length)
- `transition`: Transition effect

### Text Slide Fields
- `background`: Path to background image (or empty for black)
- `content`: Markdown text with color tags
- `font`: CSS font-family string
- `fontSize`: Percentage of viewport width (5-20)

### Image Slide Fields
- `media`: Path to image file
- `caption`: Optional caption text
- `captionPosition`: "top", "bottom", or "center"

### Video Slide Fields
- `media`: Path to video file
- `loop`: Boolean, repeat video
- `muted`: Boolean, silent playback

## Tips & Best Practices

### Timing
- **Read time**: 1 second per 3-4 words
- **Image slides**: 5-7 seconds typical
- **Video ads**: 15-30 seconds
- **Full slideshow**: 2-5 minutes total for looping

### Design
- **Contrast**: Ensure text readable on backgrounds
- **Consistency**: Use same fonts/colors across slides
- **Simplicity**: Less text = more impact
- **Resolution**: Use 1920x1080 or higher for full-screen images
- **File size**: Keep videos under 50MB for smooth playback

### Content
- **Call to action**: Tell viewers what to do next
- **Branding**: Include logo or business name
- **Urgency**: Highlight limited-time offers
- **Visuals**: Images outperform text-only slides
- **Rotation**: Update content weekly/monthly to stay fresh

### Technical
- **Test playback**: Always preview before going live
- **Video formats**: MP4 H.264 for best compatibility
- **Autoplay**: Videos may not autoplay with sound on some browsers
- **Network**: Local playback = no buffering issues
- **Fallback**: Keep a menu rule as fallback if slideshow fails

## Troubleshooting

### Slideshow Won't Play
- Check rule schedule matches current time
- Verify slideshow path in rules.json
- Confirm JSON file exists in `slideshows/sets/`
- Check browser console for errors

### Video Won't Play
- Ensure format is MP4, WebM, or MOV
- Try muting video (some browsers block autoplay with sound)
- Check file isn't corrupted
- Verify video codec compatibility (H.264 recommended)

### Upload Fails
- Check file size (50MB typical limit)
- Verify MIME type (images: jpg/png/gif/webp, videos: mp4/webm/mov)
- Check disk space on Pi
- Review `logs/slideshow-uploads.log`

### Transition Stutters
- Reduce image/video resolution
- Use fade instead of slide transitions
- Check Pi CPU usage
- Ensure adequate power supply

### Can't Save Changes
- Check WebDAV permissions
- Verify lighttpd is running
- Run `sudo bash permissions.sh`
- Check logs for 501 errors

## Advanced Usage

### Manual Slideshow Playback
Force slideshow without rules:
```
http://your-pi.local/?slideshow=slideshows/sets/example.json
```

### Multiple Slideshows
Create different sets for different occasions:
- `morning-announcements.json`: 7am-11am
- `lunch-specials.json`: 11am-2pm
- `happy-hour.json`: 4pm-7pm
- `closed-ads.json`: After hours

### Dynamic Content
Edit JSON files directly (advanced):
```bash
ssh pi@your-pi.local
sudo nano /var/www/html/slideshows/sets/your-file.json
```

### Backup Slideshows
```bash
sudo cp -r /var/www/html/slideshows/ ~/slideshows-backup-$(date +%Y%m%d)
```

## Examples

### Restaurant Use Cases
1. **Lunch Specials**: Text slides showing today's specials with prices
2. **Happy Hour**: Image slides of drinks + video of bartender making signature cocktail
3. **Closed Hours**: Slideshow advertising upcoming events, catering services, gift cards
4. **Weekend Brunch**: Photos of dishes with captions highlighting ingredients

### Other Industries
- **Retail**: Product photos, sales announcements, store hours
- **Office**: Meeting room schedules, company announcements, employee birthdays
- **Church**: Service times, upcoming events, volunteer opportunities, sermon series
- **School**: Daily announcements, lunch menu, sports schedules, club information
- **Gym**: Class schedules, trainer spotlights, membership promotions

---

## Need Help?

- Check main README.md for system overview
- See FORMATTING.md for text styling syntax
- Review troubleshooting.md for common issues
- File issues at: https://github.com/UnderhillForge/314Sign/issues
