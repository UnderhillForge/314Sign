import express from 'express';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { ApiResponse } from '../types/index.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = express.Router();

// GET /api/fonts - Scan fonts directory and return list of TTF files
router.get('/', async (req, res) => {
  try {
    const fontsDir = path.join(__dirname, '../../fonts');
    const fonts: any[] = [];

    // Scan directory for .ttf files
    try {
      const files = await fs.readdir(fontsDir);

      for (const file of files) {
        if (path.extname(file).toLowerCase() === '.ttf') {
          const filePath = path.join(fontsDir, file);
          const stats = await fs.stat(filePath);

          // Extract font name from filename
          // Convert "BebasNeue-Regular.ttf" -> "Bebas Neue"
          let name = path.basename(file, '.ttf');
          name = name.replace(/[-_]?(Regular|Bold|Italic|Light|Medium|Heavy|Black)$/i, '');
          name = name.replace(/([a-z])([A-Z])/g, '$1 $2'); // Add spaces between camelCase
          name = name.trim();

          fonts.push({
            name,
            file,
            filename: path.basename(file, '.ttf'),
            mtime: stats.mtime.getTime()
          });
        }
      }
    } catch (error) {
      // Fonts directory doesn't exist or can't be read
      console.warn('Could not read fonts directory:', error);
    }

    // Sort by name
    fonts.sort((a, b) => a.name.localeCompare(b.name));

    res.json({
      success: true,
      data: fonts
    } as ApiResponse<any[]>);
  } catch (error) {
    console.error('Error scanning fonts:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to scan fonts directory',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

export default router;
