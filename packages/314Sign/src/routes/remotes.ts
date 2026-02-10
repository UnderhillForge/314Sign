import express from 'express';
import { authenticateToken } from './auth.js';
import { dbHelpers } from '../database.js';

const router = express.Router();

// Get all registered remotes
router.get('/', authenticateToken, async (req, res) => {
  try {
    // Use direct SQL with the raw database object
    const db = req.app.locals.db;

    // Use prepared statement for the query
    const stmt = db.prepare(`
      SELECT id, serial, code, display_name, mode, slideshow_name,
             orientation, last_seen, created_at, status, sync_enabled, cache_updated_at
      FROM remotes
      ORDER BY last_seen DESC, created_at DESC
    `);
    const remotes = stmt.all();

    res.json({
      success: true,
      data: remotes.map((remote: any) => ({
        id: remote.id,
        serial: remote.serial,
        code: remote.code,
        displayName: remote.display_name,
        mode: remote.mode,
        slideshowName: remote.slideshow_name,
        orientation: JSON.parse(remote.orientation || '{}'),
        lastSeen: remote.last_seen,
        createdAt: remote.created_at,
        status: remote.status,
        syncEnabled: !!remote.sync_enabled,
        cacheUpdatedAt: remote.cache_updated_at
      }))
    });
  } catch (error) {
    console.error('Failed to get remotes:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve remotes'
    });
  }
});

// Register a new remote by device code
router.post('/register', authenticateToken, async (req, res) => {
  try {
    const { code, displayName, mode, slideshowId, orientation, syncEnabled } = req.body;

    if (!code) {
      return res.status(400).json({
        success: false,
        error: 'Device code is required'
      });
    }

    const db = req.app.locals.db;

    // Check if remote is already registered
    const existingStmt = db.prepare('SELECT id FROM remotes WHERE code = ?');
    const existing = existingStmt.get(code);
    if (existing) {
      return res.status(409).json({
        success: false,
        error: 'Remote with this code is already registered'
      });
    }

    // Insert new remote
    const insertStmt = db.prepare(`
      INSERT INTO remotes (code, display_name, mode, slideshow_name, orientation, status, sync_enabled, created_at, last_seen)
      VALUES (?, ?, ?, ?, ?, 'active', ?, datetime('now'), datetime('now'))
    `);
    const result = insertStmt.run(
      code,
      displayName || `Remote ${code}`,
      mode || 'mirror',
      slideshowId || null,
      JSON.stringify(orientation || { hdmi1: 0, hdmi2: 0 }),
      syncEnabled ? 1 : 0
    );

    // Note: Remote config update is handled separately after registration
    // The remote device will poll for its configuration once it starts

    res.json({
      success: true,
      data: {
        id: result.lastID,
        code,
        displayName: displayName || `Remote ${code}`,
        mode: mode || 'mirror',
        slideshowId,
        orientation: orientation || { hdmi1: 0, hdmi2: 0 },
        syncEnabled: !!syncEnabled
      }
    });
  } catch (error) {
    console.error('Failed to register remote:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to register remote'
    });
  }
});

// Update remote configuration
router.put('/:id', authenticateToken, async (req, res) => {
  try {
    const { id } = req.params;
    const { displayName, mode, slideshowId, orientation, status, syncEnabled } = req.body;

    const db = req.app.locals.db;

    // Check if remote exists
    const existingStmt = db.prepare('SELECT id FROM remotes WHERE id = ?');
    const existing = existingStmt.get(id);
    if (!existing) {
      return res.status(404).json({
        success: false,
        error: 'Remote not found'
      });
    }

    // Build update query dynamically
    const updates = [];
    const params = [];

    if (displayName !== undefined) {
      updates.push('display_name = ?');
      params.push(displayName);
    }

    if (mode !== undefined) {
      updates.push('mode = ?');
      params.push(mode);
    }

    if (slideshowId !== undefined) {
      updates.push('slideshow_name = ?');
      params.push(slideshowId);
    }

    if (orientation !== undefined) {
      updates.push('orientation = ?');
      params.push(JSON.stringify(orientation));
    }

    if (status !== undefined) {
      updates.push('status = ?');
      params.push(status);
    }

    if (syncEnabled !== undefined) {
      updates.push('sync_enabled = ?');
      params.push(syncEnabled ? 1 : 0);
    }

    if (updates.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'No valid update fields provided'
      });
    }

    // Add last_seen update
    updates.push('last_seen = datetime(\'now\')');
    params.push(id);

    const query = `UPDATE remotes SET ${updates.join(', ')} WHERE id = ?`;

    db.run(query, params);

    // Get updated remote
    const updated = db.get(`
      SELECT id, serial, code, display_name, mode, slideshow_name, orientation, last_seen, status, sync_enabled, cache_updated_at
      FROM remotes WHERE id = ?
    `, [id]);

    res.json({
      success: true,
      data: {
        id: updated.id,
        serial: updated.serial,
        code: updated.code,
        displayName: updated.display_name,
        mode: updated.mode,
        slideshowName: updated.slideshow_name,
        orientation: JSON.parse(updated.orientation || '{}'),
        lastSeen: updated.last_seen,
        status: updated.status,
        syncEnabled: !!updated.sync_enabled,
        cacheUpdatedAt: updated.cache_updated_at
      }
    });
  } catch (error) {
    console.error('Failed to update remote:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to update remote'
    });
  }
});

