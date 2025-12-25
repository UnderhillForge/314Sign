import express from 'express';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { SlideshowSet, ApiResponse } from '../types/index.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = express.Router();

// GET /api/slideshows/sets - List all slideshow sets
router.get('/sets', async (req, res) => {
  try {
    const setsDir = path.join(__dirname, '../../slideshows/sets');

    let setFiles: string[] = [];
    try {
      const files = await fs.readdir(setsDir);
      setFiles = files.filter(file => file.endsWith('.json'));
    } catch (error) {
      // Sets directory doesn't exist or is empty
      return res.json({
        success: true,
        data: []
      } as ApiResponse<string[]>);
    }

    res.json({
      success: true,
      data: setFiles
    } as ApiResponse<string[]>);
  } catch (error) {
    console.error('Error listing slideshow sets:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to list slideshow sets',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// GET /api/slideshows/sets/:name - Get specific slideshow set
router.get('/sets/:name', async (req, res) => {
  try {
    const { name } = req.params;

    // Validate filename
    if (!/^[a-z0-9-]+\.json$/i.test(name)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid slideshow set name',
        message: 'Name must be alphanumeric with dashes, ending in .json'
      } as ApiResponse);
    }

    const setsDir = path.join(__dirname, '../../slideshows/sets');
    const filePath = path.join(setsDir, name);

    try {
      const content = await fs.readFile(filePath, 'utf-8');
      const slideshowSet: SlideshowSet = JSON.parse(content);

      res.json({
        success: true,
        data: slideshowSet
      } as ApiResponse<SlideshowSet>);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        return res.status(404).json({
          success: false,
          error: 'Slideshow set not found',
          message: `Slideshow set '${name}' does not exist`
        } as ApiResponse);
      }
      throw error;
    }
  } catch (error) {
    console.error('Error reading slideshow set:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to read slideshow set',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// PUT /api/slideshows/sets/:name - Save/update slideshow set
router.put('/sets/:name', async (req, res) => {
  try {
    const { name } = req.params;
    const slideshowSet = req.body;

    // Validate filename
    if (!/^[a-z0-9-]+\.json$/i.test(name)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid slideshow set name',
        message: 'Name must be alphanumeric with dashes, ending in .json'
      } as ApiResponse);
    }

    // Validate slideshow set structure
    if (!slideshowSet || typeof slideshowSet !== 'object') {
      return res.status(400).json({
        success: false,
        error: 'Invalid slideshow set data',
        message: 'Request body must be a valid slideshow set object'
      } as ApiResponse);
    }

    const setsDir = path.join(__dirname, '../../slideshows/sets');

    // Ensure sets directory exists
    try {
      await fs.access(setsDir);
    } catch (error) {
      await fs.mkdir(setsDir, { recursive: true });
    }

    const filePath = path.join(setsDir, name);

    // Prepare JSON content
    const jsonContent = JSON.stringify(slideshowSet, null, 2);

    // Atomic write: temp file then rename
    const tempPath = path.join(setsDir, `tmp_${Date.now()}_${name}`);
    await fs.writeFile(tempPath, jsonContent, 'utf-8');
    await fs.rename(tempPath, filePath);

    // Ensure permissions
    try {
      await fs.chmod(filePath, 0o644);
    } catch (error) {
      // Ignore permission errors on some systems
    }

    res.json({
      success: true,
      data: slideshowSet,
      message: 'Slideshow set saved successfully'
    } as ApiResponse<SlideshowSet>);
  } catch (error) {
    console.error('Error saving slideshow set:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to save slideshow set',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// DELETE /api/slideshows/sets/:name - Delete slideshow set
router.delete('/sets/:name', async (req, res) => {
  try {
    const { name } = req.params;

    // Validate filename
    if (!/^[a-z0-9-]+\.json$/i.test(name)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid slideshow set name',
        message: 'Name must be alphanumeric with dashes, ending in .json'
      } as ApiResponse);
    }

    const setsDir = path.join(__dirname, '../../slideshows/sets');
    const filePath = path.join(setsDir, name);

    try {
      await fs.unlink(filePath);

      res.json({
        success: true,
        message: `Slideshow set '${name}' deleted successfully`
      } as ApiResponse);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        return res.status(404).json({
          success: false,
          error: 'Slideshow set not found',
          message: `Slideshow set '${name}' does not exist`
        } as ApiResponse);
      }
      throw error;
    }
  } catch (error) {
    console.error('Error deleting slideshow set:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to delete slideshow set',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

export default router;
