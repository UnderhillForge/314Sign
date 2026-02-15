import express from 'express';
import { dbHelpers } from '../database.js';
import { applyXrandrConfig, type DisplayConfig } from '../utils/system-control.js';

const router = express.Router();

function isLocalRequest(req: express.Request): boolean {
  const ip = req.ip || req.connection.remoteAddress || '';
  const hostname = req.hostname || '';

  if (ip === '127.0.0.1' || ip === '::1' || ip === '::ffff:127.0.0.1') {
    return true;
  }

  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return true;
  }

  return false;
}

router.use((req, res, next) => {
  if (!isLocalRequest(req)) {
    return res.status(403).json({
      success: false,
      error: 'Access denied',
      message: 'Kiosk endpoints are restricted to localhost'
    });
  }
  next();
});

router.get('/displays', (req, res) => {
  try {
    const displays = dbHelpers.getAllDisplays();
    res.json({
      success: true,
      data: displays,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Failed to get kiosk displays:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve display configuration'
    });
  }
});

router.post('/displays/apply', async (req, res) => {
  try {
    const displays = (dbHelpers.getAllDisplays() || []) as DisplayConfig[];

    if (displays.length === 0) {
      return res.status(500).json({
        success: false,
        error: 'No display configurations found'
      });
    }

    console.log(`[KIOSK] Applying xrandr configuration for ${displays.length} displays`);
    const success = await applyXrandrConfig(displays);

    if (!success) {
      return res.status(500).json({
        success: false,
        error: 'Failed to apply xrandr configuration'
      });
    }

    res.json({
      success: true,
      message: 'Display configuration applied successfully',
      displays_affected: displays.length,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Failed to apply kiosk display configuration:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to apply display configuration',
      details: error instanceof Error ? error.message : String(error)
    });
  }
});

export default router;