// Unregister a remote
router.delete('/:id', authenticateToken, async (req, res) => {
  try {
    const { id } = req.params;
    const db = req.app.locals.db;

    // Check if remote exists
    const existingStmt = db.prepare('SELECT id, code FROM remotes WHERE id = ?');
    const existing = existingStmt.get(id);
    if (!existing) {
      return res.status(404).json({
        success: false,
        error: 'Remote not found'
      });
    }

    // Delete remote
    const deleteStmt = db.prepare('DELETE FROM remotes WHERE id = ?');
    deleteStmt.run(id);

    res.json({
      success: true,
      message: `Remote ${existing.code} unregistered successfully`
    });
  } catch (error) {
    console.error('Failed to unregister remote:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to unregister remote'
    });
  }
});

// Get remote configuration (for remotes to poll)
router.get('/config/:code', async (req, res) => {
  try {
    const { code } = req.params;
    const db = req.app.locals.db;

    const remoteStmt = db.prepare(`
      SELECT id, serial, display_name, mode, slideshow_name, orientation, status
      FROM remotes WHERE code = ? AND status = 'active'
    `);
    const remote = remoteStmt.get(code);

    if (!remote) {
      return res.json({
        registered: false,
        mode: 'unregistered',
        lastUpdate: new Date().toISOString()
      });
    }

    // Update last seen
    const updateStmt = db.prepare('UPDATE remotes SET last_seen = datetime(\'now\') WHERE id = ?');
    updateStmt.run(remote.id);

    res.json({
      registered: true,
      displayName: remote.display_name,
      mode: remote.mode,
      slideshowName: remote.slideshow_name,
      orientation: JSON.parse(remote.orientation || '{}'),
      lastUpdate: new Date().toISOString()
    });
  } catch (error) {
    console.error('Failed to get remote config:', error);
    res.status(500).json({
      registered: false,
      mode: 'unregistered',
      error: 'Configuration service unavailable',
      lastUpdate: new Date().toISOString()
    });
  }
});

// Heartbeat endpoint for remotes to check connectivity
router.get('/ping/:code', async (req, res) => {
  try {
    const { code } = req.params;
    const db = req.app.locals.db;

    const remoteStmt = db.prepare('SELECT id FROM remotes WHERE code = ? AND status = \'active\'');
    const remote = remoteStmt.get(code);

    if (remote) {
      // Update last seen
      const updateStmt = db.prepare('UPDATE remotes SET last_seen = datetime(\'now\') WHERE id = ?');
      updateStmt.run(remote.id);

      res.json({
        success: true,
        message: 'Remote is registered and active',
        timestamp: new Date().toISOString()
      });
    } else {
      res.status(404).json({
        success: false,
        error: 'Remote not found or not active'
      });
    }
  } catch (error) {
    console.error('Heartbeat failed:', error);
    res.status(500).json({
      success: false,
      error: 'Heartbeat service unavailable'
    });
  }
});

