import express from 'express';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { RulesConfig, ApiResponse } from '../types/index.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = express.Router();

// GET /api/rules - Get current rules configuration
router.get('/', async (req, res) => {
  try {
    const rulesPath = path.join(__dirname, '../../rules.json');

    let rules: RulesConfig = {
      rules: [],
      defaultMenu: undefined,
      defaultSlideshow: undefined,
      defaultBackground: undefined,
      defaultTheme: undefined
    };

    try {
      const rulesData = await fs.readFile(rulesPath, 'utf-8');
      const parsedRules = JSON.parse(rulesData);

      // Merge with defaults
      rules = {
        rules: parsedRules.rules || [],
        defaultMenu: parsedRules.defaultMenu,
        defaultSlideshow: parsedRules.defaultSlideshow,
        defaultBackground: parsedRules.defaultBackground,
        defaultTheme: parsedRules.defaultTheme
      };
    } catch (error) {
      // Rules file doesn't exist or is invalid, return defaults
      console.log('Rules file not found or invalid, using defaults');
    }

    res.json({
      success: true,
      data: rules
    } as ApiResponse<RulesConfig>);
  } catch (error) {
    console.error('Error reading rules:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to read rules configuration',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// POST /api/rules - Update rules (merge operation)
router.post('/', async (req, res) => {
  try {
    const rulesPath = path.join(__dirname, '../../rules.json');
    const updates = req.body;

    if (!updates || typeof updates !== 'object') {
      return res.status(400).json({
        success: false,
        error: 'Invalid request body',
        message: 'Request body must be a valid JSON object'
      } as ApiResponse);
    }

    // Read existing rules
    let existingRules: RulesConfig = {
      rules: [],
      defaultMenu: undefined,
      defaultSlideshow: undefined,
      defaultBackground: undefined,
      defaultTheme: undefined
    };

    try {
      const rulesData = await fs.readFile(rulesPath, 'utf-8');
      existingRules = JSON.parse(rulesData);
    } catch (error) {
      // Rules file doesn't exist, that's okay
      console.log('Creating new rules file');
    }

    // Merge rules (updates take precedence)
    const newRules: RulesConfig = {
      rules: updates.rules !== undefined ? updates.rules : existingRules.rules,
      defaultMenu: updates.defaultMenu !== undefined ? updates.defaultMenu : existingRules.defaultMenu,
      defaultSlideshow: updates.defaultSlideshow !== undefined ? updates.defaultSlideshow : existingRules.defaultSlideshow,
      defaultBackground: updates.defaultBackground !== undefined ? updates.defaultBackground : existingRules.defaultBackground,
      defaultTheme: updates.defaultTheme !== undefined ? updates.defaultTheme : existingRules.defaultTheme
    };

    // Write back to file
    await fs.writeFile(rulesPath, JSON.stringify(newRules, null, 2), 'utf-8');

    res.json({
      success: true,
      data: newRules,
      message: 'Rules configuration updated successfully'
    } as ApiResponse<RulesConfig>);
  } catch (error) {
    console.error('Error updating rules:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to update rules configuration',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// PUT /api/rules - Replace entire rules configuration
router.put('/', async (req, res) => {
  try {
    const rulesPath = path.join(__dirname, '../../rules.json');
    const newRules = req.body;

    if (!newRules || typeof newRules !== 'object') {
      return res.status(400).json({
        success: false,
        error: 'Invalid request body',
        message: 'Request body must be a valid JSON object'
      } as ApiResponse);
    }

    // Ensure required structure
    const validatedRules: RulesConfig = {
      rules: Array.isArray(newRules.rules) ? newRules.rules : [],
      defaultMenu: newRules.defaultMenu,
      defaultSlideshow: newRules.defaultSlideshow,
      defaultBackground: newRules.defaultBackground,
      defaultTheme: newRules.defaultTheme
    };

    // Write to file
    await fs.writeFile(rulesPath, JSON.stringify(validatedRules, null, 2), 'utf-8');

    res.json({
      success: true,
      data: validatedRules,
      message: 'Rules configuration replaced successfully'
    } as ApiResponse<RulesConfig>);
  } catch (error) {
    console.error('Error replacing rules:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to replace rules configuration',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

export default router;
