import express from 'express';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { ApiResponse } from '../types/index.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = express.Router();

// POST /api/system/reload - Trigger kiosk reload
router.post('/reload', async (req, res) => {
  try {
    // Security: Only allow from localhost/same host (similar to PHP version)
    const clientIP = req.ip || req.connection.remoteAddress;
    const allowedHosts = ['localhost', '127.0.0.1', '::1'];

    // Check if request is from allowed host
    const isAllowed = allowedHosts.includes(clientIP as string) ||
                     (req.hostname && ['localhost', req.hostname].includes(req.hostname));

    if (!isAllowed) {
      return res.status(403).json({
        success: false,
        error: 'Access denied',
        message: 'Reload can only be triggered from localhost'
      } as ApiResponse);
    }

    const reloadFile = path.join(__dirname, '../../reload.txt');

    // Create file if it doesn't exist
    try {
      await fs.access(reloadFile);
    } catch (error) {
      // File doesn't exist, create it
      await fs.writeFile(reloadFile, '', 'utf-8');
    }

    // Write current timestamp
    const timestamp = Math.floor(Date.now() / 1000).toString();
    await fs.writeFile(reloadFile, timestamp, 'utf-8');

    res.json({
      success: true,
      message: 'Reload triggered',
      timestamp: parseInt(timestamp)
    } as ApiResponse<any>);
  } catch (error) {
    console.error('Error triggering reload:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to trigger reload',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

export default router;
