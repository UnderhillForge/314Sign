# 314Sign Copilot Instructions

## Architecture Overview
314Sign is a **zero-backend, static-file kiosk** system: lighttpd serves HTML/JS/CSS, edits happen via HTTP PUT/WebDAV directly to files in `/var/www/html`, and no database or REST API exists. The entire state lives in JSON files and plain text menus.

## Deployment Pipeline
- **Installation**: `setup-kiosk.sh` provisions lighttpd + PHP-CGI, clones the repo, rsyncs web assets to `/var/www/html`, configures WebDAV, and generates QR codes for mobile access. **Critical**: When adding/moving files, update this script's rsync section and the WebDAV config block to maintain consistency on fresh installs.
- **Permissions**: `permissions.sh` sets www-data ownership and ensures editable files (config.json, rules.json, index.html, menus/*.txt, editor pages) have 664 permissions while directories like `bg/`, `menus/`, and `logs/` get 775 for write access. Run after file changes.
- **Update workflow**: Changes sync via rsync; no build step exists. Test locally with `php -S` or lighttpd + WebDAV before deploying.

## Core Files & Data Flow

### `index.html` (TV/kiosk display)
- **Boot sequence**: Fetches `config.json` once at load → applies `bg`, `font`, `fontScalePercent`, `pollIntervalMs/Seconds/legacy` → starts polling selected menu file (default: `menus/dinner.txt`, persisted in localStorage).
- **Polling mechanism**: ETag-aware fetch every `pollIntervalMs` (default 3000ms); compares ETag header → if changed, parses menu as Markdown via marked.js → renders with color tag replacements (`{r}` → red span, `{y}` → yellow, etc. — see `FORMATTING.md`). Falls back to text comparison if ETag missing.
- **Auto-switching**: Checks `rules.json` every 60s → if a rule matches current day/time, calls `switchMenu()` to load new menu file and update localStorage.
- **Hard reload**: Full page reload every 5 minutes to catch background/font changes that don't affect menu files.
- **Remote control**: Polls `demo-command.txt` every 2 seconds for remote commands from `demo/index.html`. Commands like `menu:breakfast` or `slideshow:example` trigger instant view changes without page reload.
- **Gotcha**: `index.html` never writes config—it's read-only. `design/index.html` writes `bg`/`font`, `edit/index.html` writes `fontScalePercent`. All must tolerate missing keys gracefully.

### `edit/index.html` (mobile menu editor)
- **Dynamic menu tabs**: Automatically populates tabs from `rules.json` using each rule's `name` property as the button label. Extracts unique menu files from all rules, making the editor agnostic to use case (food menus, event schedules, ad rotations, etc.). Falls back to breakfast/lunch/dinner/closed if rules.json missing. Each tab PUTs to its own file using `../menus/{name}.txt` relative paths via localStorage.
- **Active rule display**: Shows which menu is currently active on kiosk based on rules.json schedule. Updates menu tab styling and displays status bar with active rule name and time range. Refreshes every 60s.
- **Font scale slider**: Adjusts `fontScalePercent` (5-20%) in `config.json` via PUT; `index.html` reads this to set `clamp()` font sizes dynamically. Merges into existing config to avoid clobbering `bg`/`font`.
- **Menu history**: Auto-saves to `save-menu-history.php` on every save, creates one file per day in `history/` directory (format: MENUNAME_YYYY-MM-DD_DayOfWeek.txt). Modal displays 7-day history via `get-menu-history.php` with restore capability. History files auto-prune after 7 days. Multiple saves on same day overwrite the daily file.
- **Reload trigger**: Button writes timestamp to `reload.txt`; kiosk checks every 10s and reloads on change. Also auto-triggers on menu save.
- **Markdown toolbar**: Inserts formatting (`**bold**`, color tags like `{r}`, list bullets, alignment tags, size overrides) and shows live preview via marked.js.
- **Emoji toolbar**: Quick-insert buttons for 🍔🍕🍗🥗🍰☕🍺🍷.
- **Toast UX**: Shows success/error notifications using `.toast` CSS + `showToast()` helper; all editor pages follow this pattern (aria-live for accessibility).

### `design/index.html` (style configurator)
- **Background picker**: Fetches image list from `bg/index.php` → renders thumbnails → on selection, PUTs `config.json` with new `bg` filename (prefer file references over data URLs for caching).
- **Upload flow**: User picks image → validates client-side → POSTs FormData to `upload-bg.php` → receives `{filename: "uploaded_YYYYMMDD_HHMMSS.ext"}` → saves filename to `config.json` → adds thumb to grid.
- **Font dropdown**: Populated from `config.json.availableFonts` map (keys = display names, values = CSS font-family strings).
- **Header controls**: Text input for custom header text, size slider (5-20%) for header font size.
- **Brightness slider**: Adjusts background brightness (20-150%, default 100%) saved as `bgBrightness` (0.2-1.5) in config.json. Applied via CSS filter on body element.
- **Clock settings**: Toggles for showClock and clock24Hour format.
- **CRITICAL SYNC**: `generateIndexHTML()` (L314-430) creates a **simplified** version of `index.html` when saving themes. This generator **intentionally omits** ETag polling, rules checking, and fontScalePercent logic to avoid complexity. Prefer writing only `config.json` instead of regenerating `index.html` unless the user explicitly requests full HTML rewrites. If you add kiosk features (e.g., new polling behaviors), update both the live `index.html` and the generator or document why they diverge.

### `rules/index.html` (schedule configurator)
- **Rules engine**: Writes `rules.json` with `{enabled: bool, rules: [{name, days[], startTime, endTime, menu?, slideshow?}]}`. `index.html` checks this every minute.
- **Content type selection**: Rules can specify either `menu` (traditional text menu) or `slideshow` (multimedia presentation). Only one per rule.
- **Time range logic**: Handles midnight crossings (e.g., startTime "22:00" → endTime "07:00" spans two days); see `checkScheduleRules()` in `index.html` for implementation.

### `slideshows/index.html` (slideshow editor)
- **Multi-set management**: Create/edit multiple slideshow sets (JSON files in `slideshows/sets/`). Each set contains array of slides.
- **Slide types**: Text (markdown + background), Image (with captions), Video (with loop/mute controls).
- **Visual editor**: Form-based slide editing with live preview panel. Upload media directly or specify paths.
- **Transitions**: 6 effects (fade, slide-left/right/up/down, zoom, none). Per-slide duration control (0 = video length).
- **Reordering**: Up/down buttons to change slide sequence. Delete button removes slides.
- **Media uploads**: POST to `upload-media.php` → saves to `slideshows/media/` with timestamped filenames.
- **Test mode**: Opens slideshow in new window via `?slideshow=path` URL parameter.

### `start/index.html` (quick start landing page)
- **Navigation hub**: Simple, mobile-friendly landing page with large buttons linking to edit/, design/, rules/, slideshows/, and the main kiosk display.
- **Visual design**: Gradient background, colorful card-style buttons with icons, responsive grid layout.
- **Purpose**: Provides easy access for staff who need to quickly navigate to editing/configuration tools without remembering URLs.

### `demo/index.html` (remote control panel) - UNDOCUMENTED FEATURE
- **Remote control**: Phone/tablet interface for controlling kiosk TV during demonstrations. Not linked from start menu - accessed directly via `/demo/` URL.
- **Command system**: Sends commands via PUT to `demo-command.txt`; kiosk polls file every 2 seconds and executes commands instantly.
- **Supported commands**: `menu:breakfast|lunch|dinner|closed`, `slideshow:example`, `reload` for full page reload.
- **Touch-optimized UI**: Large buttons (60px min-height, 1.1rem font) for easy tapping on phones/tablets. Toast notifications confirm command delivery.
- **Use case**: Sales demonstrations where presenter controls kiosk TV from phone while audience watches display. Perfect for showcasing menu switching, slideshows, and instant updates.
- **Setup**: Open demo/index.html on phone, open index.html fullscreen on TV. Commands take 1-2 seconds to execute on kiosk.

### PHP Backends
- **`design/upload-bg.php`**: Validates MIME type (`image/*`), file extension (jpg/png/gif/webp), renames to `uploaded_YYYYMMDD_HHMMSS.{ext}`, saves to `../bg/`, logs to `logs/uploads.log`. Returns JSON `{filename}` on success or `{error}` with HTTP 4xx/5xx on failure. Check logs for permission/quota issues.
- **`slideshows/upload-media.php`**: Similar to upload-bg.php but accepts images + videos (mp4/webm/mov). Saves to `slideshows/media/` with `slide_YYYYMMDD_HHMMSS.{ext}` naming. Logs to `logs/slideshow-uploads.log`.
- **`bg/index.php`**: Scans `bg/` directory, filters for image extensions, sorts naturally, returns JSON array of filenames. No pagination; assumes <100 images.
- **`save-menu-history.php`**: Receives POST with menu name and content, creates one file per day in `history/` directory (format: MENUNAME_YYYY-MM-DD_DayOfWeek.txt). Overwrites existing file if saving multiple times same day. Auto-prunes files older than 7 days, logs to `logs/history.log`.
- **`get-menu-history.php`**: Returns menu history as JSON. action=list returns array sorted by timestamp descending, action=get returns specific file content.

## Configuration Schema

### `config.json`
```json
{
  "bg": "filename.jpg",                     // background image (or data URL for legacy)
  "font": "'Comic Sans MS', cursive",       // CSS font-family string
  "fontScalePercent": 5,                    // viewport width % for body text (5-20)
  "headerSizePercent": 5,                   // viewport width % for header text (5-20)
  "bgBrightness": 1.0,                      // background brightness (0.2-1.5, default 1.0)
  "headerText": "Specials",                 // header text override
  "showClock": false,                       // show/hide clock
  "clock24Hour": true,                      // 24-hour vs 12-hour format
  "pollIntervalMs": 3000,                   // preferred poll interval (milliseconds)
  "pollIntervalSeconds": 3,                 // alternate (seconds)
  "pollInterval": 3,                        // legacy shorthand (seconds)
  "availableFonts": { "Display": "CSS" }    // map for design/index.html dropdown
}
```
- **Forward compat**: New fields must be optional; old pages ignore unknown keys. Never destructively rewrite—always read → merge → write.
- **Poll interval precedence**: `pollIntervalMs` > `pollIntervalSeconds` > legacy `pollInterval`; fallback to 3000ms. `index.html` validates positive finite values.

### `rules.json`
```json
{
  "enabled": true,
  "rules": [
    {
      "name": "Breakfast Hours",
      "days": ["monday", "tuesday", ...],   // lowercase, full names
      "startTime": "07:00",                 // HH:MM 24-hour
      "endTime": "11:00",
      "menu": "menus/breakfast.txt"
    },
    {
      "name": "Closed - Show Ads",
      "days": ["monday", "tuesday", ...],
      "startTime": "22:00",
      "endTime": "07:00",
      "slideshow": "slideshows/sets/upcoming-events.json"  // alternative to menu
    }
  ]
}
```
- **Matching logic**: Current day + time must fall within `days[]` and `startTime`/`endTime` range. First matching rule wins; order matters.
- **Content types**: Rules specify either `menu` (text file) or `slideshow` (JSON file). Only one per rule.

### `slideshows/sets/*.json`
```json
{
  "name": "Example Slideshow",
  "description": "Optional description",
  "defaultDuration": 5000,
  "defaultTransition": "fade",
  "slides": [
    {
      "type": "text",                      // or "image", "video"
      "duration": 5000,                    // milliseconds (0 = video length)
      "transition": "fade",                // fade|slide-left|slide-right|slide-up|slide-down|zoom|none
      "background": "../bg/image.jpg",     // for text slides
      "content": "# Title\n\nMarkdown text with {r}color{/r} tags",
      "font": "Lato, sans-serif",
      "fontSize": 5                        // viewport width percentage
    },
    {
      "type": "image",
      "duration": 7000,
      "transition": "slide-left",
      "media": "media/slide_20251204_140532.jpg",
      "caption": "Optional caption text",
      "captionPosition": "bottom"          // top|bottom|center
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
- **Slide types**: Text (markdown + background), Image (with caption), Video (loop/mute controls).
- **Transitions**: Applied when entering slide; 6 options available.
- **Duration**: Time in milliseconds; 0 for videos = play to completion.

## WebDAV Security Model
- **Allowed paths**: `/etc/lighttpd/conf-enabled/10-webdav.conf` restricts PUT to: `index.html`, `config.json`, `rules.json`, `menus/*.txt`, `slideshows/sets/*.json`, `edit/design/rules/slideshows/index.html`. Lighttpd rejects PUTs to other paths with 403/501.
- **No authentication by default**: Intended for trusted local networks (e.g., restaurant staff Wi-Fi). `create-webdav-user.sh` exists for advanced setups but is **not required**—skip for simplicity unless exposing to internet (discouraged).
- **Permission failures**: Usually manifest as 501 errors in browser; check lighttpd error log and re-run `permissions.sh` if edits fail.

## Front-End Conventions
- **No bundler**: Vanilla ES6 modules aren't used—everything is inline `<script>` tags. External deps (marked.js) come from CDN.
- **Responsive patterns**: Typography uses `clamp(minRem, viewportPercent, maxRem)` so text auto-scales to screen size. See `index.html` header (5vw between 1.5-4rem) and specials div (`fontScalePercent` vw between 1-3rem).
- **iOS safe areas**: Mobile editors use `padding: max(1rem, env(safe-area-inset-*))` to avoid notch/home bar overlap.
- **Color tags**: `{r}red text` → `<span style="color:#ff4444">red text</span>` via regex replacements in `index.html`. Supported: r/y/g/b/o/p/w (red/yellow/green/blue/orange/pink/white). Color persists to end-of-line or next color tag.

## Testing & Debugging
- **Local dev**: Run `php -S localhost:8000` from repo root; PUT/WebDAV won't work (use browser DevTools Network tab to inspect fetch calls). Test read-only features like menu rendering and config parsing.
- **Full testing**: Deploy to Pi with lighttpd + WebDAV, then verify:
  1. `index.html` loads menu, applies bg/font from `config.json`, polls within `pollIntervalMs`.
  2. `edit/` dynamically loads tabs from rules.json, saves changes to menu files; kiosk updates within poll window.
  3. `design/` uploads image, persists to `bg/`, updates `config.json`, and kiosk reloads bg on next 5-min cycle.
  4. `rules/` enables schedule, kiosk auto-switches menus at specified times.
- **Logs**: Upload failures → `logs/uploads.log` (JSON lines); WebDAV errors → lighttpd error log (`/var/log/lighttpd/error.log`).
- **Health check**: `status.php` returns JSON with version, uptime, menu file stats, disk space; use for monitoring.

## Utilities
- **`scripts/backup.sh`**: Copies menus/, config.json, rules.json, bg/uploaded_* to timestamped dirs under `/var/backups/314sign/`. Excludes default backgrounds. Prunes backups >30 days old.
- **`scripts/update-from-github.sh`**: Syncs local installation with GitHub main branch. Downloads changed files via curl, compares with local versions, updates only differences. Preserves config.json, rules.json, menus/*.txt, and bg/uploaded_* files. Supports `--dry-run` (preview), `--backup` (auto-backup before update), `--force` (ignore local changes). Updates core HTML/PHP, scripts, default backgrounds. Run after pushing changes to keep deployed kiosks current.
- **`scripts/os-lite-kiosk.sh`**: Installs minimal X11 + Chromium/Firefox for Pi OS Lite; prompts for screen rotation (0-3); re-runnable to change rotation without reinstalling.
- **`setup-kiosk.sh`**: One-shot installer; see "Deployment Pipeline" above. Re-run to update files but **manually merge config.json/rules.json** to preserve settings.

## Common Pitfalls
1. **Adding files without updating installer**: New editable files need WebDAV config entries AND rsync includes in `setup-kiosk.sh`.
2. **Destructive config writes**: Always read existing `config.json` → merge new keys → write back; never `JSON.stringify({bg, font})` which loses `fontScalePercent`.
3. **Breaking `generateIndexHTML()`**: This function is a **minimal template generator**, not a full clone. Don't expect it to replicate all kiosk features; prefer config-only updates.
4. **Forgetting relative paths**: Editor pages (`edit/`, `design/`, `rules/`) use `../` for config/menu files since they're in subdirectories.
5. **Ignoring ETag**: `index.html` relies on lighttpd's ETag header for fast change detection; disabling ETags (via `server.etag = "disable"`) forces text comparisons on every poll (slower but functional).

## Version Management
- Current version: **0.9.1** (hardcoded in HTML footer divs, `status.php`, README). Increment when releasing breaking changes or major features; update all instances via find/replace.
