import express from 'express';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { ApiResponse } from '../types/index.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = express.Router();

interface CuratedFont {
  name: string;
  filename: string;
  family: string;
  category: string;
  weight: number;
  style: string;
}

interface FontManifest {
  curatedFonts: CuratedFont[];
}

// Load curated fonts from manifest
async function loadCuratedFonts(): Promise<CuratedFont[]> {
  try {
    const manifestPath = path.join(__dirname, '../../fonts/manifest.json');
    const manifestData = await fs.readFile(manifestPath, 'utf-8');
    const manifest: FontManifest = JSON.parse(manifestData);
    return manifest.curatedFonts || [];
  } catch (error) {
    console.warn('Could not load fonts manifest:', error);
    return [];
  }
}

// GET /api/fonts - Return curated fonts + custom uploaded fonts
router.get('/', async (req, res) => {
  try {
    const fontsDir = path.join(__dirname, '../../fonts');
    
    // Load curated fonts from manifest
    const curatedFonts = await loadCuratedFonts();
    const curatedFilenames = new Set(curatedFonts.map(f => f.filename));

    // Scan directory for custom uploaded fonts (not in manifest)
    const customFonts: any[] = [];

    try {
      const files = await fs.readdir(fontsDir);
      const fontFiles: any[] = [];

      // Collect all font files that aren't in the curated list
      for (const file of files) {
        const ext = path.extname(file).toLowerCase();
        if (['.woff', '.woff2', '.ttf'].includes(ext) && !curatedFilenames.has(file)) {
          const baseName = path.basename(file, ext);
          const stats = await fs.stat(path.join(fontsDir, file));

          fontFiles.push({
            baseName,
            file,
            ext,
            stats,
            priority: ext === '.woff2' ? 3 : ext === '.woff' ? 2 : 1
          });
        }
      }

      // Group by base name and pick the best format
      const fontGroups: { [key: string]: any[] } = {};
      fontFiles.forEach(f => {
        if (!fontGroups[f.baseName]) fontGroups[f.baseName] = [];
        fontGroups[f.baseName].push(f);
      });

      // Select best format for each custom font
      Object.keys(fontGroups).forEach(baseName => {
        const group = fontGroups[baseName];
        group.sort((a, b) => b.priority - a.priority);

        const best = group[0];

        // Extract font name from filename
        let name = baseName;
        name = name.replace(/[-_]?(Regular|Bold|Italic|Light|Medium|Heavy|Black)$/i, '');
        name = name.replace(/([a-z])([A-Z])/g, '$1 $2');
        name = name.trim();

        customFonts.push({
          name: `${name} (Custom)`,
          file: best.file,
          filename: baseName,
          format: best.ext.substring(1).toUpperCase(),
          mtime: best.stats.mtime.getTime(),
          url: `/fonts/${best.file}`
        });
      });

      customFonts.sort((a, b) => a.name.localeCompare(b.name));

    } catch (error) {
      console.warn('Could not read fonts directory:', error);
    }

    // Build response with curated and custom fonts
    res.json({
      success: true,
      data: {
        curatedFonts: curatedFonts.map(font => ({
          ...font,
          url: `/fonts/${font.filename}`
        })),
        customFonts: customFonts
      }
    } as ApiResponse<any>);
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
