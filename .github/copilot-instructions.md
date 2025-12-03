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
- **Gotcha**: `index.html` never writes config—it's read-only. `design/index.html` writes `bg`/`font`, `edit/index.html` writes `fontScalePercent`. All must tolerate missing keys gracefully.

### `edit/index.html` (mobile menu editor)
- **Multi-menu tabs**: Switches between breakfast/lunch/dinner/closed.txt via localStorage; each tab PUTs to its own file using `../menus/{name}.txt` relative paths.
- **Font scale slider**: Adjusts `fontScalePercent` (1-10%) in `config.json` via PUT; `index.html` reads this to set `clamp()` font sizes dynamically. Merges into existing config to avoid clobbering `bg`/`font`.
- **Markdown toolbar**: Inserts formatting (`**bold**`, color tags like `{r}`, list bullets) and shows live preview via marked.js.
- **Toast UX**: Shows success/error notifications using `.toast` CSS + `showToast()` helper; all editor pages follow this pattern (aria-live for accessibility).

### `design/index.html` (style configurator)
- **Background picker**: Fetches image list from `bg/index.php` → renders thumbnails → on selection, PUTs `config.json` with new `bg` filename (prefer file references over data URLs for caching).
- **Upload flow**: User picks image → validates client-side → POSTs FormData to `upload-bg.php` → receives `{filename: "uploaded_YYYYMMDD_HHMMSS.ext"}` → saves filename to `config.json` → adds thumb to grid.
- **Font dropdown**: Populated from `config.json.availableFonts` map (keys = display names, values = CSS font-family strings).
- **CRITICAL SYNC**: `generateIndexHTML()` (L314-430) creates a **simplified** version of `index.html` when saving themes. This generator **intentionally omits** ETag polling, rules checking, and fontScalePercent logic to avoid complexity. Prefer writing only `config.json` instead of regenerating `index.html` unless the user explicitly requests full HTML rewrites. If you add kiosk features (e.g., new polling behaviors), update both the live `index.html` and the generator or document why they diverge.

### `rules/index.html` (schedule configurator)
- **Rules engine**: Writes `rules.json` with `{enabled: bool, rules: [{name, days[], startTime, endTime, menu}]}`. `index.html` checks this every minute.
- **Time range logic**: Handles midnight crossings (e.g., startTime "22:00" → endTime "07:00" spans two days); see `checkScheduleRules()` in `index.html` for implementation.

### PHP Backends
- **`design/upload-bg.php`**: Validates MIME type (`image/*`), file extension (jpg/png/gif/webp), renames to `uploaded_YYYYMMDD_HHMMSS.{ext}`, saves to `../bg/`, logs to `logs/uploads.log`. Returns JSON `{filename}` on success or `{error}` with HTTP 4xx/5xx on failure. Check logs for permission/quota issues.
- **`bg/index.php`**: Scans `bg/` directory, filters for image extensions, sorts naturally, returns JSON array of filenames. No pagination; assumes <100 images.

## Configuration Schema

### `config.json`
```json
{
  "bg": "filename.jpg",                     // background image (or data URL for legacy)
  "font": "'Comic Sans MS', cursive",       // CSS font-family string
  "fontScalePercent": 3,                    // viewport width % for clamp() (1-10)
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
    }
  ]
}
```
- **Matching logic**: Current day + time must fall within `days[]` and `startTime`/`endTime` range. First matching rule wins; order matters.

## WebDAV Security Model
- **Allowed paths**: `/etc/lighttpd/conf-enabled/10-webdav.conf` restricts PUT to: `index.html`, `config.json`, `rules.json`, `menus/*.txt`, `edit/design/rules/index.html`. Lighttpd rejects PUTs to other paths with 403/501.
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
  2. `edit/` saves changes to all four menu tabs; kiosk updates within poll window.
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
- Current version: **0.8.0** (hardcoded in HTML footer divs, `status.php`, README). Increment when releasing breaking changes or major features; update all instances via find/replace.
