#!/usr/bin/env node

/**
 * Migration script to move legacy .txt files and JSON files to database
 * Run this script to migrate existing content from file-based storage to database
 */

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import Database from 'better-sqlite3';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.join(__dirname, '..');

const DB_PATH = path.join(ROOT_DIR, '314sign.db');

// Initialize database connection
const db = new Database(DB_PATH);
db.pragma('journal_mode = WAL');

async function migrateMenus() {
  console.log('🔄 Migrating menu content from .txt files to database...');

  const menusDir = path.join(ROOT_DIR, 'menus');
  let migrated = 0;
  let skipped = 0;

  try {
    const files = await fs.readdir(menusDir);

    for (const file of files) {
      if (file.endsWith('.txt')) {
        const menuName = file.replace('.txt', '');
        const filePath = path.join(menusDir, file);

        try {
          // Check if already exists in database
          const existing = db.prepare('SELECT id FROM menus WHERE name = ?').get(menuName);
          if (existing) {
            console.log(`⏭️  Menu '${menuName}' already exists in database, skipping...`);
            skipped++;
            continue;
          }

          // Read file content
          const content = await fs.readFile(filePath, 'utf-8');

          // Insert into database
          db.prepare('INSERT INTO menus (name, content) VALUES (?, ?)').run(menuName, content.trim());

          console.log(`✅ Migrated menu: ${menuName}`);
          migrated++;
        } catch (error) {
          console.error(`❌ Error migrating menu ${menuName}:`, error.message);
        }
      }
    }
  } catch (error) {
    console.error('❌ Error reading menus directory:', error.message);
  }

  console.log(`📊 Menu migration complete: ${migrated} migrated, ${skipped} skipped\n`);
}

async function migrateSlideshows() {
  console.log('🔄 Migrating slideshow content from JSON files to database...');

  const slideshowsDir = path.join(ROOT_DIR, 'slideshows', 'sets');
  let migrated = 0;
  let skipped = 0;

  try {
    const files = await fs.readdir(slideshowsDir);

    for (const file of files) {
      if (file.endsWith('.json')) {
        const slideshowName = file.replace('.json', '');
        const filePath = path.join(slideshowsDir, file);

        try {
          // Check if already exists in database (using menus table for now)
          const existing = db.prepare('SELECT id FROM menus WHERE name = ?').get(slideshowName);
          if (existing) {
            console.log(`⏭️  Slideshow '${slideshowName}' already exists in database, skipping...`);
            skipped++;
            continue;
          }

          // Read and parse JSON content
          const content = await fs.readFile(filePath, 'utf-8');
          const slideshowData = JSON.parse(content);

          // Insert into database (using menus table for now)
          db.prepare('INSERT INTO menus (name, content) VALUES (?, ?)').run(slideshowName, content.trim());

          console.log(`✅ Migrated slideshow: ${slideshowName}`);
          migrated++;
        } catch (error) {
          console.error(`❌ Error migrating slideshow ${slideshowName}:`, error.message);
        }
      }
    }
  } catch (error) {
    console.error('❌ Error reading slideshows directory:', error.message);
  }

  console.log(`📊 Slideshow migration complete: ${migrated} migrated, ${skipped} skipped\n`);
}

async function migrateRules() {
  console.log('🔄 Migrating rules content from JSON file to database...');

  const rulesFile = path.join(ROOT_DIR, 'rules.json');
  let migrated = 0;
  let skipped = 0;

  try {
    const content = await fs.readFile(rulesFile, 'utf-8');
    const rulesData = JSON.parse(content);

    if (rulesData.rules && Array.isArray(rulesData.rules)) {
      for (const rule of rulesData.rules) {
        try {
          // Check if rule already exists
          const existing = db.prepare('SELECT id FROM rules WHERE name = ?').get(rule.name);
          if (existing) {
            console.log(`⏭️  Rule '${rule.name}' already exists in database, skipping...`);
            skipped++;
            continue;
          }

          // Insert rule into database
          db.prepare(`
            INSERT INTO rules (name, days, start_time, end_time, menu_name, slideshow_path, enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?)
          `).run(
            rule.name,
            JSON.stringify(rule.days || []),
            rule.startTime || '00:00',
            rule.endTime || '23:59',
            rule.menu || null,
            rule.slideshow || null,
            rule.enabled !== false ? 1 : 0
          );

          console.log(`✅ Migrated rule: ${rule.name}`);
          migrated++;
        } catch (error) {
          console.error(`❌ Error migrating rule ${rule.name}:`, error.message);
        }
      }
    }
  } catch (error) {
    console.error('❌ Error reading rules file:', error.message);
  }

  console.log(`📊 Rules migration complete: ${migrated} migrated, ${skipped} skipped\n`);
}

async function main() {
  console.log('🚀 Starting database migration...\n');

  try {
    await migrateMenus();
    await migrateSlideshows();
    await migrateRules();

    console.log('🎉 Database migration completed successfully!');
    console.log('\n📝 Next steps:');
    console.log('1. Test that all content is accessible via API endpoints');
    console.log('2. Consider removing legacy .txt and .json files after verification');
    console.log('3. Update frontend interfaces to use database-only APIs');

  } catch (error) {
    console.error('💥 Migration failed:', error);
    process.exit(1);
  } finally {
    db.close();
  }
}

// Run migration if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { migrateMenus, migrateSlideshows, migrateRules };
