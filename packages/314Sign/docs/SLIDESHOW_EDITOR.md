# Slideshow Editor Guide

## 🎬 Advanced Slideshow System with reveal.js

The 314Sign platform now includes a modern drag-and-drop slideshow editor powered by reveal.js.

## Features

### 🎨 Slide Types
- **Text Slides**: Title, subtitle, and content text
- **Image Slides**: Full-screen images with optional captions
- **Video Slides**: Auto-playing looping videos
- **Weather Widget**: Real-time weather data with 3-day forecast
- **Time & Date**: Live clock display
- **Markdown**: Rich content with markdown syntax

### ⚙️ Slide Properties
Each slide can be configured with:
- **Duration**: How long the slide displays (in milliseconds)
- **Transition**: Animation effect (none, fade, slide, convex, concave, zoom)
- **Background**: Color or image URL
- **Vertical**: Make this slide appear below the previous one (↓ navigation)
- **Type-specific settings**: Media URLs, weather location, time format, etc.

### 🎯 Navigation Modes
- **Horizontal slides**: Navigate left → right (or auto-advance)
- **Vertical slides**: Check "Vertical Slide" to nest below previous slide
  - Press ↓ to go down into details
  - Press ↑ to go back up
  - Great for grouping related content

### 🎯 Interface Overview

#### Left Sidebar - Slide Templates
Click or drag slide types to add them to your presentation:
- 📝 Text Slide
- 🖼️ Image
- 🎥 Video
- 🌤️ Weather
- 🕐 Time & Date
- 📄 Markdown

#### Center - Slide List
Your slides appear here in order. You can:
- **Drag to reorder** slides
- **Click to select** and edit
- **Duplicate** slides with the 📋 button
- **Delete** slides with the 🗑️ button

#### Right Sidebar - Properties Panel
Edit the selected slide's properties:
- Duration and transition settings
- Background color/image
- Type-specific content (text, media URLs, etc.)

### 🎮 Editor Controls

**Top Bar:**
- 📂 **Load** - Open existing slideshows
- � **Export HTML** - Download standalone HTML file
- 👁️ **Preview** - Open slideshow in new window
- 💾 **Save** - Save your slideshow

**Keyboard Shortcuts:**
- `Ctrl/Cmd + S` - Save slideshow
- `Ctrl/Cmd + E` - Export to HTML
- `Delete` - Delete selected slide

## Weather API Setup

The weather widget uses OpenWeatherMap API. To enable real weather data:

1. Get a free API key from https://openweathermap.org/api
2. Set environment variable:
   ```bash
   export OPENWEATHER_API_KEY="your-api-key-here"
   ```
3. Restart the server

Without an API key, the weather widget will display mock data.

## Creating Your First Slideshow

1. **Open the Editor**
   Navigate to: `/slideshows/editor.html`

2. **Add Slides**
   Click on slide types in the left sidebar to add them

3. **Configure Each Slide**
   - Click a slide to select it
   - Edit properties in the right panel
   - Set duration (5000ms = 5 seconds)
   - Choose transition effect

4. **Reorder Slides**
   Drag slides up or down to reorder

5. **Save Your Work**
   - Click "💾 Save" button
   - Enter a unique name (e.g., "my-slideshow")
   - Add optional description

6. **Preview**
   Click "👁️ Preview" to see your slideshow in action

## Exporting Slideshows

### Export to HTML
Create a standalone HTML file that can be shared or presented anywhere:

1. Click the "📦 Export HTML" button (or press `Ctrl+E`)
2. The file will download automatically
3. Open the HTML file in any modern browser
4. Works offline - no server required!

**What's included in the export:**
- Complete reveal.js presentation
- All slide content and styling
- Auto-play functionality
- Keyboard navigation (arrow keys)
- CDN-linked reveal.js libraries (requires internet on first load)

**Note:** Weather widgets and dynamic content will show placeholders in exported files since they require API connections.

## Assigning Slideshows to Displays

1. Navigate to **Screens Configuration** (`/screens/`)
2. Select a display (HDMI-1 or HDMI-2)
3. Set mode to "Slideshow"
4. Choose your slideshow from the dropdown
5. Click "Save Configuration"

## API Endpoints

### Slideshows
- `GET /api/slideshows` - List all slideshows
- `GET /api/slideshows/:name` - Get specific slideshow
- `POST /api/slideshows` - Create/update slideshow
- `DELETE /api/slideshows/:name` - Delete slideshow

### Weather
- `GET /api/weather?location=auto&units=F` - Get weather data
  - `location`: 'auto' or city name
  - `units`: 'F' (Fahrenheit) or 'C' (Celsius)

## Slideshow Data Format

```json
{
  "name": "my-slideshow",
  "description": "Example slideshow",
  "defaultDuration": 5000,
  "defaultTransition": "slide",
  "slides": [
    {
      "type": "text",
      "duration": 5000,
      "transition": "fade",
      "background": "#000000",
      "vertical": false,
      "title": "Welcome",
      "subtitle": "Restaurant Specials",
      "content": "Check out today's deals!"
    },
    {
      "type": "text",
      "duration": 3000,
      "transition": "slide",
      "background": "#1a1a2e",
      "vertical": true,
      "title": "Lunch Special",
      "content": "Available 11am-2pm"
    },
    {
      "type": "image",
      "duration": 7000,
      "transition": "slide",
      "background": "#000000",
      "vertical": false,
      "media": "/media/food-photo.jpg",
      "caption": "Fresh Daily Specials"
    },
    {
      "type": "weather",
      "duration": 8000,
      "transition": "convex",
      "background": "#1a1a2e",
      "vertical": false,
      "location": "auto",
      "units": "F"
    }
  ]
}
```

Note: Slides with `"vertical": true` will appear below the previous slide when navigating.

## Tips & Best Practices

1. **Slide Duration**: 5-10 seconds per slide works well for most content
2. **Transitions**: Use consistent transitions for a professional look
3. **Vertical Slides**: Great for organizing content hierarchically
   - Use horizontal slides for main topics
   - Use vertical slides for details/sub-topics
   - Example: Main menu → Details below → Next main menu →
4. **Weather Updates**: Weather data refreshes every 10 minutes
5. **Image Optimization**: Use AVIF or WebP formats for best performance
6. **Video Format**: MP4 with H.264 codec works best
7. **Background Colors**: Dark backgrounds (#000000, #1a1a2e) are easier on the eyes
8. **Export for Sharing**: Use HTML export to share presentations with others

## Troubleshooting

### Slideshow Not Showing
- Check that display is set to "Slideshow" mode in Screens Configuration
- Verify slideshow name matches exactly
- Preview slideshow in editor to test

### Weather Not Loading
- Check browser console for API errors
- Verify OPENWEATHER_API_KEY environment variable is set
- Check internet connection

### Images Not Displaying
- Verify image URLs are correct
- Images must be accessible from the browser
- Use absolute URLs or paths relative to web root

## Files

- **Editor**: `/packages/314Sign/slideshows/editor.html`
- **Player**: `/packages/314Sign/slideshows/reveal-player.html`
- **API Route**: `/packages/314Sign/src/routes/weather.ts`
- **Slideshow API**: `/packages/314Sign/src/routes/slideshows.ts`

---

For more information, visit the [314Sign Documentation](../docs/).
