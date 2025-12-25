import express from 'express';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { ApiResponse } from '../types/index.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = express.Router();

// GET /api/backgrounds - List background image files
router.get('/', async (req, res) => {
  try {
    const bgDir = path.join(__dirname, '../../bg');

    let files: string[] = [];
    try {
      files = await fs.readdir(bgDir);
    } catch (error) {
      // BG directory doesn't exist, return empty array
      return res.json({
        success: true,
        data: []
      } as ApiResponse<string[]>);
    }

    // Filter for image files only
    const imageExtensions = /\.(jpe?g|png|gif|webp|avif)$/i;
    const images: string[] = [];

    for (const file of files) {
      // Skip hidden files and directories
      if (file.startsWith('.') || file === 'index.php') continue;

      if (imageExtensions.test(file)) {
        const filePath = path.join(bgDir, file);
        try {
          const stat = await fs.stat(filePath);
          if (stat.isFile()) {
            images.push(file);
          }
        } catch (error) {
          // Skip files we can't stat
          continue;
        }
      }
    }

    // Sort by name (natural case-insensitive)
    images.sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }));

    res.json({
      success: true,
      data: images
    } as ApiResponse<string[]>);
  } catch (error) {
    console.error('Error listing background images:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to list background images',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

export default router;
