import express from 'express';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { ApiResponse } from '../types/index.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = express.Router();

// Web-safe fonts that work everywhere (no platform-specific fonts)
const WEB_SAFE_FONTS = {
  // System fonts that work across all platforms
  "Arial": "Arial, sans-serif",
  "Helvetica": "Helvetica, sans-serif",
  "Times New Roman": "Times New Roman, serif",
  "Times": "Times, serif",
  "Courier New": "Courier New, monospace",
  "Courier": "Courier, monospace",
  "Georgia": "Georgia, serif",
  "Verdana": "Verdana, sans-serif",
  "Geneva": "Geneva, sans-serif",
  "Trebuchet MS": "Trebuchet MS, sans-serif",

  // Google Fonts (loaded via CDN, work everywhere)
  "Roboto": "Roboto, sans-serif",
  "Open Sans": "Open Sans, sans-serif",
  "Lato": "Lato, sans-serif",
  "Montserrat": "Montserrat, sans-serif",
  "Poppins": "Poppins, sans-serif",
  "Nunito": "Nunito, sans-serif",
  "Inter": "Inter, sans-serif",
  "Work Sans": "Work Sans, sans-serif",
  "Source Sans Pro": "Source Sans Pro, sans-serif",
  "Ubuntu": "Ubuntu, sans-serif",
  "Noto Sans": "Noto Sans, sans-serif",
  "Fira Sans": "Fira Sans, sans-serif",
  "Oxygen": "Oxygen, sans-serif",
  "Hind": "Hind, sans-serif",
  "Mukti": "Mukti, sans-serif",
  "Arimo": "Arimo, sans-serif",
  "Tinos": "Tinos, serif",
  "Crimson Text": "Crimson Text, serif",
  "Merriweather": "Merriweather, serif",
  "Libre Baskerville": "Libre Baskerville, serif",
  "Source Serif Pro": "Source Serif Pro, serif",
  "Vollkorn": "Vollkorn, serif",
  "Space Mono": "Space Mono, monospace",
  "Fira Code": "Fira Code, monospace",
  "JetBrains Mono": "JetBrains Mono, monospace",
  "Roboto Mono": "Roboto Mono, monospace",
  "Source Code Pro": "Source Code Pro, monospace",
  "IBM Plex Mono": "IBM Plex Mono, monospace"
};

// GET /api/fonts - Return web-safe fonts + custom WOFF/WOFF2 fonts
router.get('/', async (req, res) => {
  try {
    const fontsDir = path.join(__dirname, '../../fonts');
    const customFonts: any[] = [];

    // Scan directory for web fonts (WOFF/WOFF2 prioritized over TTF)
    try {
      const files = await fs.readdir(fontsDir);
      const fontFiles: any[] = [];

      // Collect all font files
      for (const file of files) {
        const ext = path.extname(file).toLowerCase();
        if (['.woff', '.woff2', '.ttf'].includes(ext)) {
          const baseName = path.basename(file, ext);
          const stats = await fs.stat(path.join(fontsDir, file));

          fontFiles.push({
            baseName,
            file,
            ext,
            stats,
            priority: ext === '.woff2' ? 3 : ext === '.woff' ? 2 : 1 // WOFF2 > WOFF > TTF
          });
        }
      }

      // Group by base name and pick the best format (WOFF2 > WOFF > TTF)
      const fontGroups: { [key: string]: any[] } = {};
      fontFiles.forEach(f => {
        if (!fontGroups[f.baseName]) fontGroups[f.baseName] = [];
        fontGroups[f.baseName].push(f);
      });

      // Select best format for each font
      Object.keys(fontGroups).forEach(baseName => {
        const group = fontGroups[baseName];
        group.sort((a, b) => b.priority - a.priority); // Highest priority first

        const best = group[0]; // Best format available

        // Extract font name from filename
        let name = baseName;
        name = name.replace(/[-_]?(Regular|Bold|Italic|Light|Medium|Heavy|Black)$/i, '');
        name = name.replace(/([a-z])([A-Z])/g, '$1 $2'); // Add spaces between camelCase
        name = name.trim();

        customFonts.push({
          name: `${name} (Custom)`,
          file: best.file,
          filename: baseName,
          format: best.ext.substring(1).toUpperCase(), // 'WOFF2', 'WOFF', 'TTF'
          mtime: best.stats.mtime.getTime(),
          url: `/fonts/${best.file}`
        });
      });

      // Sort custom fonts by name
      customFonts.sort((a, b) => a.name.localeCompare(b.name));

    } catch (error) {
      // Fonts directory doesn't exist or can't be read
      console.warn('Could not read fonts directory:', error);
    }

    // Combine web-safe fonts with custom fonts
    const allFonts: { [key: string]: string } = { ...WEB_SAFE_FONTS };

    // Add custom fonts (only if they have web-safe formats)
    customFonts.forEach(font => {
      // Only include WOFF/WOFF2 fonts for web compatibility
      if (font.format === 'WOFF' || font.format === 'WOFF2') {
        allFonts[font.name] = `'${font.filename}', sans-serif`;
      }
    });

    res.json({
      success: true,
      data: {
        webSafeFonts: WEB_SAFE_FONTS,
        customFonts: customFonts.filter(f => f.format === 'WOFF' || f.format === 'WOFF2'),
        allFonts: allFonts
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