// Push configuration update to a registered remote
router.post('/:id/push-config', authenticateToken, async (req, res) => {
  try {
    const { id } = req.params;
    const { mainKioskUrl, mode, slideshowName, orientation } = req.body;

    const db = req.app.locals.db;

    // Get remote details
    const remoteStmt = db.prepare('SELECT id, code FROM remotes WHERE id = ? AND status = \'active\'');
    const remote = remoteStmt.get(id);
    if (!remote) {
      return res.status(404).json({
        success: false,
        error: 'Remote not found or not active'
      });
    }

    // Prepare config update
    const configUpdate: any = {
      lastUpdate: new Date().toISOString()
    };

    if (mainKioskUrl !== undefined) configUpdate.mainKioskUrl = mainKioskUrl;
    if (mode !== undefined) configUpdate.mode = mode;
    if (slideshowName !== undefined) configUpdate.slideshowName = slideshowName;
    if (orientation !== undefined) configUpdate.orientation = orientation;

    // Try to push config to remote
    try {
      const remoteHostname = `remote-${remote.code}.local`;
      const remoteConfigUrl = `http://${remoteHostname}/update-remote-config.php`;

      const response = await fetch(remoteConfigUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configUpdate)
      });

      if (response.ok) {
        // Update database with new configuration
        const updates = [];
        const params = [];

        if (mode !== undefined) {
          updates.push('mode = ?');
          params.push(mode);
        }

        if (slideshowName !== undefined) {
          updates.push('slideshow_name = ?');
          params.push(slideshowName);
        }

        if (orientation !== undefined) {
          updates.push('orientation = ?');
          params.push(JSON.stringify(orientation));
        }

        if (updates.length > 0) {
          updates.push('last_seen = datetime(\'now\')');
          params.push(id);

          const query = `UPDATE remotes SET ${updates.join(', ')} WHERE id = ?`;
          db.run(query, params);
        }

        res.json({
          success: true,
          message: `Configuration pushed to remote ${remote.code}`,
          config: configUpdate
        });
      } else {
        res.status(500).json({
          success: false,
          error: `Failed to push config to remote ${remote.code}: ${response.status}`
        });
      }
    } catch (fetchError) {
      console.error(`Failed to push config to remote ${remote.code}:`, fetchError);
      res.status(500).json({
        success: false,
        error: `Could not reach remote ${remote.code}: ${fetchError instanceof Error ? fetchError.message : String(fetchError)}`
      });
    }
  } catch (error) {
    console.error('Push config failed:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to push configuration'
    });
  }
});

// NEW ENDPOINTS FOR MASTER-REMOTE SYNC

