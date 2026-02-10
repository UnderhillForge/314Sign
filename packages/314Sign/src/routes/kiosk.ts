import express from 'express';
import { dbHelpers } from '../database.js';

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

export default router;
