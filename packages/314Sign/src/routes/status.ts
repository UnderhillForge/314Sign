import express from 'express';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import os from 'os';
import { ServerStatus, ApiResponse } from '../types/index.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = express.Router();

// GET /api/version - Get application version
router.get('/version', async (req, res) => {
  try {
    const versionPath = path.join(__dirname, '../../version.txt');

    // Try database first
    const db = await import('../database.js');
    const dbVersion = db.dbHelpers.getConfig('version');

    let version: string;
    if (dbVersion) {
      version = dbVersion.value;
    } else {
      // Fallback to version.txt
      try {
        const versionContent = await fs.readFile(versionPath, 'utf-8');
        version = versionContent.toString().trim();
      } catch (error) {
        console.warn('Could not read version from version.txt');
        version = '0.9.2.1'; // ultimate fallback
      }

      // Store in database for future use
      try {
        db.dbHelpers.setConfig('version', version);
      } catch (dbError) {
        console.warn('Could not store version in database:', dbError);
      }
    }

    res.json({
      success: true,
      data: { version }
    } as ApiResponse<any>);
  } catch (error) {
    console.error('Error getting version:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get version',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

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

    // Get system uptime using Node.js os module
    let uptime: string | null = null;
    try {
      const uptimeSeconds = os.uptime();
      const days = Math.floor(uptimeSeconds / 86400);
      const hours = Math.floor((uptimeSeconds % 86400) / 3600);
      const minutes = Math.floor((uptimeSeconds % 3600) / 60);
      uptime = `${days}d ${hours}h ${minutes}m`;
    } catch (error) {
      console.warn('Could not get uptime:', error);
    }

    // Get hostname and IP address
    let hostname = 'unknown';
    let ipAddress = 'unknown';
    try {
      hostname = os.hostname() || 'localhost';

      // Get network interfaces
      const networkInterfaces = os.networkInterfaces();

      for (const interfaceName of Object.keys(networkInterfaces)) {
        const interfaces = networkInterfaces[interfaceName];
        if (!interfaces) continue;

        for (const iface of interfaces) {
          // Skip internal and non-IPv4 addresses
          if (iface.internal || iface.family !== 'IPv4') continue;

          // Prefer external interfaces over loopback, but take any IPv4 address
          if (iface.address !== '127.0.0.1' &&
              (!ipAddress || ipAddress === 'unknown' || interfaceName.startsWith('lo'))) {
            ipAddress = iface.address;
          }
        }
      }

      // Fallback for development environments
      if (ipAddress === 'unknown') {
        ipAddress = '127.0.0.1';
      }
      if (hostname === 'unknown') {
        hostname = 'localhost';
      }

    } catch (error) {
      // Provide reasonable defaults if system calls fail
      hostname = 'localhost';
      ipAddress = '127.0.0.1';
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
      hostname: hostname || 'localhost',
      ipAddress: ipAddress || '127.0.0.1',
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
