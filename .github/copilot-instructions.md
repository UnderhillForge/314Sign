# 314Sign — Copilot / AI Agent Instructions (concise)
# 314Sign — Copilot / AI Agent Instructions (concise)

Purpose: give an AI coding agent the minimal, high-value knowledge to be productive in this repo.

1) Big picture
- Zero-backend static kiosk: static HTML/JS/CSS served by lighttpd; runtime state = files under /var/www/html (no DB/API).
- Editors modify files directly via WebDAV/HTTP PUT and a few PHP endpoints (menus, rules, slideshows).

2) High-value entry points
- `index.html`: kiosk UI — loads `config.json`, polls `menus/*.txt` and `rules.json` (ETag-aware). See `FORMATTING.md` for color/tag rules.
- `edit/index.html`: mobile editor — derives tabs from `rules.json`, PUTs menu text to `../menus/{name}.txt`, uses `save-menu-history.php`.
- `design/index.html`: uploads backgrounds via `design/upload-bg.php` and updates `config.json`. `generateIndexHTML()` exports themes only.
- `rules/index.html`: schedule editor — writes `rules.json` (handles midnight-spanning ranges; search for `checkScheduleRules()`).
- `slideshows/sets/*.json` and `slideshows/upload-media.php`: slideshow sets and media uploads.

3) Project-specific conventions & gotchas
- No bundler: JavaScript is inline in HTML files. Make minimal, localized edits and preserve formatting.
- Non-destructive `config.json` updates: always read → merge → write to avoid losing keys (backgrounds, fonts, logos).
- Editor pages use relative `../` paths — moving files often breaks saves.
- `index.html` relies on server ETags; changing server ETag behavior alters polling semantics.

4) Common workflows & quick commands
- Local UI check (read-only): run `php -S localhost:8000` from repository root.
- Deploy / install server + WebDAV: `./setup-kiosk.sh` (also syncs files to `/var/www/html`).
- Fix permissions after remote changes: run `permissions.sh` on the host.
- Trigger client reloads: update `version.txt` (helper: `./scripts/increment-version.sh`).

5) Integrations & ops notes
- WebDAV PUTs are controlled by server config; adding editable files requires updating the WebDAV include list in `setup-kiosk.sh`.
- Demo control: `demo/index.html` writes `demo-command.txt`; `index.html` polls it frequently.
- Upload/logs: check `logs/` (e.g., `logs/uploads.log`) for upload or permission errors.

6) Safe-change contract for AI edits
- Scope: small, focused changes to HTML/JS, JSON schemas (`config.json`, `rules.json`, slideshows), or `menus/*.txt`.
- Must be backward-compatible and non-destructive: preserve unknown keys in JSON, avoid moving editor paths, and do not remove WebDAV-compatible endpoints.
- Verify permission-related issues and server-side PHP endpoints when saving remotely (403/501 are common failure modes).

7) Verification checklist
- Run `php -S localhost:8000` to visually verify the UI (note: PUTs won't work in this static server).
- If you add/move editable files, update `setup-kiosk.sh` rsync includes and server WebDAV config; then run `permissions.sh` on the host.
- Bump `version.txt` to force clients to reload and confirm changes on the kiosk.

If anything here is unclear or you'd like a short `config.json` merge snippet or a checklist for adding a new editable file, tell me which section to expand.
