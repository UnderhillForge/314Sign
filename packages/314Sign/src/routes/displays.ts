import { Router, Request, Response, NextFunction } from 'express';
import db, { dbHelpers } from '../database.js';
import { authenticateToken, requireAdmin } from './auth.js';
import {
  getXrandrOutputs,
  applyXrandrConfig,
  testDisplayOutput,
  restartServices,
  validateDisplayConfig,
  type DisplayConfig
} from '../utils/system-control.js';

const router = Router();

// Type extensions for authenticated requests
interface AuthenticatedRequest extends Request {
  user?: {
    id: number;
    username: string;
    role: string;
  };
}

// Apply authentication to all routes
router.use(authenticateToken);

/**
 * GET /api/displays
 * List all displays with current configuration and xrandr status
 */
router.get('/', requireAdmin, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const displays = dbHelpers.getAllDisplays();
    const xrandrOutputs = await getXrandrOutputs();
    
    // Enhance display data with xrandr availability
    const enhancedDisplays = displays.map(display => ({
      ...display,
      xrandr_available: xrandrOutputs.includes(display.xrandr_output)
    }));
    
    res.json({
      displays: enhancedDisplays,
      xrandr_outputs: xrandrOutputs,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Failed to get displays:', error);
    res.status(500).json({ error: 'Failed to retrieve display configuration' });
  }
});

/**
 * GET /api/displays/:port
 * Get configuration for a specific HDMI port
 */
router.get('/:port', requireAdmin, (req: AuthenticatedRequest, res: Response) => {
  try {
    const port = parseInt(req.params.port, 10);
    
    if (![0, 1].includes(port)) {
      return res.status(400).json({ error: 'Invalid HDMI port. Must be 0 or 1' });
    }
    
    const display = dbHelpers.getDisplayByPort(port);
    
    if (!display) {
      return res.status(404).json({ error: 'Display configuration not found' });
    }
    
    res.json(display);
  } catch (error) {
    console.error('Failed to get display:', error);
    res.status(500).json({ error: 'Failed to retrieve display configuration' });
  }
});

/**
 * PUT /api/displays/:port
 * Update display configuration (orientation, mode, slideshow, etc.)
 * Does NOT apply changes to xrandr - use /apply for that
 */
router.put('/:port', requireAdmin, (req: AuthenticatedRequest, res: Response) => {
  try {
    const port = parseInt(req.params.port, 10);
    
    if (![0, 1].includes(port)) {
      return res.status(400).json({ error: 'Invalid HDMI port. Must be 0 or 1' });
    }
    
    const display = dbHelpers.getDisplayByPort(port);
    if (!display) {
      return res.status(404).json({ error: 'Display not found' });
    }
    
    // Validate incoming configuration
    const validation = validateDisplayConfig(req.body);
    if (!validation.valid) {
      return res.status(400).json({ errors: validation.errors });
    }
    
    // Validate slideshow reference if present
    if (req.body.slideshow_name) {
      const slideshow = dbHelpers.getSlideshowByName(req.body.slideshow_name);
      if (!slideshow) {
        return res.status(400).json({ error: 'Referenced slideshow not found' });
      }
    }
    
    // Update the display configuration
    dbHelpers.updateDisplay(port, {
      enabled: req.body.enabled ?? display.enabled,
      guest_facing: req.body.guest_facing !== undefined
        ? (req.body.guest_facing ? 1 : 0)
        : display.guest_facing,
      orientation: req.body.orientation ?? display.orientation,
      mode: req.body.mode ?? display.mode,
      slideshow_name: req.body.slideshow_name !== undefined ? req.body.slideshow_name : display.slideshow_name,
      resolution: req.body.resolution ?? display.resolution,
      xrandr_output: req.body.xrandr_output ?? display.xrandr_output,
      position_x: req.body.position_x ?? display.position_x,
      position_y: req.body.position_y ?? display.position_y,
      refresh_rate: req.body.refresh_rate ?? display.refresh_rate
    });

    if (req.body.guest_facing) {
      dbHelpers.setGuestFacingExclusive(port);
    }
    
    const updatedDisplay = dbHelpers.getDisplayByPort(port);
    
    res.json({
      message: 'Display configuration updated (not yet applied to system)',
      display: updatedDisplay,
      requires_apply: true
    });
  } catch (error) {
    console.error('Failed to update display:', error);
    res.status(500).json({ error: 'Failed to update display configuration' });
  }
});

