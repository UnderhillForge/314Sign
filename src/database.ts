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
      mode TEXT NOT NULL DEFAULT 'mirror', -- 'mirror', 'menu', 'slideshow'
      slideshow_name TEXT, -- Name of slideshow file if mode is 'slideshow'
      orientation TEXT NOT NULL DEFAULT '{}', -- JSON orientation settings
      status TEXT NOT NULL DEFAULT 'active', -- 'active', 'inactive'
      last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
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
  `);

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

  // Initialize prepared statements after tables are created
  initializeStatements();
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
  setConfig: (key: string, value: string) => setConfigStmt.run(key, value, Date.now()),
  getAllConfig: () => getAllConfigStmt.all(),

  // Uploads
  logUpload: (filename: string, originalName: string, type: string, size: number, uploadedBy?: string) =>
    logUploadStmt.run(filename, originalName, type, size, uploadedBy),
  getUploads: (type: string, limit: number) => getUploadsStmt.all(type, limit)
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
