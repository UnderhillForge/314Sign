# 🚀 Hybrid Markup + Image Display System

## Overview

This is a revolutionary hybrid approach that combines the **reliability of image-based displays** with the **flexibility of dynamic content** through Lightweight Markup Script (LMS) files.

## Core Concept

Instead of sending large rendered images for every content update, send **lightweight markup files** that reference cached background images and specify text overlays, dynamic content, and styling.

## Architecture

```
Content Creation → LMS Markup → Intelligent Rendering → Display
                    ↓
            Background Cache
```

## Key Advantages

- **95% Bandwidth Reduction**: Only markup updates instead of full images
- **Dynamic Content**: Real-time clocks, weather, custom variables
- **Rich Formatting**: Fonts, colors, positioning, effects, animations
- **Caching**: Background images stored locally, only downloaded once
- **Progressive Enhancement**: Start with images, add markup overlays

## Current Implementation

### ✅ Completed (Phase 1)

- **LMS Parser** (`lms/parser.py`): Full JSON parser with validation
- **Example Files**: Restaurant menu and classroom schedule demonstrations
- **Directory Structure**: Organized codebase for hybrid components

### 🔄 Next Steps (Phase 2)

- **LMS Renderer**: Convert LMS files to rendered images
- **Dynamic Content Engine**: Handle real-time data (time, weather, etc.)
- **Font Management**: Load and cache fonts for rendering
- **Integration**: Merge with existing image display system

### 📋 Future Phases

- **Animation Engine**: Smooth transitions and effects
- **Content Pipeline**: Kiosk-side LMS generation tools
- **Remote Sync**: Intelligent LMS file distribution
- **Python Kiosk**: Multi-display support for main kiosk

## Example LMS File

```json
{
  "version": "1.0",
  "background": {
    "image": "restaurant-bg.jpg",
    "brightness": 0.9
  },
  "overlays": [
    {
      "type": "text",
      "content": "Daily Specials",
      "font": "BebasNeue",
      "size": 48,
      "color": "#FFD700",
      "position": {"x": 100, "y": 50}
    },
    {
      "type": "dynamic",
      "content": "current_time",
      "format": "HH:MM",
      "position": {"x": 1600, "y": 50}
    }
  ]
}
```

## Bandwidth Comparison

| Method | Update Size | Frequency | Daily Bandwidth |
|--------|-------------|-----------|-----------------|
| **Full Images** | 2MB each | Every 5 min | ~576MB/day |
| **Hybrid LMS** | 2KB markup | Every 5 min | ~0.5MB/day |
| **Savings** | **99.9% reduction** | Same updates | **99.9% less bandwidth** |

## Use Cases

- **Restaurants**: Menu updates with real-time specials
- **Schools**: Class schedules with current time/class info
- **Offices**: Directory displays with weather/clock
- **Retail**: Promotions with dynamic pricing
- **Events**: Venue info with countdown timers

## Development Status

This is an **experimental feature branch** kept separate from the main production codebase until thoroughly tested and proven stable.

### Branch: `feature/hybrid-markup-system`

**Ready to continue development tomorrow!** 🎯

---

*This hybrid approach represents the future of reliable, efficient digital signage.*