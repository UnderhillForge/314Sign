import express from 'express';
import { authenticateToken } from './auth.js';

const router = express.Router();

// Get all registered remotes
router.get('/', authenticateToken, async (req, res) => {
  try {
    const db = req.app.locals.db;
    const remotes = await db.all(`
      SELECT id, serial, code, display_name, mode, slideshow_name,
             orientation, last_seen, created_at, status
      FROM remotes
      ORDER BY last_seen DESC, created_at DESC
    `);

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
        status: remote.status
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
    const { code, displayName, mode, slideshowId, orientation } = req.body;

    if (!code) {
      return res.status(400).json({
        success: false,
        error: 'Device code is required'
      });
    }

    const db = req.app.locals.db;

    // Check if remote is already registered
    const existing = await db.get('SELECT id FROM remotes WHERE code = ?', [code]);
    if (existing) {
      return res.status(409).json({
        success: false,
        error: 'Remote with this code is already registered'
      });
    }

    // Insert new remote
    const result = await db.run(`
      INSERT INTO remotes (code, display_name, mode, slideshow_name, orientation, status, created_at, last_seen)
      VALUES (?, ?, ?, ?, ?, 'active', datetime('now'), datetime('now'))
    `, [
      code,
      displayName || `Remote ${code}`,
      mode || 'mirror',
      slideshowId || null,
      JSON.stringify(orientation || { hdmi1: 0, hdmi2: 0 })
    ]);

    // Try to update the remote device's configuration with main kiosk URL
    // The remote should be accessible at remote-{code}.local
    try {
      const remoteHostname = `remote-${code}.local`;
      const remoteConfigUrl = `http://${remoteHostname}/update-remote-config.php`;

      // Get the main kiosk's hostname for the remote to connect to
      const mainKioskHostname = req.headers.host?.split(':')[0] || 'localhost';

      const remoteConfig = {
        registered: true,
        displayName: displayName || `Remote ${code}`,
        mode: mode || 'mirror',
        slideshowName: slideshowId || null,
        mainKioskUrl: `http://${mainKioskHostname}`,
        orientation: orientation || { hdmi1: 0, hdmi2: 0 },
        lastUpdate: new Date().toISOString()
      };

      // Try to update the remote's config via the PHP endpoint
      fetch(remoteConfigUrl, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(remoteConfig)
      }).catch(err => {
        console.log(`Could not update remote ${code} config (normal for initial setup):`, err.message);
      });

    } catch (error) {
      console.log(`Failed to configure remote ${code}:`, error instanceof Error ? error.message : String(error));
    }

    res.json({
      success: true,
      data: {
        id: result.lastID,
        code,
        displayName: displayName || `Remote ${code}`,
        mode: mode || 'mirror',
        slideshowId,
        orientation: orientation || { hdmi1: 0, hdmi2: 0 }
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
    const { displayName, mode, slideshowId, orientation, status } = req.body;

    const db = req.app.locals.db;

    // Check if remote exists
    const existing = await db.get('SELECT id FROM remotes WHERE id = ?', [id]);
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

    await db.run(query, params);

    // Get updated remote
    const updated = await db.get(`
      SELECT id, serial, code, display_name, mode, slideshow_name, orientation, last_seen, status
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
        status: updated.status
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
    const existing = await db.get('SELECT id, code FROM remotes WHERE id = ?', [id]);
    if (!existing) {
      return res.status(404).json({
        success: false,
        error: 'Remote not found'
      });
    }

    // Delete remote
    await db.run('DELETE FROM remotes WHERE id = ?', [id]);

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

    const remote = await db.get(`
      SELECT id, serial, display_name, mode, slideshow_name, orientation, status
      FROM remotes WHERE code = ? AND status = 'active'
    `, [code]);

    if (!remote) {
      return res.json({
        registered: false,
        mode: 'unregistered',
        lastUpdate: new Date().toISOString()
      });
    }

    // Update last seen
    await db.run('UPDATE remotes SET last_seen = datetime(\'now\') WHERE id = ?', [remote.id]);

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

    const remote = await db.get('SELECT id FROM remotes WHERE code = ? AND status = \'active\'', [code]);

    if (remote) {
      // Update last seen
      await db.run('UPDATE remotes SET last_seen = datetime(\'now\') WHERE id = ?', [remote.id]);

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
    const remote = await db.get('SELECT id, code FROM remotes WHERE id = ? AND status = \'active\'', [id]);
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
          await db.run(query, params);
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

export default router;
