import express from 'express';
import { MenuItem, ApiResponse } from '../types/index.js';
import { dbHelpers } from '../database.js';
import { authenticateToken, requireAdmin } from './auth.js';

const router = express.Router();

// POST /api/menu - Update current menu (for kiosk initialization)
router.post('/', async (req, res) => {
  try {
    const { name, content } = req.body;

    if (typeof name !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'Invalid request body',
        message: 'Name must be a string'
      } as ApiResponse);
    }

    // For current menu updates, we just need to acknowledge
    // The actual current menu is managed by localStorage and current-menu.json
    res.json({
      success: true,
      message: `Current menu set to ${name}`,
      data: { name, content: content || '' }
    } as ApiResponse);
  } catch (error) {
    console.error('Error updating current menu:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to update current menu',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// GET /api/menu - List all menus (database only)
router.get('/', async (req, res) => {
  try {
    const menus = dbHelpers.getAllMenus();

    // Transform database results to API format
    const menuItems: MenuItem[] = menus.map((menu: any) => ({
      name: menu.name,
      content: menu.content,
      lastModified: new Date(menu.updated_at)
    }));

    res.json({
      success: true,
      data: menuItems
    } as ApiResponse<MenuItem[]>);
  } catch (error) {
    console.error('Error listing menus:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to list menus',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// GET /api/menu/files - List menu files (for frontend dropdowns)
router.get('/files', async (req, res) => {
  try {
    const menus = dbHelpers.getAllMenus();

    const files: any[] = menus.map((menu: any) => ({
      filename: menu.name + '.txt',
      path: 'menus/' + menu.name + '.txt',
      label: menu.name.charAt(0).toUpperCase() + menu.name.slice(1)
    }));

    // Sort alphabetically
    files.sort((a, b) => a.label.localeCompare(b.label));

    res.json({
      success: true,
      data: files
    } as ApiResponse<any[]>);
  } catch (error) {
    console.error('Error listing menu files:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to list menu files',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// GET /api/menu/:name - Get specific menu
router.get('/:name', async (req, res) => {
  try {
    const { name } = req.params;
    const menu = dbHelpers.getMenuByName(name);

    if (!menu) {
      return res.status(404).json({
        success: false,
        error: 'Menu not found',
        message: `Menu '${name}' does not exist`
      } as ApiResponse);
    }

    const menuItem: MenuItem = {
      name: menu.name,
      content: menu.content,
      lastModified: new Date(menu.updated_at)
    };

    res.json({
      success: true,
      data: menuItem
    } as ApiResponse<MenuItem>);
  } catch (error) {
    console.error('Error reading menu:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to read menu',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// PUT /api/menu/:name - Update or create menu content
router.put('/:name', async (req, res) => {
  try {
    const { name } = req.params;
    const { content, font, fontScalePercent } = req.body;

    if (typeof content !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'Invalid request body',
        message: 'Content must be a string'
      } as ApiResponse);
    }

    // Check if menu exists
    const existingMenu = dbHelpers.getMenuByName(name);

    if (existingMenu) {
      // Update existing menu
      dbHelpers.updateMenu(content, name, font, fontScalePercent);
    } else {
      // Create new menu
      dbHelpers.createMenu(name, content, font, fontScalePercent);
    }

    // Get menu data (whether created or updated)
    const menu = dbHelpers.getMenuByName(name);
    if (!menu) {
      throw new Error('Menu not found after create/update');
    }

    const menuItem: MenuItem = {
      name: menu.name,
      content: menu.content,
      lastModified: new Date(menu.updated_at)
    };

    res.json({
      success: true,
      data: menuItem,
      message: existingMenu ? 'Menu updated successfully' : 'Menu created successfully'
    } as ApiResponse<MenuItem>);
  } catch (error) {
    console.error('Error updating/creating menu:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to update/create menu',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// DELETE /api/menu/:name - Delete menu (admin only)
router.delete('/:name', authenticateToken, requireAdmin, async (req, res) => {
  try {
    const { name } = req.params;

    // Delete menu from database
    dbHelpers.deleteMenu(name);

    res.json({
      success: true,
      message: `Menu '${name}' deleted successfully`
    } as ApiResponse);
  } catch (error) {
    console.error('Error deleting menu:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to delete menu',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

export default router;
