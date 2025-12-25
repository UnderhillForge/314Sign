import express from 'express';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { KioskConfig, ApiResponse } from '../types/index.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = express.Router();

// GET /api/config - Get current config
router.get('/', async (req, res) => {
  try {
    const configPath = path.join(__dirname, '../../config.json');

    let config: KioskConfig = {
      version: '1.0.0'
    };

    try {
      const configData = await fs.readFile(configPath, 'utf-8');
      config = { ...config, ...JSON.parse(configData) };
    } catch (error) {
      // Config file doesn't exist or is invalid, return defaults
      console.log('Config file not found or invalid, using defaults');
    }

    res.json({
      success: true,
      data: config
    } as ApiResponse<KioskConfig>);
  } catch (error) {
    console.error('Error reading config:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to read configuration',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// POST /api/config - Update config (merge operation)
router.post('/', async (req, res) => {
  try {
    const configPath = path.join(__dirname, '../../config.json');
    const updates = req.body;

    if (!updates || typeof updates !== 'object') {
      return res.status(400).json({
        success: false,
        error: 'Invalid request body',
        message: 'Request body must be a valid JSON object'
      } as ApiResponse);
    }

    // Read existing config
    let existingConfig: KioskConfig = {
      version: '1.0.0'
    };

    try {
      const configData = await fs.readFile(configPath, 'utf-8');
      existingConfig = JSON.parse(configData);
    } catch (error) {
      // Config file doesn't exist, that's okay
      console.log('Creating new config file');
    }

    // Merge configs (updates take precedence)
    const newConfig: KioskConfig = {
      ...existingConfig,
      ...updates,
      // Ensure version is preserved or updated
      version: updates.version || existingConfig.version || '1.0.0'
    };

    // Write back to file
    await fs.writeFile(configPath, JSON.stringify(newConfig, null, 2), 'utf-8');

    res.json({
      success: true,
      data: newConfig,
      message: 'Configuration updated successfully'
    } as ApiResponse<KioskConfig>);
  } catch (error) {
    console.error('Error updating config:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to update configuration',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// PUT /api/config - Replace entire config
router.put('/', async (req, res) => {
  try {
    const configPath = path.join(__dirname, '../../config.json');
    const newConfig = req.body;

    if (!newConfig || typeof newConfig !== 'object') {
      return res.status(400).json({
        success: false,
        error: 'Invalid request body',
        message: 'Request body must be a valid JSON object'
      } as ApiResponse);
    }

    // Ensure version exists
    if (!newConfig.version) {
      newConfig.version = '1.0.0';
    }

    // Write to file
    await fs.writeFile(configPath, JSON.stringify(newConfig, null, 2), 'utf-8');

    res.json({
      success: true,
      data: newConfig,
      message: 'Configuration replaced successfully'
    } as ApiResponse<KioskConfig>);
  } catch (error) {
    console.error('Error replacing config:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to replace configuration',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

export default router;