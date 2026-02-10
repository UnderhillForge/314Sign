import express from 'express';
import multer from 'multer';
import fs from 'fs/promises';
import fsSync from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dbHelpers } from '../database.js';
import { ApiResponse } from '../types/index.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = express.Router();

const mediaDir = path.join(__dirname, '../../slideshows/media');
const mediaStorage = multer.diskStorage({
  destination: (req, file, cb) => {
    try {
      if (!fsSync.existsSync(mediaDir)) {
        fsSync.mkdirSync(mediaDir, { recursive: true });
      }
      cb(null, mediaDir);
    } catch (error) {
      cb(error as Error, mediaDir);
    }
  },
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    const base = path.basename(file.originalname, ext).replace(/[^a-z0-9_-]+/gi, '-');
    const unique = Date.now() + '-' + Math.round(Math.random() * 1e9);
    cb(null, `${base}-${unique}${ext}`);
  }
});

const mediaUpload = multer({
  storage: mediaStorage,
  limits: { fileSize: 15 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    const allowedTypes = [
      'image/jpeg',
      'image/png',
      'image/gif',
      'image/svg+xml',
      'image/avif'
    ];
    if (allowedTypes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('Unsupported file type'));
    }
  }
});

/**
 * GET /api/slideshows - List all slideshows
 * Returns array of slideshow summaries (name, slide count, last modified)
 */
