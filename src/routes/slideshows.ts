import express from 'express';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { dbHelpers } from '../database.js';
import { ApiResponse } from '../types/index.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = express.Router();

// GET /api/slideshows - List all slideshows (database + files)
router.get('/', async (req, res) => {
  try {
    const slideshows: any[] = [];

    // Get database slideshows
    try {
      // Note: We need to add slideshow database helpers to dbHelpers
      // For now, slideshows are stored in menus table with JSON content
      const dbSlideshows = dbHelpers.getAllMenus();
      dbSlideshows.forEach((item: any) => {
        try {
          const data = JSON.parse(item.content);
          // Check if this looks like slideshow data (has slides array)
          if (data.slides && Array.isArray(data.slides)) {
            slideshows.push({
              name: item.name,
              type: 'database',
              slides: data.slides.length,
              lastModified: new Date(item.updated_at).getTime()
            });
          }
        } catch (e) {
          // Skip invalid JSON
        }
      });
    } catch (error) {
      console.warn('Error reading database slideshows:', error);
    }

    // Get file-based slideshows
    const slideshowsDir = path.join(__dirname, '../../public/slideshows/sets');
    try {
      const files = await fs.readdir(slideshowsDir);
      for (const file of files) {
        if (file.endsWith('.json')) {
          const name = file.replace('.json', '');
          try {
            const filePath = path.join(slideshowsDir, file);
            const content = await fs.readFile(filePath, 'utf-8');
            const data = JSON.parse(content);
            const stats = await fs.stat(filePath);

            slideshows.push({
              name,
              type: 'file',
              slides: data.slides?.length || 0,
              lastModified: stats.mtime.getTime()
            });
          } catch (error) {
            console.warn(`Error reading slideshow ${file}:`, error);
          }
        }
      }
    } catch (error) {
      console.warn('Error reading slideshows directory:', error);
    }

    // Remove duplicates (prefer database over files)
    const uniqueSlideshows = slideshows.filter((item, index, self) =>
      index === self.findIndex(s => s.name === item.name)
    );

    res.json({
      success: true,
      data: uniqueSlideshows
    } as ApiResponse<any[]>);
  } catch (error) {
    console.error('Error listing slideshows:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to list slideshows',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// GET /api/slideshows/:name - Get specific slideshow
router.get('/:name', async (req, res) => {
  try {
    const { name } = req.params;

    // Try database first
    try {
      const dbItem = dbHelpers.getMenuByName(name);
      if (dbItem) {
        const data = JSON.parse(dbItem.content);
        return res.json({
          success: true,
          data: {
            name: dbItem.name,
            type: 'database',
            ...data,
            lastModified: new Date(dbItem.updated_at).getTime()
          }
        } as ApiResponse<any>);
      }
    } catch (error) {
      console.warn('Error reading slideshow from database:', error);
    }

    // Fall back to file
    const filePath = path.join(__dirname, '../../slideshows/sets', `${name}.json`);
    try {
      const content = await fs.readFile(filePath, 'utf-8');
      const data = JSON.parse(content);
      const stats = await fs.stat(filePath);

      res.json({
        success: true,
        data: {
          name,
          type: 'file',
          ...data,
          lastModified: stats.mtime.getTime()
        }
      } as ApiResponse<any>);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        return res.status(404).json({
          success: false,
          error: 'Slideshow not found',
          message: `Slideshow '${name}' does not exist`
        } as ApiResponse);
      }
      throw error;
    }
  } catch (error) {
    console.error('Error reading slideshow:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to read slideshow',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// POST /api/slideshows - Create new slideshow
router.post('/', async (req, res) => {
  try {
    const { name, ...data } = req.body;

    if (!name || typeof name !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'Invalid request body',
        message: 'Name is required and must be a string'
      } as ApiResponse);
    }

    // Store in database
    try {
      dbHelpers.createMenu(name, JSON.stringify(data));
    } catch (error) {
      if ((error as any).code === 'SQLITE_CONSTRAINT_UNIQUE') {
        return res.status(409).json({
          success: false,
          error: 'Slideshow already exists',
          message: `Slideshow '${name}' already exists`
        } as ApiResponse);
      }
      throw error;
    }

    res.json({
      success: true,
      data: { name, ...data },
      message: 'Slideshow created successfully'
    } as ApiResponse<any>);
  } catch (error) {
    console.error('Error creating slideshow:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to create slideshow',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// PUT /api/slideshows/:name - Update slideshow
router.put('/:name', async (req, res) => {
  try {
    const { name } = req.params;
    const data = req.body;

    // Update in database
    try {
      dbHelpers.updateMenu(JSON.stringify(data), name);
    } catch (error) {
      return res.status(404).json({
        success: false,
        error: 'Slideshow not found',
        message: `Slideshow '${name}' does not exist`
      } as ApiResponse);
    }

    res.json({
      success: true,
      data: { name, ...data },
      message: 'Slideshow updated successfully'
    } as ApiResponse<any>);
  } catch (error) {
    console.error('Error updating slideshow:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to update slideshow',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// DELETE /api/slideshows/:name - Delete slideshow
router.delete('/:name', async (req, res) => {
  try {
    const { name } = req.params;

    // Delete from database
    try {
      dbHelpers.deleteMenu(name);
    } catch (error) {
      return res.status(404).json({
        success: false,
        error: 'Slideshow not found',
        message: `Slideshow '${name}' does not exist`
      } as ApiResponse);
    }

    res.json({
      success: true,
      message: `Slideshow '${name}' deleted successfully`
    } as ApiResponse);
  } catch (error) {
    console.error('Error deleting slideshow:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to delete slideshow',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

export default router;