/**
 * POST /api/displays/:port/apply
 * Apply xrandr changes for this display (and all other configured displays)
 */
router.post('/:port/apply', requireAdmin, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const port = parseInt(req.params.port, 10);
    
    if (![0, 1].includes(port)) {
      return res.status(400).json({ error: 'Invalid HDMI port. Must be 0 or 1' });
    }
    
    // Get all displays to apply configurations
    const displays = (dbHelpers.getAllDisplays() || []) as DisplayConfig[];
    
    if (displays.length === 0) {
      return res.status(500).json({ error: 'No display configurations found' });
    }
    
    console.log(`[DISPLAYS] Applying xrandr configuration for ${displays.length} displays`);
    console.log(`[DISPLAYS] Display config:`, JSON.stringify(displays, null, 2));
    
    // Apply xrandr configuration for all displays
    const success = await applyXrandrConfig(displays);
    
    if (!success) {
      return res.status(500).json({
        error: 'Failed to apply xrandr configuration',
        details: 'Check system logs (journalctl -u 314sign-web) for xrandr errors',
        displays_attempted: displays.length
      });
    }
    
    res.json({
      message: 'Display configuration applied successfully',
      displays_affected: displays.length,
      timestamp: new Date().toISOString(),
      command_executed: true
    });
  } catch (error) {
    console.error('Failed to apply display configuration:', error);
    res.status(500).json({
      error: 'Failed to apply display configuration',
      details: error instanceof Error ? error.message : String(error)
    });
  }
});

/**
 * POST /api/displays/:port/test
 * Send a test signal to the display (brief brightness pulse)
 */
router.post('/:port/test', requireAdmin, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const port = parseInt(req.params.port, 10);
    
    if (![0, 1].includes(port)) {
      return res.status(400).json({ error: 'Invalid HDMI port. Must be 0 or 1' });
    }
    
    const display = dbHelpers.getDisplayByPort(port);
    
    if (!display) {
      return res.status(404).json({ error: 'Display not found' });
    }
    
    console.log(`[TEST DISPLAY] Testing output ${display.xrandr_output} on HDMI ${port}`);
    
    const success = await testDisplayOutput(display.xrandr_output);
    
    res.json({
      message: success
        ? `Test signal sent to ${display.xrandr_output}`
        : `Failed to send test signal to ${display.xrandr_output}`,
      xrandr_output: display.xrandr_output,
      hdmi_port: port,
      success,
      details: success ? 'Screen should briefly dim' : 'Check if xrandr and DISPLAY are properly configured'
    });
  } catch (error) {
    console.error('Failed to test display:', error);
    res.status(500).json({
      error: 'Failed to send test signal',
      details: error instanceof Error ? error.message : String(error)
    });
  }
});

/**
 * POST /api/restart
 * Restart X server and web service
 * This is destructive - requires confirmation from user via query param
 */
router.post('/system/restart', requireAdmin, async (req: AuthenticatedRequest, res: Response) => {
  try {
    // Require explicit confirmation
    if (req.query.confirm !== 'true') {
      return res.status(400).json({
        error: 'Restart requires confirmation',
        message: 'Pass ?confirm=true to proceed',
        warning: 'This will restart the X server and web service, causing a brief interruption'
      });
    }
    
    console.warn(`[ADMIN ACTION] ${req.user?.username} initiated system restart`);
    
    const result = await restartServices();
    
    res.json({
      message: 'Service restart initiated',
      results: result,
      note: 'Services are restarting. The web interface may be unavailable for 30 seconds.'
    });
  } catch (error) {
    console.error('Failed to restart services:', error);
    res.status(500).json({ error: 'Failed to restart services' });
  }
});

export default router;
