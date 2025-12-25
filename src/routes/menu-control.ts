import express from 'express';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { ApiResponse } from '../types/index.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = express.Router();

// GET /api/menu-control/current - Get currently active menu
router.get('/current', async (req, res) => {
  try {
    const currentMenuPath = path.join(__dirname, '../../current-menu.json');

    try {
      const content = await fs.readFile(currentMenuPath, 'utf-8');
      const currentMenu = JSON.parse(content);

      res.json({
        success: true,
        data: currentMenu
      } as ApiResponse<any>);
    } catch (error) {
      // File doesn't exist, return default
      res.json({
        success: true,
        data: { menu: null },
        message: 'No current menu set'
      } as ApiResponse<any>);
    }
  } catch (error) {
    console.error('Error reading current menu:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to read current menu',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// PUT /api/menu-control/current - Set currently active menu
router.put('/current', async (req, res) => {
  try {
    const { menu } = req.body;

    if (!menu) {
      return res.status(400).json({
        success: false,
        error: 'Missing menu parameter',
        message: 'Request body must include a menu field'
      } as ApiResponse);
    }

    // Validate menu format (should be menus/*.txt)
    if (!/^menus\/[a-zA-Z0-9_-]+\.txt$/.test(menu)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid menu format',
        message: 'Menu must be in format: menus/[name].txt'
      } as ApiResponse);
    }

    // Check if menu file exists
    const menuPath = path.join(__dirname, '../../', menu);
    try {
      await fs.access(menuPath);
    } catch (error) {
      return res.status(404).json({
        success: false,
        error: 'Menu file not found',
        message: `Menu file '${menu}' does not exist`
      } as ApiResponse);
    }

    const currentMenuPath = path.join(__dirname, '../../current-menu.json');

    // Create JSON content
    const content = JSON.stringify({ menu }, null, 2) + '\n';

    // Write to file
    await fs.writeFile(currentMenuPath, content, 'utf-8');

    res.json({
      success: true,
      data: { menu },
      message: 'Current menu updated successfully'
    } as ApiResponse<any>);
  } catch (error) {
    console.error('Error setting current menu:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to set current menu',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// GET /api/menu-control/history - List menu history
router.get('/history', async (req, res) => {
  try {
    const { menu } = req.query;
    const historyDir = path.join(__dirname, '../../history');

    let pattern = path.join(historyDir, '*.txt');

    if (menu && typeof menu === 'string') {
      // Sanitize menu name
      const sanitizedMenu = menu.replace(/[^a-z0-9_-]/gi, '').toLowerCase();
      if (sanitizedMenu) {
        pattern = path.join(historyDir, `${sanitizedMenu}_*.txt`);
      }
    }

    // Use glob-like functionality
    const files = await fs.readdir(historyDir).catch(() => []);
    const matchingFiles = files.filter(file => {
      const fullPattern = path.basename(pattern).replace(/\*/g, '.*');
      return new RegExp(fullPattern).test(file);
    });

    const history = [];

    for (const file of matchingFiles) {
      const filePath = path.join(historyDir, file);
      const basename = file.replace('.txt', '');
      const parts = basename.split('_');

      // Format: MENUNAME_YYYY-MM-DD_DayOfWeek
      if (parts.length >= 3) {
        const stats = await fs.stat(filePath);
        history.push({
          filename: file,
          menu: parts[0],
          date: parts[1],
          dayOfWeek: parts[2],
          timestamp: stats.mtime.getTime(),
          size: stats.size
        });
      }
    }

    // Sort by timestamp, newest first
    history.sort((a, b) => b.timestamp - a.timestamp);

    res.json({
      success: true,
      data: { history }
    } as ApiResponse<any>);
  } catch (error) {
    console.error('Error listing menu history:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to list menu history',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// GET /api/menu-control/history/:filename - Get specific history entry
router.get('/history/:filename', async (req, res) => {
  try {
    const { filename } = req.params;

    // Security: prevent directory traversal
    const sanitizedFilename = path.basename(filename);

    const historyDir = path.join(__dirname, '../../history');
    const filePath = path.join(historyDir, sanitizedFilename);

    try {
      const content = await fs.readFile(filePath, 'utf-8');

      res.json({
        success: true,
        data: { content }
      } as ApiResponse<any>);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        return res.status(404).json({
          success: false,
          error: 'History file not found',
          message: `History file '${sanitizedFilename}' does not exist`
        } as ApiResponse);
      }
      throw error;
    }
  } catch (error) {
    console.error('Error reading history file:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to read history file',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// POST /api/menu-control/history - Save menu to history
router.post('/history', async (req, res) => {
  let filename = '';
  let isUpdate = false;
  let pruned = 0;

  try {
    const { menu: menuName, content } = req.body;

    if (!menuName || !content) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields',
        message: 'Request body must include menu name and content'
      } as ApiResponse);
    }

    // Sanitize menu name
    const sanitizedMenu = menuName.replace(/[^a-z0-9_-]/gi, '').toLowerCase();
    if (!sanitizedMenu || sanitizedMenu.length > 50) {
      return res.status(400).json({
        success: false,
        error: 'Invalid menu name',
        message: 'Menu name must be alphanumeric, dash, underscore, max 50 chars'
      } as ApiResponse);
    }

    const historyDir = path.join(__dirname, '../../history');

    // Ensure history directory exists
    try {
      await fs.access(historyDir);
    } catch (error) {
      await fs.mkdir(historyDir, { recursive: true });
    }

    // Create filename with format: MENUNAME_YYYY-MM-DD_DayOfWeek.txt
    const timestamp = Date.now();
    const date = new Date(timestamp).toISOString().split('T')[0];
    const dayOfWeek = new Date(timestamp).toLocaleDateString('en-US', { weekday: 'long' });
    filename = `${sanitizedMenu}_${date}_${dayOfWeek}.txt`;
    const filePath = path.join(historyDir, filename);

    // Check if file for today already exists
    try {
      await fs.access(filePath);
      isUpdate = true;
    } catch (error) {
      // File doesn't exist, that's fine
    }

    // Save history file
    await fs.writeFile(filePath, content, 'utf-8');

    // Prune old history files (older than 7 days)
    const cutoffTime = timestamp - (7 * 24 * 60 * 60 * 1000);
    const files = await fs.readdir(historyDir).catch(() => []);

    for (const file of files) {
      const filePathToCheck = path.join(historyDir, file);
      try {
        const stats = await fs.stat(filePathToCheck);
        if (stats.mtime.getTime() < cutoffTime) {
          await fs.unlink(filePathToCheck);
          pruned++;
        }
      } catch (error) {
        // Ignore errors for individual files
      }
    }

    // Log the save
    const logDir = path.join(__dirname, '../../logs');
    try {
      await fs.access(logDir);
    } catch (error) {
      await fs.mkdir(logDir, { recursive: true });
    }

    const logEntry = JSON.stringify({
      timestamp: new Date().toISOString(),
      menu: sanitizedMenu,
      filename,
      action: isUpdate ? 'updated' : 'created',
      pruned
    }) + '\n';

    const logPath = path.join(logDir, 'history.log');
    await fs.appendFile(logPath, logEntry);

    res.json({
      success: true,
      data: { filename, action: isUpdate ? 'updated' : 'created', pruned },
      message: 'Menu history saved successfully'
    } as ApiResponse<any>);
  } catch (error) {
    console.error('Error saving menu history:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to save menu history',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

export default router;
