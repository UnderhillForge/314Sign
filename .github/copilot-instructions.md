# 314Sign Copilot Instructions

- **Mission-critical context**: 314Sign is a zero-backend kiosk that serves static HTML/JS with lighttpd; edits happen through HTTP PUT/WebDAV against files in `/var/www/html` so preserving file names and paths is essential.
- **Runtime & deployment**: `setup-kiosk.sh` provisions lighttpd + PHP-CGI, clones the repo, and rsyncs the web assets into `/var/www/html`; update that script if you add or move files so fresh installs stay consistent.
- **Core files**:
  - `index.html`: TV-facing display that fetches `config.json` once and polls `specials.txt` every `pollInterval*` milliseconds (ETag-aware, 5-minute hard reload for config/background changes).
  - `edit.html`: Mobile editor that PUTs `specials.txt` and updates `config.json.fontScalePercent`; assumes WebDAV is enabled for those paths.
  - `design.html`: Style configurator that picks backgrounds/fonts, writes `config.json`, uploads images, and rewrites `index.html` via PUT.
  - `upload-bg.php`: Validates uploads (extension, MIME, permissions), saves into `bg/`, and logs to `logs/uploads.log`.
  - `bg/index.php`: Returns a sorted JSON list of images under `bg/` for the designer picker.
- **Configuration contract**: `config.json` currently tracks `bg`, `font`, `fontScalePercent`, and poll interval variants (`pollIntervalMs`, `pollIntervalSeconds`, legacy `pollInterval`) plus an `availableFonts` map; new fields must remain JSON-serializable and tolerate missing/unknown keys on older pages.
- **Cross-page coordination**: `design.html` only writes `bg`/`font`, `edit.html` updates `fontScalePercent`, and `index.html` must continue reading all three without breaking if one page hasn’t written yet—keep defaults sane and avoid destructive rewrites of unrecognized properties.
- **Background workflow**: Prefer storing uploaded assets as files in `bg/`; when `upload-bg.php` returns `filename`, `design.html` immediately persists that name back into `config.json`. Support for data URLs exists for legacy configs, but newly saved designs should favor file references so the kiosk can cache efficiently.
- **Lighttpd/WebDAV limits**: Setup enables PUT only for `index.html`, `config.json`, and `specials.txt`; if you introduce new editable files (e.g., extra JSON), update `/etc/lighttpd/conf-enabled/10-webdav.conf` via the installer or document the manual change.
- **Front-end patterns**: Everything is vanilla ES6 with inline `<style>` blocks—no bundler. Responsive typography leans on `clamp()` and viewport units, and touch UI should account for iOS safe areas (see `edit.html`/`design.html`).
- **Testing checklist**: After changes, hit `index.html` and `edit.html` through an HTTP server that honors PUT (lighttpd, nginx with WebDAV, or `php -S` behind a proxy); confirm specials update within the configured poll window and that full reloads pick up background/font tweaks.
- **Diagnostics**: Background upload issues surface in `logs/uploads.log`; WebDAV/PUT failures usually show up in lighttpd’s error log. Make sure new API responses stay JSON and include actionable error strings for the toasts.
- **Keep generators aligned**: `design.html`’s `generateIndexHTML()` must stay in sync with the canonical `index.html` template. If you add kiosk features, update both the live file and the generator to avoid regressions when staff save a new theme.
