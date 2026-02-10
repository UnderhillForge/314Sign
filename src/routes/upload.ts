import express from 'express';
import multer from 'multer';
import path from 'path';
import fs from 'fs/promises';
import { fileURLToPath } from 'url';
import { UploadResult, ApiResponse } from '../types/index.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = express.Router();

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: async (req, file, cb) => {
    let uploadDir = '';

    // Determine upload directory based on field name or request path
    if (file.fieldname === 'background' || req.path.includes('/bg')) {
      uploadDir = path.join(__dirname, '../../bg');
    } else if (file.fieldname === 'media' || req.path.includes('/media')) {
      uploadDir = path.join(__dirname, '../../media');
    } else if (file.fieldname === 'logo' || req.path.includes('/logo')) {
      uploadDir = path.join(__dirname, '../../logos');
    } else {
      uploadDir = path.join(__dirname, '../../uploads');
    }

    // Ensure directory exists
    try {
      await fs.access(uploadDir);
    } catch (error) {
      await fs.mkdir(uploadDir, { recursive: true });
    }

    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    // Generate unique filename with timestamp
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    const ext = path.extname(file.originalname);
    const basename = path.basename(file.originalname, ext);
    cb(null, `${basename}-${uniqueSuffix}${ext}`);
  }
});

const upload = multer({
  storage,
  limits: {
    fileSize: 50 * 1024 * 1024, // 50MB limit
  },
  fileFilter: (req, file, cb) => {
    // Allow images, videos, and documents
    const allowedTypes = [
      'image/jpeg',
      'image/png',
      'image/gif',
      'image/webp',
      'video/mp4',
      'video/webm',
      'video/ogg',
      'application/pdf',
      'text/plain'
    ];

    if (allowedTypes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error(`File type ${file.mimetype} not allowed`));
    }
  }
});

// POST /api/upload/bg - Upload background image
router.post('/bg', upload.single('background'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No file uploaded',
        message: 'Please select a background image to upload'
      } as ApiResponse);
    }

    const result: UploadResult = {
      filename: req.file.filename,
      url: `/bg/${req.file.filename}`,
      size: req.file.size,
      type: req.file.mimetype
    };

    res.json({
      success: true,
      data: result,
      message: 'Background uploaded successfully'
    } as ApiResponse<UploadResult>);
  } catch (error) {
    console.error('Error uploading background:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to upload background',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// POST /api/upload/media - Upload media file
router.post('/media', upload.single('media'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No file uploaded',
        message: 'Please select a media file to upload'
      } as ApiResponse);
    }

    const result: UploadResult = {
      filename: req.file.filename,
      url: `/media/${req.file.filename}`,
      size: req.file.size,
      type: req.file.mimetype
    };

    res.json({
      success: true,
      data: result,
      message: 'Media file uploaded successfully'
    } as ApiResponse<UploadResult>);
  } catch (error) {
    console.error('Error uploading media:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to upload media file',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// POST /api/upload/logo - Upload logo
router.post('/logo', upload.single('logo'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No file uploaded',
        message: 'Please select a logo to upload'
      } as ApiResponse);
    }

    const result: UploadResult = {
      filename: req.file.filename,
      url: `/logos/${req.file.filename}`,
      size: req.file.size,
      type: req.file.mimetype
    };

    res.json({
      success: true,
      data: result,
      message: 'Logo uploaded successfully'
    } as ApiResponse<UploadResult>);
  } catch (error) {
    console.error('Error uploading logo:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to upload logo',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// POST /api/upload - General file upload (for design interface)
router.post('/', upload.single('background'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No file uploaded',
        message: 'Please select a file to upload'
      } as ApiResponse);
    }

    const result: UploadResult = {
      filename: req.file.filename,
      url: `/bg/${req.file.filename}`,
      size: req.file.size,
      type: req.file.mimetype
    };

    res.json({
      success: true,
      data: result,
      message: 'File uploaded successfully'
    } as ApiResponse<UploadResult>);
  } catch (error) {
    console.error('Error uploading file:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to upload file',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// POST /api/upload/general - General file upload
router.post('/general', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No file uploaded',
        message: 'Please select a file to upload'
      } as ApiResponse);
    }

    const result: UploadResult = {
      filename: req.file.filename,
      url: `/uploads/${req.file.filename}`,
      size: req.file.size,
      type: req.file.mimetype
    };

    res.json({
      success: true,
      data: result,
      message: 'File uploaded successfully'
    } as ApiResponse<UploadResult>);
  } catch (error) {
    console.error('Error uploading file:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to upload file',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// DELETE /api/upload/bg/:filename - Delete background image
router.delete('/bg/:filename', async (req, res) => {
  try {
    const { filename } = req.params;

    if (!filename) {
      return res.status(400).json({
        success: false,
        error: 'Missing filename',
        message: 'Filename parameter is required'
      } as ApiResponse);
    }

    // Validate filename to prevent directory traversal
    if (filename.includes('..') || filename.includes('/') || filename.includes('\\')) {
      return res.status(400).json({
        success: false,
        error: 'Invalid filename',
        message: 'Filename contains invalid characters'
      } as ApiResponse);
    }

    const filePath = path.join(__dirname, '../../bg', filename);

    // Check if file exists
    try {
      await fs.access(filePath);
    } catch (error) {
      return res.status(404).json({
        success: false,
        error: 'File not found',
        message: `Background image '${filename}' does not exist`
      } as ApiResponse);
    }

    // Don't allow deletion of default background images
    const defaultImages = ['backgd.jpg', 'backgd2.avif'];
    if (defaultImages.includes(filename)) {
      return res.status(403).json({
        success: false,
        error: 'Cannot delete default image',
        message: 'Default background images cannot be deleted'
      } as ApiResponse);
    }

    // Delete the file
    await fs.unlink(filePath);

    res.json({
      success: true,
      message: `Background image '${filename}' deleted successfully`
    } as ApiResponse);
  } catch (error) {
    console.error('Error deleting background image:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to delete background image',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// Error handling for multer
router.use((error: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  if (error instanceof multer.MulterError) {
    if (error.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({
        success: false,
        error: 'File too large',
        message: 'File size exceeds the 50MB limit'
      } as ApiResponse);
    }
  }

  if (error.message.includes('not allowed')) {
    return res.status(400).json({
      success: false,
      error: 'Invalid file type',
      message: error.message
    } as ApiResponse);
  }

  next(error);
});

export default router;
