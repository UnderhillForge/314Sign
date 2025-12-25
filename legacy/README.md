# Legacy PHP Backend Files

This directory contains PHP files from the original 314Sign implementation that are being phased out as the project migrates to a modern Node.js/TypeScript architecture.

## Status

These files are **deprecated** and will be removed in a future release after their functionality is fully implemented in the TypeScript API.

## Files

### PHP Backend Scripts
- `apply-updates.php` - Apply GitHub updates (used by maintenance page)
- `check-updates.php` - Check for available updates (used by maintenance page)
- `create-backup.php` - Create system backups (used by maintenance page)
- `get-menu-history.php` - Retrieve menu change history (used by edit pages)
- `save-menu-history.php` - Save menu changes to history (used by edit pages)
- `set-current-menu.php` - Set the active menu (used by kiosk display)

### System Configuration (PHP/lighttpd era)
- `create-webdav-user.sh` - Create dedicated WebDAV user for security
- `sudoers-314sign` - Sudo permissions for PHP maintenance operations

## Migration Plan

Each PHP file will be replaced with a TypeScript API endpoint:

- `apply-updates.php` → `POST /api/system/apply-updates`
- `check-updates.php` → `GET /api/system/check-updates`
- `create-backup.php` → `POST /api/system/create-backup`
- `get-menu-history.php` → `GET /api/menu/history`
- `save-menu-history.php` → `POST /api/menu/history`
- `set-current-menu.php` → `PUT /api/menu-control/current`

## Why Keep These Files?

The frontend HTML pages still reference these PHP endpoints. Removing them would break the current functionality until all API endpoints are implemented and the frontend is updated.

## Timeline

- **Phase 1** (Current): PHP files moved to legacy directory ✅
- **Phase 2**: Implement TypeScript API replacements
- **Phase 3**: Update frontend to use new APIs
- **Phase 4**: Remove legacy PHP files

For questions about the migration, see the main [README.md](../README.md) or create an issue.
