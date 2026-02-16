import express from 'express';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { exec } from 'child_process';
import { promisify } from 'util';
import { ApiResponse } from '../types/index.js';
import multer from 'multer';

const execPromise = promisify(exec);

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = express.Router();

// Configure multer for backup file uploads
const upload = multer({
  dest: '/tmp/',
  limits: { fileSize: 500 * 1024 * 1024 }, // 500MB max
  fileFilter: (req, file, cb) => {
    const filename = file.originalname.toLowerCase();
    if (filename.endsWith('.tar.gz') || filename.endsWith('.tgz') || filename.endsWith('.gz')) {
      cb(null, true);
    } else {
      cb(new Error('Only .tar.gz, .tgz, or .gz files are allowed'));
    }
  }
});

// POST /api/system/reload - Trigger kiosk reload
router.post('/reload', async (req, res) => {
  try {
    // Security: Only allow from localhost/same host (similar to PHP version)
    const clientIP = req.ip || req.connection.remoteAddress;
    const allowedHosts = ['localhost', '127.0.0.1', '::1'];

    // Check if request is from allowed host
    const isAllowed = allowedHosts.includes(clientIP as string) ||
                     (req.hostname && ['localhost', req.hostname].includes(req.hostname));

    if (!isAllowed) {
      return res.status(403).json({
        success: false,
        error: 'Access denied',
        message: 'Reload can only be triggered from localhost'
      } as ApiResponse);
    }

    const reloadFile = path.join(__dirname, '../../reload.txt');

    // Create file if it doesn't exist
    try {
      await fs.access(reloadFile);
    } catch (error) {
      // File doesn't exist, create it
      await fs.writeFile(reloadFile, '', 'utf-8');
    }

    // Write current timestamp
    const timestamp = Math.floor(Date.now() / 1000).toString();
    await fs.writeFile(reloadFile, timestamp, 'utf-8');

    res.json({
      success: true,
      message: 'Reload triggered',
      timestamp: parseInt(timestamp)
    } as ApiResponse<any>);
  } catch (error) {
    console.error('Error triggering reload:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to trigger reload',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// POST /api/system/backup - Create comprehensive backup archive
router.post('/backup', async (req, res) => {
  try {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0] + '_' + 
                      new Date().toTimeString().split(' ')[0].replace(/:/g, '-');
    const backupName = `314sign-backup-${timestamp}`;
    const backupDir = '/tmp/' + backupName;
    const archivePath = `/tmp/${backupName}.tar.gz`;

    // Create temporary backup directory
    await fs.mkdir(backupDir, { recursive: true });

    const rootDir = path.join(__dirname, '../..');

    // Copy database
    try {
      await fs.copyFile(
        path.join(rootDir, '314sign.db'),
        path.join(backupDir, '314sign.db')
      );
    } catch (e) {
      console.warn('Database file not found or could not be copied');
    }

    // Copy config.json
    try {
      await fs.copyFile(
        path.join(rootDir, 'config.json'),
        path.join(backupDir, 'config.json')
      );
    } catch (e) {
      console.warn('Config file not found or could not be copied');
    }

    // Copy fonts directory
    try {
      await execPromise(`cp -r "${path.join(rootDir, 'fonts')}" "${backupDir}/fonts"`);
    } catch (e) {
      console.warn('Fonts directory not found or could not be copied');
    }

    // Copy backgrounds
    try {
      await execPromise(`cp -r "${path.join(rootDir, 'bg')}" "${backupDir}/bg"`);
    } catch (e) {
      console.warn('Backgrounds directory not found or could not be copied');
    }

    // Copy media directory
    try {
      await execPromise(`cp -r "${path.join(rootDir, 'media')}" "${backupDir}/media"`);
    } catch (e) {
      console.warn('Media directory not found or could not be copied');
    }

    // Copy slideshows directory
    try {
      await execPromise(`cp -r "${path.join(rootDir, 'slideshows')}" "${backupDir}/slideshows"`);
    } catch (e) {
      console.warn('Slideshows directory not found or could not be copied');
    }

    // Create tar.gz archive
    await execPromise(`cd /tmp && tar -czf "${backupName}.tar.gz" "${backupName}"`);

    // Clean up temporary directory
    await execPromise(`rm -rf "${backupDir}"`);

    // Send file for download
    res.download(archivePath, `${backupName}.tar.gz`, async (err) => {
      // Clean up archive after download
      try {
        await fs.unlink(archivePath);
      } catch (e) {
        console.warn('Could not delete temporary archive:', e);
      }

      if (err) {
        console.error('Error sending backup file:', err);
      }
    });

  } catch (error) {
    console.error('Backup error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to create backup',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// POST /api/system/restore - Restore from backup archive
router.post('/restore', upload.single('backup'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No backup file provided',
        message: 'Please upload a .tar.gz backup file'
      } as ApiResponse);
    }

    const uploadPath = req.file.path;
    const extractDir = '/tmp/314sign-restore-' + Date.now();
    const rootDir = path.join(__dirname, '../..');

    // Create extraction directory
    await fs.mkdir(extractDir, { recursive: true });

    // Extract archive
    await execPromise(`tar -xzf "${uploadPath}" -C "${extractDir}"`);

    // Find the backup directory (should be the only subdirectory)
    const extractedContents = await fs.readdir(extractDir);
    const backupFolder = extractedContents.find(name => name.startsWith('314sign-backup-'));
    
    if (!backupFolder) {
      throw new Error('Invalid backup archive structure');
    }

    const backupPath = path.join(extractDir, backupFolder);

    // Stop any active processes by closing the database connection
    // (The database will be reopened automatically on next request)
    const db = req.app.locals.db;
    if (db) {
      db.close();
    }

    // Restore database
    try {
      const dbPath = path.join(backupPath, '314sign.db');
      await fs.access(dbPath);
      await execPromise(`cp "${dbPath}" "${path.join(rootDir, '314sign.db')}"`);
    } catch (e) {
      console.warn('No database file in backup');
    }

    // Restore config
    try {
      const configPath = path.join(backupPath, 'config.json');
      await fs.access(configPath);
      await execPromise(`cp "${configPath}" "${path.join(rootDir, 'config.json')}"`);
    } catch (e) {
      console.warn('No config file in backup');
    }

    // Restore fonts
    try {
      const fontsPath = path.join(backupPath, 'fonts');
      await fs.access(fontsPath);
      await execPromise(`rm -rf "${path.join(rootDir, 'fonts')}" && cp -r "${fontsPath}" "${path.join(rootDir, 'fonts')}"`);
    } catch (e) {
      console.warn('No fonts directory in backup');
    }

    // Restore backgrounds
    try {
      const bgPath = path.join(backupPath, 'bg');
      await fs.access(bgPath);
      await execPromise(`rm -rf "${path.join(rootDir, 'bg')}" && cp -r "${bgPath}" "${path.join(rootDir, 'bg')}"`);
    } catch (e) {
      console.warn('No backgrounds directory in backup');
    }

    // Restore media
    try {
      const mediaPath = path.join(backupPath, 'media');
      await fs.access(mediaPath);
      await execPromise(`rm -rf "${path.join(rootDir, 'media')}" && cp -r "${mediaPath}" "${path.join(rootDir, 'media')}"`);
    } catch (e) {
      console.warn('No media directory in backup');
    }

    // Restore slideshows
    try {
      const slideshowsPath = path.join(backupPath, 'slideshows');
      await fs.access(slideshowsPath);
      await execPromise(`rm -rf "${path.join(rootDir, 'slideshows')}" && cp -r "${slideshowsPath}" "${path.join(rootDir, 'slideshows')}"`);
    } catch (e) {
      console.warn('No slideshows directory in backup');
    }

    // Clean up temporary files
    await execPromise(`rm -rf "${extractDir}"`);
    await fs.unlink(uploadPath);

    // Reinitialize database connection
    const Database = await import('better-sqlite3');
    const newDb = new (Database.default)(path.join(rootDir, '314sign.db'));
    newDb.pragma('journal_mode = WAL');
    req.app.locals.db = newDb;

    res.json({
      success: true,
      message: 'Backup restored successfully. Please restart the service for changes to take full effect.'
    } as ApiResponse);

  } catch (error) {
    console.error('Restore error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to restore backup',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// GET /api/system/check-updates - Check GitHub for new releases
router.get('/check-updates', async (req, res) => {
  try {
    const currentVersionPath = path.join(__dirname, '../../version.txt');
    let currentVersion = '1.0.0';
    
    try {
      const versionContent = await fs.readFile(currentVersionPath, 'utf-8');
      currentVersion = versionContent.trim();
    } catch (e) {
      console.warn('Could not read current version');
    }

    // Fetch latest release from GitHub API
    const response = await fetch('https://api.github.com/repos/UnderhillForge/314Sign/releases/latest', {
      headers: {
        'Accept': 'application/vnd.github+json',
        'User-Agent': '314Sign-Updater'
      }
    });

    if (!response.ok) {
      throw new Error(`GitHub API returned ${response.status}`);
    }

    const release = await response.json() as {
      tag_name: string;
      html_url: string;
      tarball_url: string;
      body: string;
      published_at: string;
    };
    const latestVersion = release.tag_name.replace(/^v/, ''); // Remove 'v' prefix if present
    
    // Compare versions (simple string comparison for now)
    const isUpdateAvailable = latestVersion !== currentVersion && 
                              compareVersions(latestVersion, currentVersion) > 0;

    res.json({
      success: true,
      data: {
        currentVersion,
        latestVersion,
        updateAvailable: isUpdateAvailable,
        releaseUrl: release.html_url,
        downloadUrl: release.tarball_url,
        releaseNotes: release.body,
        publishedAt: release.published_at
      }
    } as ApiResponse);

  } catch (error) {
    console.error('Check updates error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to check for updates',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// POST /api/system/install-update - Download and install update from GitHub
router.post('/install-update', async (req, res) => {
  try {
    const { downloadUrl } = req.body;
    
    if (!downloadUrl) {
      return res.status(400).json({
        success: false,
        error: 'Missing download URL'
      } as ApiResponse);
    }

    const tempDir = '/tmp/314sign-update-' + Date.now();
    const tarballPath = path.join(tempDir, 'update.tar.gz');
    const rootDir = path.join(__dirname, '../..');

    // Create temp directory
    await fs.mkdir(tempDir, { recursive: true });

    // Download tarball
    console.log('Downloading update from:', downloadUrl);
    const downloadResponse = await fetch(downloadUrl, {
      headers: {
        'User-Agent': '314Sign-Updater'
      }
    });

    if (!downloadResponse.ok) {
      throw new Error(`Download failed: ${downloadResponse.status}`);
    }

    const arrayBuffer = await downloadResponse.arrayBuffer();
    await fs.writeFile(tarballPath, Buffer.from(arrayBuffer));

    // Extract tarball
    console.log('Extracting update...');
    await execPromise(`cd "${tempDir}" && tar -xzf update.tar.gz`);

    // Find extracted directory (GitHub tarballs extract to <user>-<repo>-<hash>/)
    const files = await fs.readdir(tempDir);
    const extractedDir = files.find(f => f.startsWith('UnderhillForge-314Sign-') || f.startsWith('314Sign-'));
    
    if (!extractedDir) {
      throw new Error('Could not find extracted directory');
    }

    const updatePath = path.join(tempDir, extractedDir, 'packages/314Sign');

    // Backup current version
    console.log('Creating backup of current version...');
    const backupDir = '/tmp/314sign-backup-pre-update-' + Date.now();
    await execPromise(`mkdir -p "${backupDir}" && cp -r "${rootDir}" "${backupDir}/"`);

    // Stop database connection before updating
    const db = req.app.locals.db;
    if (db) {
      db.close();
    }

    // Install update (preserve database, config, and user data)
    console.log('Installing update...');
    
    // Update source files
    await execPromise(`cp -r "${updatePath}/src" "${rootDir}/src"`);
    await execPromise(`cp -r "${updatePath}/dist" "${rootDir}/dist" || true`);
    
    // Update HTML files
    await execPromise(`cp "${updatePath}"/*.html "${rootDir}/" || true`);
    await execPromise(`cp "${updatePath}"/*.js "${rootDir}/" || true`);
    
    // Update subdirectories (preserve user data)
    const dirsToUpdate = ['design', 'edit', 'login', 'maintenance', 'remotes', 'rules', 'screens', 'debug', 'demo', 'start', 'tasks', 'legacy', 'docs'];
    for (const dir of dirsToUpdate) {
      await execPromise(`cp -r "${updatePath}/${dir}" "${rootDir}/${dir}" || true`).catch(() => {});
    }

    // Update version file
    await execPromise(`cp "${updatePath}/version.txt" "${rootDir}/version.txt" || true`);

    // Update package.json and install dependencies if changed
    const packageJsonPath = path.join(rootDir, 'package.json');
    const newPackageJsonPath = path.join(updatePath, 'package.json');
    
    try {
      await execPromise(`cp "${newPackageJsonPath}" "${packageJsonPath}"`);
      console.log('Running npm install...');
      await execPromise(`cd "${rootDir}" && npm install --production`);
    } catch (e) {
      console.warn('Could not update dependencies:', e);
    }

    // Rebuild TypeScript
    console.log('Building TypeScript...');
    await execPromise(`cd "${rootDir}/../.. && npm run build:314sign`).catch(() => {
      console.warn('TypeScript build failed, continuing anyway');
    });

    // Clean up temp directory
    await execPromise(`rm -rf "${tempDir}"`);

    // Reinitialize database
    const Database = await import('better-sqlite3');
    const newDb = new (Database.default)(path.join(rootDir, '314sign.db'));
    newDb.pragma('journal_mode = WAL');
    req.app.locals.db = newDb;

    res.json({
      success: true,
      message: 'Update installed successfully. Restart the service to complete the update.',
      backupPath: backupDir
    } as ApiResponse);

  } catch (error) {
    console.error('Install update error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to install update',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// Helper function to compare semantic versions
function compareVersions(v1: string, v2: string): number {
  const parts1 = v1.split('.').map(Number);
  const parts2 = v2.split('.').map(Number);
  
  for (let i = 0; i < Math.max(parts1.length, parts2.length); i++) {
    const part1 = parts1[i] || 0;
    const part2 = parts2[i] || 0;
    
    if (part1 > part2) return 1;
    if (part1 < part2) return -1;
  }
  
  return 0;
}

export default router;
