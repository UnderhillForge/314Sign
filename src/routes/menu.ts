import express from 'express';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { MenuItem, ApiResponse } from '../types/index.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = express.Router();

// GET /api/menu - List all menus
router.get('/', async (req, res) => {
  try {
    const menusDir = path.join(__dirname, '../../menus');

    let menuFiles: string[] = [];
    try {
      menuFiles = await fs.readdir(menusDir);
    } catch (error) {
      // Menus directory doesn't exist
      return res.json({
        success: true,
        data: []
      } as ApiResponse<MenuItem[]>);
    }

    const menus: MenuItem[] = [];

    for (const file of menuFiles) {
      if (file.endsWith('.txt')) {
        const menuName = file.replace('.txt', '');
        const filePath = path.join(menusDir, file);

        try {
          const content = await fs.readFile(filePath, 'utf-8');
          const stats = await fs.stat(filePath);

          menus.push({
            name: menuName,
            content: content.trim(),
            lastModified: stats.mtime
          });
        } catch (error) {
          console.warn(`Error reading menu file ${file}:`, error);
        }
      }
    }

    res.json({
      success: true,
      data: menus
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
    const menusDir = path.join(__dirname, '../../menus');

    let menuFiles: string[] = [];
    try {
      menuFiles = await fs.readdir(menusDir);
    } catch (error) {
      // Menus directory doesn't exist
      return res.json({
        success: true,
        data: []
      } as ApiResponse<any[]>);
    }

    const files: any[] = [];

    for (const file of menuFiles) {
      if (file.endsWith('.txt') && file !== 'index.php') {
        files.push({
          filename: file,
          path: 'menus/' + file,
          label: file.replace('.txt', '').replace(/^\w/, c => c.toUpperCase())
        });
      }
    }

    // Natural sort for human-friendly ordering
    files.sort((a, b) => a.filename.localeCompare(b.filename, undefined, { numeric: true, sensitivity: 'base' }));

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
    const filePath = path.join(__dirname, '../../menus', `${name}.txt`);

    try {
      const content = await fs.readFile(filePath, 'utf-8');
      const stats = await fs.stat(filePath);

      const menu: MenuItem = {
        name,
        content: content.trim(),
        lastModified: stats.mtime
      };

      res.json({
        success: true,
        data: menu
      } as ApiResponse<MenuItem>);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        return res.status(404).json({
          success: false,
          error: 'Menu not found',
          message: `Menu '${name}' does not exist`
        } as ApiResponse);
      }
      throw error;
    }
  } catch (error) {
    console.error('Error reading menu:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to read menu',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// PUT /api/menu/:name - Update menu content
router.put('/:name', async (req, res) => {
  try {
    const { name } = req.params;
    const { content } = req.body;

    if (typeof content !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'Invalid request body',
        message: 'Content must be a string'
      } as ApiResponse);
    }

    const menusDir = path.join(__dirname, '../../menus');

    // Ensure menus directory exists
    try {
      await fs.access(menusDir);
    } catch (error) {
      await fs.mkdir(menusDir, { recursive: true });
    }

    const filePath = path.join(menusDir, `${name}.txt`);

    // Write content to file
    await fs.writeFile(filePath, content, 'utf-8');

    // Read back to confirm and get metadata
    const stats = await fs.stat(filePath);

    const menu: MenuItem = {
      name,
      content,
      lastModified: stats.mtime
    };

    res.json({
      success: true,
      data: menu,
      message: 'Menu updated successfully'
    } as ApiResponse<MenuItem>);
  } catch (error) {
    console.error('Error updating menu:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to update menu',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// DELETE /api/menu/:name - Delete menu
router.delete('/:name', async (req, res) => {
  try {
    const { name } = req.params;
    const filePath = path.join(__dirname, '../../menus', `${name}.txt`);

    try {
      await fs.unlink(filePath);

      res.json({
        success: true,
        message: `Menu '${name}' deleted successfully`
      } as ApiResponse);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        return res.status(404).json({
          success: false,
          error: 'Menu not found',
          message: `Menu '${name}' does not exist`
        } as ApiResponse);
      }
      throw error;
    }
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
