# 314Sign — Task list for AI agents (issues & ideas)

This file lists concrete issues, bugs, and future ideas that an AI coding agent (Copilot) can pick from. Each item includes a short description, suggested files to inspect, and a quick verification step.

## High priority — recent work (done)

- Implemented safe `config.json` merge endpoint and switched `design` to use it
  - Files changed: `scripts/merge-config.php` (new), `design/index.html` (updated)
  - Result: design saves are non-destructive; the merge endpoint does atomic write and returns helpful hints on failure.

- Fixed editor save path issues
  - Files changed: `edit/index.html` (uses absolute `/menus/...` paths for GET/PUT)
  - Result: editor saves no longer break due to shifted relative paths.

- Improved upload error messages & remediation hints
  - Files changed: `design/upload-bg.php`, `slideshows/upload-media.php`
  - Result: logs and JSON responses include permission/owner hints and suggest running `permissions.sh`.

## Next high-priority tasks (pick in order)

- Open draft GitHub issues for the top 3 items
  - Files/refs: this file `.github/TASKS.md`, `scripts/merge-config.php`, `design/index.html`, `edit/index.html`
  - Verify: issues created with the suggested titles, file references, and reproduction steps.

- Convert remaining `config.json` writers to use the merge endpoint
  - Why: avoid destructive PUTs from other pages or automation.
  - Files to inspect: `design/index.html` (done), search for other `fetch('../config.json', { method: 'PUT' })` or external scripts that PUT directly.
  - Verify: no raw PUTs remain; all callers use `scripts/merge-config.php` or call it as a fallback.

- Add a server-side guard that rejects raw PUT to `config.json` with a helpful message
  - Why: prevents accidental destructive writes from external automation; directs callers to the merge endpoint.
  - Files to add: small `scripts/put-config-guard.php` (or an Apache/lighttpd rule) — implement only if you approve.
  - Verify: direct PUT returns 409/422 with instructions.

- Add a lightweight deploy verification script (`scripts/deploy-check.sh`)
  - Checks: ETag presence, `www-data` ownership of writable dirs, `version.txt` read, reachable `index.html`.
  - Verify: script returns non-zero on failures and prints remediation hints (run `permissions.sh`).

## Middle priority — correctness & validators

- Add slideshow set schema validator and harden upload validations
  - Files: `slideshows/sets/*.json`, new validator script (`scripts/validate-slideshow-set.php` or JS)
  - Verify: validator reports missing fields and exits non-zero in CI.

- Add `rules/examples/` test cases and a tiny rule-evaluator playground
  - Files: `rules/examples/*.json`, small test page or node script to validate midnight-span logic.
  - Verify: given example times, the evaluator selects expected menu.

## Documentation & onboarding (quick wins)

- Add a short `config.json` merge snippet to `.github/copilot-instructions.md`
  - Why: quick reference for contributors and agents.
  - Verify: snippet shows read→merge→POST to `scripts/merge-config.php`.

- Update `docs/` checklist: "Add editable file" — include WebDAV, `setup-kiosk.sh` rsync list, and `permissions.sh` step.

---
How to proceed
- Tell me which next task to prioritize (I can open draft issues or implement them directly). I can also open PRs for any of the items above.


## Ops / Deployment tasks

- Make `setup-kiosk.sh` include new editable files list explicit
  - Why: Adding editable files requires matching WebDAV/rsync config.
  - Files: `setup-kiosk.sh`, deployment docs in `docs/`.
  - Verify: Add a dummy editable file, run `setup-kiosk.sh`, confirm file is included in `/var/www/html`.

- Add a simple deploy verification script
  - Why: Quick validation after deploy (ETags, permissions, version bump).
  - Files: `scripts/` (new script), `version.txt`.
  - Verify: Script returns OK when ETags present and `www-data` owns writable dirs.

## UX / Editor correctness

- Add safe `config.json` merge helper and example
  - Why: Promote non-destructive updates by editors and future scripts.
  - Files: new helper (e.g., `scripts/merge-config.php` or JS), update `design/index.html` to call it.
  - Verify: Running helper merges keys and retains unknown fields.

- Improve `rules/index.html` midnight-span handling tests
  - Why: Schedules that span midnight are tricky; add unit-like checks or a playground page.
  - Files: `rules/index.html`, `rules.json` (example cases in `history/`).
  - Verify: Scheduler evaluates rules correctly at boundary times.

## Slideshows & Media

- Harden `slideshows/upload-media.php` validations
  - Why: Prevent malformed JSON uploads and ensure media cleanup.
  - Files: `slideshows/upload-media.php`, `slideshows/sets/*.json`.
  - Verify: Upload invalid metadata and observe graceful error + log entry.

- Add a slideshow set schema validator
  - Why: Keep sets consistent and prevent runtime errors on the kiosk.
  - Files: `slideshows/sets/example.json`, new validator script.
  - Verify: Validator flags missing fields and reports line numbers.

## Documentation & Onboarding

- Expand `docs/` with a short "Add editable file" checklist
  - Why: New contributors must update WebDAV, `setup-kiosk.sh` includes, and `permissions.sh` expectations.
  - Files: `docs/file_structure.md`, `docs/troubleshooting.md`.
  - Verify: Follow checklist to add a new editable menu or page.

- Add a `config.json` merge snippet to `.github/copilot-instructions.md`
  - Why: Quick reference for AI agents and contributors.
  - Files: `.github/copilot-instructions.md` (update), `scripts/` (optional helper).
  - Verify: Snippet demonstrates read→merge→write safely.

## Nice-to-have / Enhancements

- Small test harness that runs a local headless check of `index.html` JS behavior
  - Why: Automated smoke checks for polling and ETag behavior.
  - Files: new `scripts/smoke-check.js`, README snippet for usage.
  - Verify: Smoke check passes on `php -S localhost:8000`.

- Add explicit examples of `rules.json` cases in `rules/` for test-driven improvements
  - Why: Easier debugging and reproducible edge cases for schedule logic.
  - Files: `rules/examples/*.json` (new folder).
  - Verify: `index.html` picks up rule files when used in dev server.

---
How to use this list
- Pick an item, create an issue with the suggested title and files, and reference this file in the PR.
- If you want, I can open draft issues/PRs for top N items — tell me which ones to prioritize.

***
Generated by an AI coding agent to seed issues and future work for contributors.
