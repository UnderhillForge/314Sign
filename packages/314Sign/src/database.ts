import Database from 'better-sqlite3';
import path from 'path';
import fs from 'fs';

const DB_PATH = path.join(process.cwd(), '314sign.db');

// Ensure database directory exists
const dbDir = path.dirname(DB_PATH);
if (!fs.existsSync(dbDir)) {
  fs.mkdirSync(dbDir, { recursive: true });
}

const db: Database.Database = new Database(DB_PATH);

// Enable WAL mode for better concurrency
db.pragma('journal_mode = WAL');

// Create tables
export async function initializeDatabase() {
  // Users table for authentication
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'viewer',
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      last_login DATETIME
    );

    CREATE TABLE IF NOT EXISTS sessions (
      id TEXT PRIMARY KEY,
      user_id INTEGER NOT NULL,
      expires_at DATETIME NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS menus (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT UNIQUE NOT NULL,
      content TEXT NOT NULL,
      font TEXT,
      font_scale_percent REAL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS menu_history (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      menu_name TEXT NOT NULL,
      content TEXT NOT NULL,
      created_by TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS rules (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      days TEXT NOT NULL, -- JSON array of days
      start_time TEXT NOT NULL,
      end_time TEXT NOT NULL,
      menu_name TEXT,
      slideshow_path TEXT,
      enabled BOOLEAN DEFAULT 1,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS config (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      key TEXT UNIQUE NOT NULL,
      value TEXT NOT NULL,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- Insert default values for dynamic state (replacing JSON files)
    INSERT OR IGNORE INTO config (key, value) VALUES ('current_menu', 'menus/dinner.txt');
    INSERT OR IGNORE INTO config (key, value) VALUES ('reload_trigger', '0');
    INSERT OR IGNORE INTO config (key, value) VALUES ('demo_command', 'idle');

    CREATE TABLE IF NOT EXISTS uploads (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      filename TEXT NOT NULL,
      original_name TEXT NOT NULL,
      type TEXT NOT NULL, -- 'bg', 'media', 'logo'
      size INTEGER NOT NULL,
      uploaded_by TEXT,
      uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS slideshows (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT UNIQUE NOT NULL,
      data TEXT NOT NULL, -- JSON data
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS db_rules (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT UNIQUE NOT NULL,
      data TEXT NOT NULL, -- JSON data
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );



    CREATE TABLE IF NOT EXISTS remotes (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      serial TEXT UNIQUE NOT NULL, -- Hardware serial number
      code TEXT UNIQUE NOT NULL, -- Display code for registration
      display_name TEXT NOT NULL,
      mode TEXT NOT NULL DEFAULT 'mirror', -- 'mirror', 'menu', 'slideshow', 'master-remote'
      slideshow_name TEXT, -- Name of slideshow file if mode is 'slideshow'
      orientation TEXT NOT NULL DEFAULT '{}', -- JSON orientation settings
      status TEXT NOT NULL DEFAULT 'active', -- 'active', 'inactive'
      sync_enabled BOOLEAN DEFAULT 0, -- Enable master-remote sync
      cache_updated_at DATETIME, -- Last time content cache was updated
      last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS displays (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      hdmi_port INTEGER UNIQUE NOT NULL, -- 0 or 1 for Pi 5 dual HDMI
      enabled BOOLEAN DEFAULT 1,
      guest_facing BOOLEAN DEFAULT 0,
      orientation INTEGER DEFAULT 0, -- 0 (normal), 1 (90°), 2 (180°), 3 (270°)
      mode TEXT NOT NULL DEFAULT 'main', -- 'main' (kiosk menu), 'slideshow', 'disabled'
      slideshow_name TEXT, -- Slideshow to display if mode is 'slideshow'
      resolution TEXT, -- e.g., "1920x1080" (NULL = auto-detect)
      xrandr_output TEXT, -- e.g., "HDMI-1", "HDMI-2"
      position_x INTEGER DEFAULT 0, -- X position for xrandr
      position_y INTEGER DEFAULT 0, -- Y position (for side-by-side multi-monitor)
      refresh_rate REAL, -- e.g., 60.0
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- Indexes for performance
    CREATE INDEX IF NOT EXISTS idx_menus_name ON menus(name);
    CREATE INDEX IF NOT EXISTS idx_menu_history_menu_name ON menu_history(menu_name);
    CREATE INDEX IF NOT EXISTS idx_rules_enabled ON rules(enabled);
    CREATE INDEX IF NOT EXISTS idx_config_key ON config(key);
    CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
    CREATE INDEX IF NOT EXISTS idx_remotes_code ON remotes(code);
    CREATE INDEX IF NOT EXISTS idx_remotes_status ON remotes(status);
    CREATE INDEX IF NOT EXISTS idx_remotes_last_seen ON remotes(last_seen);
    CREATE INDEX IF NOT EXISTS idx_displays_hdmi_port ON displays(hdmi_port);
  `);

  const displayColumns = db.prepare('PRAGMA table_info(displays)').all() as any[];
  const hasGuestFacing = displayColumns.some((col) => col.name === 'guest_facing');
  if (!hasGuestFacing) {
    db.exec('ALTER TABLE displays ADD COLUMN guest_facing BOOLEAN DEFAULT 0');
  }

  // Insert default admin user if no users exist
  const userCount = db.prepare('SELECT COUNT(*) as count FROM users').get() as { count: number };
  if (userCount.count === 0) {
    // Import bcrypt dynamically for ES module compatibility
    const bcrypt = await import('bcrypt');
    const hashedPassword = bcrypt.default.hashSync('admin123', 10);

    db.prepare(`
      INSERT INTO users (username, password_hash, role)
      VALUES (?, ?, ?)
    `).run('admin', hashedPassword, 'admin');

    console.log('Created default admin user: admin/admin123');
  }

  // Insert default menus if none exist
  const menuCount = db.prepare('SELECT COUNT(*) as count FROM menus').get() as { count: number };
  if (menuCount.count === 0) {
    const defaultMenus = [
      {
        name: 'breakfast',
        content: `## Breakfast Specials

{r}Hot Coffee - {y}$2.50
{g}Fresh brewed daily, unlimited refills

{r}Breakfast Burrito - {y}$8.95
{g}Sausage, eggs, cheese, salsa

{r}Pancakes - {y}$6.95
{g}Three fluffy pancakes with maple syrup

{r}Oatmeal - {y}$4.95
{g}Steel cut oats with fresh berries

---
{g}All breakfast served with toast and juice`
      },
      {
        name: 'lunch',
        content: `## Lunch Specials

{r}Grilled Cheese Sandwich - {y}$6.95
{g}Cheddar cheese on sourdough bread

{r}BLT Sandwich - {y}$7.95
{g}Bacon, lettuce, tomato on toasted bread

{r}Chicken Salad - {y}$9.95
{g}Grilled chicken with mixed greens

{r}Soup of the Day - {y}$5.95
{g}Ask your server for today's selection

---
{g}All sandwiches served with chips or fries`
      },
      {
        name: 'dinner',
        content: `## Dinner Specials

{r}Ribeye Steak - {y}$24.95
{g}8oz choice ribeye with garlic mashed potatoes

{r}Grilled Salmon - {y}$18.95
{g}Fresh Atlantic salmon with seasonal vegetables

{r}Chicken Parmesan - {y}$16.95
{g}Breaded chicken breast with marinara sauce

{r}Pasta Primavera - {y}$14.95
{g}Seasonal vegetables in garlic olive oil

---
{g}All dinners include house salad and breadsticks`
      },
      {
        name: 'closed',
        content: `## Sorry, We're Closed

{r}Store Hours:
{g}Monday - Friday: 7:00 AM - 9:00 PM
Saturday: 8:00 AM - 10:00 PM
Sunday: 9:00 AM - 8:00 PM

{r}Holiday Hours May Vary

{g}Thank you for your business!
We look forward to serving you soon.

---
{r}Follow us on social media for updates!`
      }
    ];

    const insertMenu = db.prepare(`
      INSERT INTO menus (name, content, font, font_scale_percent)
      VALUES (?, ?, ?, ?)
    `);

    for (const menu of defaultMenus) {
      insertMenu.run(menu.name, menu.content, 'Arial, sans-serif', 10);
    }

    console.log('Created default menus: breakfast, lunch, dinner, closed');
  }

  // Initialize default displays if none exist
  const displayCount = db.prepare('SELECT COUNT(*) as count FROM displays').get() as { count: number };
  if (displayCount.count === 0) {
    const defaultDisplays = [
      {
        hdmi_port: 0,
        enabled: 1,
        guest_facing: 1,
        orientation: 1, // 90° for portrait
        mode: 'main',
        slideshow_name: null,
        resolution: null,
        xrandr_output: 'HDMI-1',
        position_x: 0,
        position_y: 0,
        refresh_rate: 60.0
      },
      {
        hdmi_port: 1,
        enabled: 0, // Disabled by default
        guest_facing: 0,
        orientation: 0, // Normal landscape
        mode: 'slideshow',
        slideshow_name: null,
        resolution: null,
        xrandr_output: 'HDMI-2',
        position_x: 1080, // To the right of first monitor
        position_y: 0,
        refresh_rate: 60.0
      }
    ];

    const insertDisplay = db.prepare(`
      INSERT INTO displays (hdmi_port, enabled, guest_facing, orientation, mode, slideshow_name, resolution, xrandr_output, position_x, position_y, refresh_rate)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    for (const display of defaultDisplays) {
      insertDisplay.run(
        display.hdmi_port,
        display.enabled,
        display.guest_facing,
        display.orientation,
        display.mode,
        display.slideshow_name,
        display.resolution,
        display.xrandr_output,
        display.position_x,
        display.position_y,
        display.refresh_rate
      );
    }

    console.log('Created default display configurations for HDMI-1 and HDMI-2');
  }

  const guestDisplayCount = db.prepare('SELECT COUNT(*) as count FROM displays WHERE guest_facing = 1').get() as { count: number };
  if (guestDisplayCount.count === 0) {
    const firstDisplay = db.prepare('SELECT hdmi_port FROM displays ORDER BY hdmi_port ASC LIMIT 1').get() as { hdmi_port: number } | undefined;
    if (firstDisplay) {
      db.prepare('UPDATE displays SET guest_facing = CASE WHEN hdmi_port = ? THEN 1 ELSE 0 END').run(firstDisplay.hdmi_port);
    }
  }

  // Initialize prepared statements after tables are created
  initializeStatements();

  // Initialize version from version.txt if not in database
  const dbVersion = dbHelpers.getConfig('version');
  if (!dbVersion) {
    try {
      const fs = await import('fs/promises');
      const versionPath = path.join(process.cwd(), 'version.txt');
      const versionContent = await fs.readFile(versionPath, 'utf-8');
      const version = versionContent.toString().trim();

      if (version) {
        dbHelpers.setConfig('version', version);
        console.log('Stored version in database:', version);
      }
    } catch (error) {
      console.warn('Could not initialize version from version.txt:', error);
    }
  }
}

// Prepared statements - created after database initialization
let getUserByUsernameStmt: any;
let createUserStmt: any;
let updateUserLastLoginStmt: any;
let getSessionStmt: any;
let createSessionStmt: any;
let deleteSessionStmt: any;
let cleanupExpiredSessionsStmt: any;
let getAllMenusStmt: any;
let getMenuByNameStmt: any;
let createMenuStmt: any;
let updateMenuStmt: any;
let deleteMenuStmt: any;
let getMenuHistoryStmt: any;
let addMenuHistoryStmt: any;
let clearMenuHistoryStmt: any;
let getAllRulesStmt: any;
let getRuleByIdStmt: any;
let createRuleStmt: any;
let updateRuleStmt: any;
let deleteRuleStmt: any;
let getConfigStmt: any;
let setConfigStmt: any;
let getAllConfigStmt: any;
let logUploadStmt: any;
let getUploadsStmt: any;
let getAllSlideshowsStmt: any;
let getSlideshowByNameStmt: any;
let createSlideshowStmt: any;
let updateSlideshowStmt: any;
let deleteSlideshowStmt: any;
let renameSlideshowStmt: any;

// Initialize prepared statements after database setup
function initializeStatements() {
  getUserByUsernameStmt = db.prepare('SELECT * FROM users WHERE username = ?');
  createUserStmt = db.prepare(`
    INSERT INTO users (username, password_hash, role)
    VALUES (?, ?, ?)
  `);
  updateUserLastLoginStmt = db.prepare('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?');

  getSessionStmt = db.prepare(`
    SELECT s.*, u.username, u.role
    FROM sessions s
    JOIN users u ON s.user_id = u.id
    WHERE s.id = ? AND s.expires_at > CURRENT_TIMESTAMP
  `);
  createSessionStmt = db.prepare(`
    INSERT INTO sessions (id, user_id, expires_at)
    VALUES (?, ?, ?)
  `);
  deleteSessionStmt = db.prepare('DELETE FROM sessions WHERE id = ?');
  cleanupExpiredSessionsStmt = db.prepare('DELETE FROM sessions WHERE expires_at <= CURRENT_TIMESTAMP');

  getAllMenusStmt = db.prepare('SELECT * FROM menus ORDER BY name');
  getMenuByNameStmt = db.prepare('SELECT * FROM menus WHERE name = ?');
  createMenuStmt = db.prepare(`
    INSERT INTO menus (name, content, font, font_scale_percent)
    VALUES (?, ?, ?, ?)
  `);
  updateMenuStmt = db.prepare(`
    UPDATE menus
    SET content = ?, font = ?, font_scale_percent = ?, updated_at = CURRENT_TIMESTAMP
    WHERE name = ?
  `);
  deleteMenuStmt = db.prepare('DELETE FROM menus WHERE name = ?');

  getMenuHistoryStmt = db.prepare(`
    SELECT * FROM menu_history
    WHERE menu_name = ?
    ORDER BY created_at DESC
    LIMIT ?
  `);
  addMenuHistoryStmt = db.prepare(`
    INSERT INTO menu_history (menu_name, content, created_by)
    VALUES (?, ?, ?)
  `);
  clearMenuHistoryStmt = db.prepare('DELETE FROM menu_history WHERE menu_name = ?');

  getAllRulesStmt = db.prepare('SELECT * FROM rules WHERE enabled = 1 ORDER BY name');
  getRuleByIdStmt = db.prepare('SELECT * FROM rules WHERE id = ?');
  createRuleStmt = db.prepare(`
    INSERT INTO rules (name, days, start_time, end_time, menu_name, slideshow_path)
    VALUES (?, ?, ?, ?, ?, ?)
  `);
  updateRuleStmt = db.prepare(`
    UPDATE rules
    SET name = ?, days = ?, start_time = ?, end_time = ?, menu_name = ?, slideshow_path = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
  `);
  deleteRuleStmt = db.prepare('DELETE FROM rules WHERE id = ?');

  getConfigStmt = db.prepare('SELECT * FROM config WHERE key = ?');
  setConfigStmt = db.prepare(`
    INSERT OR REPLACE INTO config (key, value, updated_at)
    VALUES (?, ?, CURRENT_TIMESTAMP)
  `);
  getAllConfigStmt = db.prepare('SELECT * FROM config ORDER BY key');

  logUploadStmt = db.prepare(`
    INSERT INTO uploads (filename, original_name, type, size, uploaded_by)
    VALUES (?, ?, ?, ?, ?)
  `);
  getUploadsStmt = db.prepare(`
    SELECT * FROM uploads
    WHERE type = ?
    ORDER BY uploaded_at DESC
    LIMIT ?
  `);

  getAllSlideshowsStmt = db.prepare('SELECT * FROM slideshows ORDER BY name');
  getSlideshowByNameStmt = db.prepare('SELECT * FROM slideshows WHERE name = ?');
  createSlideshowStmt = db.prepare(`
    INSERT INTO slideshows (name, data)
    VALUES (?, ?)
  `);
  updateSlideshowStmt = db.prepare(`
    UPDATE slideshows
    SET data = ?, updated_at = CURRENT_TIMESTAMP
    WHERE name = ?
  `);
  deleteSlideshowStmt = db.prepare('DELETE FROM slideshows WHERE name = ?');
  renameSlideshowStmt = db.prepare('UPDATE slideshows SET name = ? WHERE name = ?');
}

// Export functions instead of prepared statements
export const dbHelpers = {
  // Users
  getUserByUsername: (username: string) => getUserByUsernameStmt.get(username),
  createUser: (username: string, passwordHash: string, role: string) => createUserStmt.run(username, passwordHash, role),
  updateUserLastLogin: (id: number) => updateUserLastLoginStmt.run(id),

  // Sessions
  getSession: (id: string) => getSessionStmt.get(id),
  createSession: (id: string, userId: number, expiresAt: string) => createSessionStmt.run(id, userId, expiresAt),
  deleteSession: (id: string) => deleteSessionStmt.run(id),
  cleanupExpiredSessions: () => cleanupExpiredSessionsStmt.run(),

  // Menus
  getAllMenus: () => getAllMenusStmt.all(),
  getMenuByName: (name: string) => getMenuByNameStmt.get(name),
  createMenu: (name: string, content: string, font?: string, fontScalePercent?: number) => createMenuStmt.run(name, content, font, fontScalePercent),
  updateMenu: (content: string, name: string, font?: string, fontScalePercent?: number) => updateMenuStmt.run(content, font, fontScalePercent, name),
  deleteMenu: (name: string) => deleteMenuStmt.run(name),

  // Menu History
  getMenuHistory: (menuName: string, limit: number) => getMenuHistoryStmt.all(menuName, limit),
  addMenuHistory: (menuName: string, content: string, createdBy?: string) => addMenuHistoryStmt.run(menuName, content, createdBy),
  clearMenuHistory: (menuName: string) => clearMenuHistoryStmt.run(menuName),

  // Rules
  getAllRules: () => getAllRulesStmt.all(),
  getRuleById: (id: number) => getRuleByIdStmt.get(id),
  createRule: (name: string, days: string, startTime: string, endTime: string, menuName?: string, slideshowPath?: string) =>
    createRuleStmt.run(name, days, startTime, endTime, menuName, slideshowPath),
  updateRule: (name: string, days: string, startTime: string, endTime: string, menuName: string | undefined, slideshowPath: string | undefined, id: number) =>
    updateRuleStmt.run(name, days, startTime, endTime, menuName, slideshowPath, id),
  deleteRule: (id: number) => deleteRuleStmt.run(id),

  // Config
  getConfig: (key: string) => getConfigStmt.get(key),
  setConfig: (key: string, value: string) => setConfigStmt.run(key, value),
  getAllConfig: () => getAllConfigStmt.all(),

  // Uploads
  logUpload: (filename: string, originalName: string, type: string, size: number, uploadedBy?: string) =>
    logUploadStmt.run(filename, originalName, type, size, uploadedBy),
  getUploads: (type: string, limit: number) => getUploadsStmt.all(type, limit),

  // Slideshows
  getAllSlideshows: () => getAllSlideshowsStmt.all(),
  getSlideshowByName: (name: string) => getSlideshowByNameStmt.get(name),
  createSlideshow: (name: string, data: string) => createSlideshowStmt.run(name, data),
  updateSlideshow: (name: string, data: string) => updateSlideshowStmt.run(data, name),
  deleteSlideshow: (name: string) => deleteSlideshowStmt.run(name),
  renameSlideshow: (oldName: string, newName: string) => renameSlideshowStmt.run(newName, oldName),

  // Remotes (sync & config)
  getRemoteByCode: (code: string) => db.prepare('SELECT * FROM remotes WHERE code = ?').get(code) as any,
  getAllRemotes: () => db.prepare('SELECT * FROM remotes ORDER BY last_seen DESC').all() as any[],
  updateRemoteSyncStatus: (code: string, syncEnabled: boolean) => 
    db.prepare('UPDATE remotes SET sync_enabled = ?, last_seen = datetime(\'now\') WHERE code = ?').run(syncEnabled, code),
  updateRemoteCacheTime: (code: string) =>
    db.prepare('UPDATE remotes SET cache_updated_at = datetime(\'now\') WHERE code = ?').run(code),
  getRemoteCacheInfo: (code: string) => {
    const remote = db.prepare('SELECT cache_updated_at, last_seen FROM remotes WHERE code = ?').get(code) as any;
    return remote ? {
      cacheUpdatedAt: remote.cache_updated_at,
      lastSeen: remote.last_seen,
      isCached: !!remote.cache_updated_at
    } : null;
  },

  // Displays (dual HDMI configuration)
  getAllDisplays: () => db.prepare('SELECT * FROM displays ORDER BY hdmi_port ASC').all() as any[],
  getDisplayByPort: (hdmiPort: number) => db.prepare('SELECT * FROM displays WHERE hdmi_port = ?').get(hdmiPort) as any,
  updateDisplay: (hdmiPort: number, config: {
    enabled?: number;
    guest_facing?: number;
    orientation?: number;
    mode?: string;
    slideshow_name?: string | null;
    resolution?: string | null;
    xrandr_output?: string | null;
    position_x?: number;
    position_y?: number;
    refresh_rate?: number | null;
  }) => {
    const updates: string[] = [];
    const values: any[] = [];

    if (config.enabled !== undefined) { updates.push('enabled = ?'); values.push(config.enabled); }
    if (config.guest_facing !== undefined) { updates.push('guest_facing = ?'); values.push(config.guest_facing); }
    if (config.orientation !== undefined) { updates.push('orientation = ?'); values.push(config.orientation); }
    if (config.mode !== undefined) { updates.push('mode = ?'); values.push(config.mode); }
    if (config.slideshow_name !== undefined) { updates.push('slideshow_name = ?'); values.push(config.slideshow_name); }
    if (config.resolution !== undefined) { updates.push('resolution = ?'); values.push(config.resolution); }
    if (config.xrandr_output !== undefined) { updates.push('xrandr_output = ?'); values.push(config.xrandr_output); }
    if (config.position_x !== undefined) { updates.push('position_x = ?'); values.push(config.position_x); }
    if (config.position_y !== undefined) { updates.push('position_y = ?'); values.push(config.position_y); }
    if (config.refresh_rate !== undefined) { updates.push('refresh_rate = ?'); values.push(config.refresh_rate); }

    if (updates.length === 0) return;

    updates.push('updated_at = CURRENT_TIMESTAMP');
    values.push(hdmiPort);

    const query = `UPDATE displays SET ${updates.join(', ')} WHERE hdmi_port = ?`;
    return db.prepare(query).run(...values);
  },
  createDisplay: (config: {
    hdmi_port: number;
    enabled?: number;
    guest_facing?: number;
    orientation?: number;
    mode?: string;
    slideshow_name?: string | null;
    resolution?: string | null;
    xrandr_output?: string | null;
    position_x?: number;
    position_y?: number;
    refresh_rate?: number | null;
  }) => {
    return db.prepare(`
      INSERT INTO displays (hdmi_port, enabled, guest_facing, orientation, mode, slideshow_name, resolution, xrandr_output, position_x, position_y, refresh_rate)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      config.hdmi_port,
      config.enabled ?? 1,
      config.guest_facing ?? 0,
      config.orientation ?? 0,
      config.mode ?? 'main',
      config.slideshow_name ?? null,
      config.resolution ?? null,
      config.xrandr_output ?? null,
      config.position_x ?? 0,
      config.position_y ?? 0,
      config.refresh_rate ?? 60.0
    );
  },
  setGuestFacingExclusive: (hdmiPort: number) =>
    db.prepare('UPDATE displays SET guest_facing = CASE WHEN hdmi_port = ? THEN 1 ELSE 0 END').run(hdmiPort)
};

// Cleanup expired sessions periodically
setInterval(() => {
  try {
    dbHelpers.cleanupExpiredSessions();
  } catch (error) {
    console.warn('Failed to cleanup expired sessions:', error);
  }
}, 60000); // Every minute

export default db;