// Get bundled content for master-remote sync (menu, rules, config, slideshow list)
router.get('/:code/content', async (req, res) => {
  try {
    const { code } = req.params;
    const db = req.app.locals.db;

    // Verify remote is registered and sync enabled
    const remoteStmt = db.prepare('SELECT id, sync_enabled FROM remotes WHERE code = ? AND status = \'active\'');
    const remote = remoteStmt.get(code);

    if (!remote || !remote.sync_enabled) {
      return res.status(404).json({
        success: false,
        error: 'Remote not found, inactive, or sync disabled'
      });
    }

    // Get current rules
    const rulesStmt = db.prepare('SELECT * FROM rules WHERE enabled = 1 ORDER BY name');
    const rules = rulesStmt.all();

    // Determine active menu based on current time and rules
    let activeMenu = 'dinner'; // default
    let activeRule = null;
    const now = new Date();
    const currentDay = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][now.getDay()];
    const currentTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

    for (const rule of rules) {
      const days = JSON.parse(rule.days || '[]');
      if (days.includes(currentDay)) {
        const { startTime, endTime } = parseTimeRange(rule.start_time, rule.end_time);
        if (isTimeInRange(currentTime, startTime, endTime)) {
          activeMenu = rule.menu_name || activeMenu;
          activeRule = rule;
          break;
        }
      }
    }

    // Get active menu content
    const menuStmt = db.prepare('SELECT content FROM menus WHERE name = ?');
    const menu = menuStmt.get(activeMenu);

    // Get config
    const configStmt = db.prepare('SELECT * FROM config');
    const configRows = configStmt.all();
    const config: any = {};
    for (const row of configRows) {
      try {
        config[row.key] = JSON.parse(row.value);
      } catch {
        config[row.key] = row.value;
      }
    }

    // Get slideshow list
    const slideshowsStmt = db.prepare('SELECT name FROM slideshows ORDER BY name');
    const slideshows = slideshowsStmt.all().map((s: any) => s.name);

    // Update remote cache time
    db.prepare('UPDATE remotes SET cache_updated_at = datetime(\'now\') WHERE code = ?').run(code);

    res.json({
      success: true,
      data: {
        activeMenu: {
          name: activeMenu,
          content: menu?.content || ''
        },
        activeRule,
        rules,
        config,
        slideshows,
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    console.error('Failed to get remote content bundle:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve content'
    });
  }
});

// Get specific menu for remote
router.get('/:code/menu/:name', async (req, res) => {
  try {
    const { code, name } = req.params;
    const db = req.app.locals.db;

    // Verify remote is registered and sync enabled
    const remoteStmt = db.prepare('SELECT id, sync_enabled FROM remotes WHERE code = ? AND status = \'active\'');
    const remote = remoteStmt.get(code);

    if (!remote || !remote.sync_enabled) {
      return res.status(404).json({
        success: false,
        error: 'Remote not found, inactive, or sync disabled'
      });
    }

    const menuStmt = db.prepare('SELECT name, content FROM menus WHERE name = ?');
    const menu = menuStmt.get(name);

    if (!menu) {
      return res.status(404).json({
        success: false,
        error: `Menu '${name}' not found`
      });
    }

    res.json({
      success: true,
      data: {
        name: menu.name,
        content: menu.content,
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    console.error('Failed to get remote menu:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve menu'
    });
  }
});

// Get slideshow for remote (JSON + media URLs)
router.get('/:code/slideshow/:name', async (req, res) => {
  try {
    const { code, name } = req.params;
    const db = req.app.locals.db;

    // Verify remote is registered and sync enabled
    const remoteStmt = db.prepare('SELECT id, sync_enabled FROM remotes WHERE code = ? AND status = \'active\'');
    const remote = remoteStmt.get(code);

    if (!remote || !remote.sync_enabled) {
      return res.status(404).json({
        success: false,
        error: 'Remote not found, inactive, or sync disabled'
      });
    }

    const slideshowStmt = db.prepare('SELECT name, data FROM slideshows WHERE name = ?');
    const slideshow = slideshowStmt.get(name);

    if (!slideshow) {
      return res.status(404).json({
        success: false,
        error: `Slideshow '${name}' not found`
      });
    }

    let slideshowData;
    try {
      slideshowData = JSON.parse(slideshow.data);
    } catch {
      slideshowData = slideshow.data;
    }

    res.json({
      success: true,
      data: {
        name: slideshow.name,
        content: slideshowData,
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    console.error('Failed to get remote slideshow:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve slideshow'
    });
  }
});

// WebSocket registration endpoint (for handshake before upgrade)
router.post('/:code/register-websocket', async (req, res) => {
  try {
    const { code } = req.params;
    const db = req.app.locals.db;

    // Verify remote is registered and sync enabled
    const remoteStmt = db.prepare('SELECT id, sync_enabled FROM remotes WHERE code = ? AND status = \'active\'');
    const remote = remoteStmt.get(code);

    if (!remote || !remote.sync_enabled) {
      return res.status(404).json({
        success: false,
        error: 'Remote not found, inactive, or sync disabled'
      });
    }

    // Return WebSocket endpoint information
    res.json({
      success: true,
      data: {
        wsEndpoint: `/ws/remotes/${code}`,
        heartbeatInterval: 30000, // 30 seconds
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    console.error('WebSocket registration failed:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to register WebSocket'
    });
  }
});

// Helper function to parse time range (handles midnight-spanning times)
function parseTimeRange(startTime: string, endTime: string) {
  return { startTime, endTime };
}

// Helper function to check if current time is within range
function isTimeInRange(current: string, start: string, end: string): boolean {
  // Convert to comparable number format (HH:MM -> HHMM)
  const currentNum = parseInt(current.replace(':', ''));
  const startNum = parseInt(start.replace(':', ''));
  const endNum = parseInt(end.replace(':', ''));

  if (startNum <= endNum) {
    // Normal range (e.g., 07:00 to 23:00)
    return currentNum >= startNum && currentNum < endNum;
  } else {
    // Midnight-spanning range (e.g., 22:00 to 07:00)
    return currentNum >= startNum || currentNum < endNum;
  }
}

export default router;