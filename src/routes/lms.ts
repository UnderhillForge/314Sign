import express from 'express';
import { authenticateToken } from './auth.js';
import { dbHelpers } from '../database.js';
import fs from 'fs';
import path from 'path';

const router = express.Router();

// Get all LMS files
router.get('/', authenticateToken, async (req, res) => {
  try {
    const lmsDir = path.join(process.cwd(), 'lms');

    // Ensure LMS directory exists
    if (!fs.existsSync(lmsDir)) {
      fs.mkdirSync(lmsDir, { recursive: true });
    }

    // Read LMS files
    const files = fs.readdirSync(lmsDir)
      .filter(file => file.endsWith('.lms'))
      .map(file => {
        const filePath = path.join(lmsDir, file);
        const stats = fs.statSync(filePath);

        return {
          name: file.replace('.lms', ''),
          filename: file,
          size: stats.size,
          modified: stats.mtime.toISOString(),
          path: filePath
        };
      });

    res.json({
      success: true,
      data: files
    });
  } catch (error) {
    console.error('Failed to list LMS files:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve LMS files'
    });
  }
});

// Get specific LMS content
router.get('/:name', async (req, res) => {
  try {
    const { name } = req.params;
    const lmsDir = path.join(process.cwd(), 'lms');
    const filePath = path.join(lmsDir, `${name}.lms`);

    if (!fs.existsSync(filePath)) {
      return res.status(404).json({
        success: false,
        error: 'LMS file not found'
      });
    }

    const content = fs.readFileSync(filePath, 'utf-8');
    res.set('Content-Type', 'application/json');
    res.send(content);

  } catch (error) {
    console.error('Failed to get LMS file:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve LMS file'
    });
  }
});

// Create/update LMS file
router.put('/:name', authenticateToken, async (req, res) => {
  try {
    const { name } = req.params;
    const { content } = req.body;

    if (!content) {
      return res.status(400).json({
        success: false,
        error: 'Content is required'
      });
    }

    // Validate JSON
    try {
      JSON.parse(content);
    } catch (e) {
      return res.status(400).json({
        success: false,
        error: 'Invalid JSON content'
      });
    }

    const lmsDir = path.join(process.cwd(), 'lms');

    // Ensure LMS directory exists
    if (!fs.existsSync(lmsDir)) {
      fs.mkdirSync(lmsDir, { recursive: true });
    }

    const filePath = path.join(lmsDir, `${name}.lms`);

    // Backup existing file if it exists
    if (fs.existsSync(filePath)) {
      const backupPath = `${filePath}.backup`;
      fs.copyFileSync(filePath, backupPath);
    }

    // Write new content
    fs.writeFileSync(filePath, content, 'utf-8');

    res.json({
      success: true,
      message: `LMS file '${name}' saved successfully`
    });

  } catch (error) {
    console.error('Failed to save LMS file:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to save LMS file'
    });
  }
});

// Delete LMS file
router.delete('/:name', authenticateToken, async (req, res) => {
  try {
    const { name } = req.params;
    const lmsDir = path.join(process.cwd(), 'lms');
    const filePath = path.join(lmsDir, `${name}.lms`);

    if (!fs.existsSync(filePath)) {
      return res.status(404).json({
        success: false,
        error: 'LMS file not found'
      });
    }

    // Remove file
    fs.unlinkSync(filePath);

    res.json({
      success: true,
      message: `LMS file '${name}' deleted successfully`
    });

  } catch (error) {
    console.error('Failed to delete LMS file:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to delete LMS file'
    });
  }
});

