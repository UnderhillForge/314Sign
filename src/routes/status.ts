import express from 'express';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { ServerStatus, ApiResponse } from '../types/index.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = express.Router();

// GET /api/status - Get server status
router.get('/', async (req, res) => {
  try {
    const configPath = path.join(__dirname, '../../config.json');
    const rulesPath = path.join(__dirname, '../../rules.json');
    const versionPath = path.join(__dirname, '../../version.txt');

    // Read version from version.txt
    let version = '0.9.2.1'; // fallback
    try {
      const versionContent = await fs.readFile(versionPath, 'utf-8');
      version = versionContent.toString().trim();
    } catch (error) {
      console.warn('Could not read version from version.txt');
    }

    // Get system uptime (Linux only)
    let uptime: string | null = null;
    try {
      const uptimePath = '/proc/uptime';
      const uptimeContent = await fs.readFile(uptimePath, 'utf-8');
      const uptimeSeconds = parseInt(uptimeContent.toString().split(' ')[0]);
      const days = Math.floor(uptimeSeconds / 86400);
      const hours = Math.floor((uptimeSeconds % 86400) / 3600);
      const minutes = Math.floor((uptimeSeconds % 3600) / 60);
      uptime = `${days}d ${hours}h ${minutes}m`;
    } catch (error) {
      // uptime not available
    }

    // Check menu files
    const menus: any = {};
    const menusDir = path.join(__dirname, '../../menus');
    let menuErrors: string[] = [];

    try {
      const menuFiles = await fs.readdir(menusDir);
      const txtFiles = menuFiles.filter(file => file.endsWith('.txt'));

      if (txtFiles.length === 0) {
        menuErrors.push("No menu files found in menus/ directory");
      }

      for (const file of txtFiles) {
        const filePath = path.join(menusDir, file);
        try {
          const stats = await fs.stat(filePath);
          menus[file] = {
            exists: true,
            size: stats.size,
            modified: stats.mtime.toISOString(),
            writable: true // Assume writable for now
          };
        } catch (error) {
          menus[file] = { exists: false };
          menuErrors.push(`Missing menu: ${file}`);
        }
      }
    } catch (error) {
      menuErrors.push("Could not read menus directory");
    }

    // Check config.json
    let config: any = { exists: false };
    try {
      const configContent = await fs.readFile(configPath, 'utf-8');
      const configJson = JSON.parse(configContent);
      config = {
        exists: true,
        valid: true,
        writable: true, // Assume writable
        background: configJson.bg || 'unknown',
        font: configJson.font || 'unknown',
        pollIntervalSeconds: configJson.pollIntervalSeconds || 'unknown'
      };
    } catch (error) {
      config = {
        exists: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
      menuErrors.push('config.json missing or invalid');
    }

    // Check rules.json
    let rules: any = { exists: false };
    try {
      const rulesContent = await fs.readFile(rulesPath, 'utf-8');
      const rulesJson = JSON.parse(rulesContent);
      rules = {
        exists: true,
        valid: true,
        writable: true, // Assume writable
        enabled: rulesJson.enabled !== false,
        ruleCount: Array.isArray(rulesJson.rules) ? rulesJson.rules.length : 0
      };
    } catch (error) {
      rules = {
        exists: false,
        valid: false
      };
      // Rules are optional, so no error
    }

    // Disk space check (simplified - using basic stat)
    let disk: any = null;
    try {
      // Note: Full disk space checking requires native bindings or external libraries
      // For now, we'll skip detailed disk space reporting
      disk = { available: false };
    } catch (error) {
      // Disk space check not available
    }

    // Check logs directory
    const logsDir = path.join(__dirname, '../../logs');
    try {
      await fs.access(logsDir);
    } catch (error) {
      menuErrors.push('logs/ directory missing');
    }

    const status = {
      version,
      timestamp: new Date().toISOString(),
      uptime,
      menus,
      config,
      rules,
      disk,
      errors: menuErrors,
      healthy: menuErrors.length === 0
    };

    res.json({
      success: true,
      data: status
    } as ApiResponse<any>);
  } catch (error) {
    console.error('Error getting server status:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get server status',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

export default router;
