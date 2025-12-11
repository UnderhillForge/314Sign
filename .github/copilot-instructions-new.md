# 314Sign — Copilot / AI Agent Instructions (concise)

Purpose: equip an AI coding agent with the exact, high-value knowledge to be immediately productive in this repo.

1) Big picture
- Zero-backend static kiosk: static HTML/JS/CSS served by lighttpd; runtime state is files under `/var/www/html` (no DB or REST API).
- Editors write via WebDAV / HTTP PUT: they modify `config.json`, `rules.json`, `menus/*.txt`, and `slideshows/sets/*.json` directly.

2) Where to look (high value files)
- `index.html` — kiosk display: loads `config.json`, polls menu files + `rules.json` (ETag-aware), applies color tags (see `FORMATTING.md`).
- `edit/index.html` — mobile editor: derives tabs from `rules.json`, PUTs menu text to `../menus/{name}.txt`, saves history via `save-menu-history.php`.
- `design/index.html` — style designer: uploads backgrounds (`design/upload-bg.php`), updates `config.json`. `generateIndexHTML()` is a simplified exporter—prefer config-only edits.
- `rules/index.html` — schedule editor: writes `rules.json`; handles midnight-spanning ranges (search for `checkScheduleRules()`).
- `slideshows/sets/*.json` + `slideshows/upload-media.php` — slideshow sets and media uploads.

3) Critical developer workflows
- Quick local check: `php -S localhost:8000` from repo root (read-only UI checks; WebDAV PUT won't work).
- Deployment: run `./setup-kiosk.sh` to install lighttpd + WebDAV and rsync assets to `/var/www/html`.
- After changing files on a deployed host: run `permissions.sh` to ensure `www-data` ownership and writable dirs.
- Force client reloads: bump `version.txt` (use `./scripts/increment-version.sh`).

4) Conventions & gotchas (project-specific)
- No bundler: JS is inline in HTML. Keep edits minimal and preserve formatting/style.
- Never destructively overwrite `config.json`: always read → merge → write to preserve unknown keys (bg, fonts, logos, etc.).
- Editor pages use `../` relative paths—be careful when moving files.
- `index.html` relies on server ETags for efficient polling; disabling ETags changes behavior to slower text comparisons.
- `generateIndexHTML()` is a theme exporter only and intentionally omits some kiosk behaviors—do not rely on it to replicate `index.html` fully.

5) Integration & infra notes
- WebDAV PUTs are restricted by server config; adding new editable files requires updating WebDAV config and the `rsync` includes in `setup-kiosk.sh`.
- Remote demo controls: `demo/index.html` writes `demo-command.txt`; `index.html` polls it (~2s).
- Upload endpoints log to `logs/` (e.g., `logs/uploads.log`) — check logs for permission or validation failures.

6) Small contract for AI edits
- Inputs: focused JS/HTML edits, JSON schema changes (`config.json`, `rules.json`, slideshows) or menu text files in `menus/`.
- Outputs: non-destructive, backward-compatible changes that preserve config keys and do not break WebDAV/installer expectations.
- Error modes to watch for: permission/PUT failures (403/501), broken ETag/polling, destructive config writes, failing uploads (check `logs/`).

7) Quick verification checklist after edits
- Run `php -S localhost:8000` to visually verify UI changes (read-only paths).
- If you add/move editable files, update `setup-kiosk.sh` rsync includes and WebDAV config, then run `permissions.sh` on the host.
- Bump `version.txt` to trigger client reloads and confirm changes propagate to kiosk display.

If you want this to replace the existing `.github/copilot-instructions.md`, tell me and I will swap files (or open a PR). If you want wording changes, specify which section to tweak and I’ll update it.