// Validate LMS content
router.post('/validate', authenticateToken, async (req, res) => {
  try {
    const { content } = req.body;

    if (!content) {
      return res.status(400).json({
        success: false,
        error: 'Content is required'
      });
    }

    let parsedContent;
    try {
      parsedContent = JSON.parse(content);
    } catch (e) {
      return res.status(400).json({
        success: false,
        error: 'Invalid JSON',
        details: e.message
      });
    }

    // Basic LMS structure validation
    const requiredFields = ['version', 'background', 'overlays'];
    const missingFields = requiredFields.filter(field => !parsedContent.hasOwnProperty(field));

    if (missingFields.length > 0) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields',
        details: `Missing: ${missingFields.join(', ')}`
      });
    }

    // Version check
    const supportedVersions = ['1.0', '1.1'];
    if (!supportedVersions.includes(parsedContent.version)) {
      return res.status(400).json({
        success: false,
        error: 'Unsupported LMS version',
        details: `Supported versions: ${supportedVersions.join(', ')}`
      });
    }

    res.json({
      success: true,
      message: 'LMS content is valid',
      version: parsedContent.version,
      overlays: parsedContent.overlays?.length || 0
    });

  } catch (error) {
    console.error('Validation failed:', error);
    res.status(500).json({
      success: false,
      error: 'Validation failed'
    });
  }
});

// Get LMS templates
router.get('/templates/list', authenticateToken, async (req, res) => {
  try {
    const templatesDir = path.join(process.cwd(), 'hybrid', 'templates');

    if (!fs.existsSync(templatesDir)) {
      return res.json({
        success: true,
        data: []
      });
    }

    const files = fs.readdirSync(templatesDir)
      .filter(file => file.endsWith('.json'))
      .map(file => {
        const filePath = path.join(templatesDir, file);
        const stats = fs.statSync(filePath);

        // Read template to get metadata
        let templateData = {};
        try {
          const content = fs.readFileSync(filePath, 'utf-8');
          templateData = JSON.parse(content);
        } catch (e) {
          // Ignore parsing errors for template list
        }

        return {
          name: file.replace('.json', ''),
          filename: file,
          title: templateData.title || file.replace('.json', ''),
          description: templateData.description || '',
          category: templateData.category || 'general',
          modified: stats.mtime.toISOString(),
          size: stats.size
        };
      });

    res.json({
      success: true,
      data: files
    });

  } catch (error) {
    console.error('Failed to list templates:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve templates'
    });
  }
});

// Get specific template
router.get('/templates/:name', authenticateToken, async (req, res) => {
  try {
    const { name } = req.params;
    const templatesDir = path.join(process.cwd(), 'hybrid', 'templates');
    const filePath = path.join(templatesDir, `${name}.json`);

    if (!fs.existsSync(filePath)) {
      return res.status(404).json({
        success: false,
        error: 'Template not found'
      });
    }

    const content = fs.readFileSync(filePath, 'utf-8');
    res.set('Content-Type', 'application/json');
    res.send(content);

  } catch (error) {
    console.error('Failed to get template:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve template'
    });
  }
});

// Create LMS from template
router.post('/templates/:name/create', authenticateToken, async (req, res) => {
  try {
    const { name } = req.params;
    const { targetName } = req.body;

    if (!targetName) {
      return res.status(400).json({
        success: false,
        error: 'Target name is required'
      });
    }

    // Load template
    const templatesDir = path.join(process.cwd(), 'hybrid', 'templates');
    const templatePath = path.join(templatesDir, `${name}.json`);

    if (!fs.existsSync(templatePath)) {
      return res.status(404).json({
        success: false,
        error: 'Template not found'
      });
    }

    const templateContent = fs.readFileSync(templatePath, 'utf-8');
    const templateData = JSON.parse(templateContent);

    // Create LMS file
    const lmsDir = path.join(process.cwd(), 'lms');
    if (!fs.existsSync(lmsDir)) {
      fs.mkdirSync(lmsDir, { recursive: true });
    }

    const lmsPath = path.join(lmsDir, `${targetName}.lms`);

    // Add creation metadata
    const lmsData = {
      ...templateData,
      _created_from: name,
      _created_at: new Date().toISOString(),
      _created_by: req.user?.username || 'unknown'
    };

    fs.writeFileSync(lmsPath, JSON.stringify(lmsData, null, 2), 'utf-8');

    res.json({
      success: true,
      message: `LMS '${targetName}' created from template '${name}'`,
      data: {
        name: targetName,
        template: name
      }
    });

  } catch (error) {
    console.error('Failed to create from template:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to create LMS from template'
    });
  }
});

export default router;