router.get('/', async (req, res) => {
  try {
    const dbSlideshows = dbHelpers.getAllSlideshows();
    
    const slideshows = dbSlideshows.map((item: any) => {
      try {
        const data = JSON.parse(item.data);
        return {
          name: item.name,
          description: data.description || '',
          slideCount: data.slides?.length || 0,
          defaultDuration: data.defaultDuration || 5000,
          defaultTransition: data.defaultTransition || 'fade',
          lastModified: new Date(item.updated_at).getTime()
        };
      } catch (error) {
        console.warn(`Error parsing slideshow '${item.name}':`, error);
        return {
          name: item.name,
          description: '',
          slideCount: 0,
          lastModified: new Date(item.updated_at).getTime()
        };
      }
    });

    res.json({
      success: true,
      data: slideshows
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

/**
 * GET /api/slideshows/:name - Get specific slideshow
 * Returns full slideshow data for playback or editing
 */
router.get('/:name', async (req, res) => {
  try {
    const { name } = req.params;

    const slideshow = dbHelpers.getSlideshowByName(name);
    if (!slideshow) {
      return res.status(404).json({
        success: false,
        error: 'Slideshow not found',
        message: `Slideshow '${name}' does not exist`
      } as ApiResponse);
    }

    try {
      const data = JSON.parse(slideshow.data);
      res.json({
        success: true,
        data: {
          name: slideshow.name,
          ...data,
          lastModified: new Date(slideshow.updated_at).getTime()
        }
      } as ApiResponse<any>);
    } catch (error) {
      console.error(`Error parsing slideshow '${name}':`, error);
      res.status(500).json({
        success: false,
        error: 'Invalid slideshow data',
        message: 'Slideshow data is corrupted or invalid JSON'
      } as ApiResponse);
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

/**
 * POST /api/slideshows - Create new slideshow
 * Requires: name, description, slides (array), defaultDuration, defaultTransition
 */
router.post('/', async (req, res) => {
  try {
    const { name, description = '', slides = [], defaultDuration = 5000, defaultTransition = 'fade' } = req.body;

    if (!name || typeof name !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'Invalid request body',
        message: 'Name is required and must be a string'
      } as ApiResponse);
    }

    if (!Array.isArray(slides)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid request body',
        message: 'Slides must be an array'
      } as ApiResponse);
    }

    // Check if slideshow already exists
    const existing = dbHelpers.getSlideshowByName(name);
    if (existing) {
      return res.status(409).json({
        success: false,
        error: 'Slideshow already exists',
        message: `Slideshow '${name}' already exists`
      } as ApiResponse);
    }

    const slideshowData = {
      description,
      slides,
      defaultDuration,
      defaultTransition
    };

    try {
      dbHelpers.createSlideshow(name, JSON.stringify(slideshowData));
      res.status(201).json({
        success: true,
        data: {
          name,
          ...slideshowData
        },
        message: 'Slideshow created successfully'
      } as ApiResponse<any>);
    } catch (error) {
      console.error('Error creating slideshow in database:', error);
      throw error;
    }
  } catch (error) {
    console.error('Error creating slideshow:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to create slideshow',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

/**
 * PUT /api/slideshows/:name - Update slideshow
 * Requires: description, slides, defaultDuration, defaultTransition (full object)
 */
router.put('/:name', async (req, res) => {
  try {
    const { name } = req.params;
    const { description = '', slides = [], defaultDuration = 5000, defaultTransition = 'fade' } = req.body;

    // Verify slideshow exists
    const existing = dbHelpers.getSlideshowByName(name);
    if (!existing) {
      return res.status(404).json({
        success: false,
        error: 'Slideshow not found',
        message: `Slideshow '${name}' does not exist`
      } as ApiResponse);
    }

    if (!Array.isArray(slides)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid request body',
        message: 'Slides must be an array'
      } as ApiResponse);
    }

    const slideshowData = {
      description,
      slides,
      defaultDuration,
      defaultTransition
    };

    dbHelpers.updateSlideshow(name, JSON.stringify(slideshowData));

    // Broadcast update to synced remotes
    try {
      const broadcastToAllRemotes = req.app.locals.broadcastToAllRemotes;
      if (broadcastToAllRemotes) {
        const updateMessage = {
          type: 'slideshow-update',
          data: {
            name,
            slideshow: slideshowData,
            timestamp: new Date().toISOString()
          }
        };
        broadcastToAllRemotes(updateMessage);
        console.log(`Broadcasted slideshow update for '${name}' to synced remotes`);
      }
    } catch (error) {
      console.error('Failed to broadcast slideshow update:', error);
      // Don't fail the request if broadcast fails
    }

    res.json({
      success: true,
      data: {
        name,
        ...slideshowData
      },
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

/**
 * DELETE /api/slideshows/:name - Delete slideshow
 */
router.delete('/:name', async (req, res) => {
  try {
    const { name } = req.params;

    // Verify slideshow exists
    const existing = dbHelpers.getSlideshowByName(name);
    if (!existing) {
      return res.status(404).json({
        success: false,
        error: 'Slideshow not found',
        message: `Slideshow '${name}' does not exist`
      } as ApiResponse);
    }

    dbHelpers.deleteSlideshow(name);

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

/**
 * POST /api/slideshows/:name/clone - Duplicate slideshow with new name
 * Requires body: { newName: string }
 */
router.post('/:name/clone', async (req, res) => {
  try {
    const { name } = req.params;
    const { newName } = req.body;

    if (!newName || typeof newName !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'Invalid request body',
        message: 'newName is required and must be a string'
      } as ApiResponse);
    }

    // Get source slideshow
    const existing = dbHelpers.getSlideshowByName(name);
    if (!existing) {
      return res.status(404).json({
        success: false,
        error: 'Slideshow not found',
        message: `Slideshow '${name}' does not exist`
      } as ApiResponse);
    }

    // Check if new name already exists
    const newExisting = dbHelpers.getSlideshowByName(newName);
    if (newExisting) {
      return res.status(409).json({
        success: false,
        error: 'Slideshow already exists',
        message: `Slideshow '${newName}' already exists`
      } as ApiResponse);
    }

    // Create clone
    dbHelpers.createSlideshow(newName, existing.data);

    const data = JSON.parse(existing.data);
    res.status(201).json({
      success: true,
      data: {
        name: newName,
        ...data
      },
      message: `Slideshow '${name}' cloned to '${newName}'`
    } as ApiResponse<any>);
  } catch (error) {
    console.error('Error cloning slideshow:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to clone slideshow',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

/**
 * GET /api/slideshows/media/list - List available media files
 * Returns array of media files in slideshows/media directory
 */
router.get('/media/list', async (req, res) => {
  try {
    const mediaDir = path.join(__dirname, '../../slideshows/media');
    
    // Ensure directory exists
    try {
      await fs.mkdir(mediaDir, { recursive: true });
    } catch (error) {
      // Directory already exists
    }

    const files = await fs.readdir(mediaDir);
    const supportedExtensions = ['jpg', 'jpeg', 'png', 'gif', 'svg', 'avif'];
    
    const mediaFiles = await Promise.all(
      files
        .filter(file => {
          const ext = file.split('.').pop()?.toLowerCase();
          return ext && supportedExtensions.includes(ext);
        })
        .map(async file => {
          try {
            const filePath = path.join(mediaDir, file);
            const stats = await fs.stat(filePath);
            return {
              filename: file,
              path: `/slideshows/media/${file}`,
              size: stats.size,
              modified: stats.mtime.getTime()
            };
          } catch (error) {
            console.warn(`Error stat'ing media file '${file}':`, error);
            return undefined;
          };
      })
    );

    res.json({
      success: true,
      data: mediaFiles.filter(f => f !== undefined)
    } as ApiResponse<any[]>);
  } catch (error) {
    console.error('Error listing media files:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to list media files',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});
router.post('/media/upload', mediaUpload.single('media'), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({
      success: false,
      error: 'No file uploaded',
      message: 'Please select an image to upload'
    } as ApiResponse);
  }

  try {
    dbHelpers.logUpload(req.file.filename, req.file.originalname, 'media', req.file.size);
  } catch (error) {
    console.warn('Failed to log slideshow upload:', error);
  }

  res.json({
    success: true,
    data: {
      filename: req.file.filename,
      path: `/slideshows/media/${req.file.filename}`,
      size: req.file.size,
      mimeType: req.file.mimetype
    },
    message: 'Media uploaded successfully'
  } as ApiResponse);
});

export default router;