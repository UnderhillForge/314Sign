import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import morgan from 'morgan';
import path from 'path';
import fs from 'fs';
import https from 'https';
import tls from 'tls';
import { fileURLToPath } from 'url';
import cookieParser from 'cookie-parser';
import { WebSocketServer } from 'ws';
import http from 'http';

// Routes
import statusRoutes from './routes/status.js';
import uploadRoutes from './routes/upload.js';
import configRoutes from './routes/config.js';
import menuRoutes from './routes/menu.js';
import rulesRoutes from './routes/rules.js';
import slideshowsRoutes from './routes/slideshows.js';
import menuControlRoutes from './routes/menu-control.js';
import systemRoutes from './routes/system.js';
import fontsRoutes from './routes/fonts.js';
import backgroundsRoutes from './routes/backgrounds.js';
import authRoutes, { authenticateToken, requireAdmin } from './routes/auth.js';
import remotesRoutes from './routes/remotes.js';
import displaysRoutes from './routes/displays.js';
import kioskRoutes from './routes/kiosk.js';
import weatherRoutes from './routes/weather.js';
import { requireAuthPage } from './middleware/auth.js';
import db, { dbHelpers, initializeDatabase } from './database.js';

// Debug log capture
let logBuffer: string[] = [];
const originalLog = console.log;
const originalError = console.error;
const originalWarn = console.warn;

console.log = (...args) => {
  const message = args.join(' ');
  const timestamped = `[${new Date().toISOString()}] ${message}`;
  logBuffer.push(timestamped);
  if (logBuffer.length > 200) logBuffer.shift();
  originalLog(...args);
};

console.error = (...args) => {
  const message = args.join(' ');
  const timestamped = `[${new Date().toISOString()}] ERROR: ${message}`;
  logBuffer.push(timestamped);
  if (logBuffer.length > 200) logBuffer.shift();
  originalError(...args);
};

console.warn = (...args) => {
  const message = args.join(' ');
  const timestamped = `[${new Date().toISOString()}] WARN: ${message}`;
  logBuffer.push(timestamped);
  if (logBuffer.length > 200) logBuffer.shift();
  originalWarn(...args);
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 80;
const HTTP_PORT = process.env.HTTP_PORT || PORT;
const HTTPS_PORT = process.env.HTTPS_PORT || 443;
const SSL_DIR = path.join(__dirname, '../ssl');
const SSL_CERT_PATH = path.join(SSL_DIR, '314sign.crt');
const SSL_KEY_PATH = path.join(SSL_DIR, '314sign.key');
const HTTPS_AVAILABLE = fs.existsSync(SSL_CERT_PATH) && fs.existsSync(SSL_KEY_PATH);

// Security middleware (HSTS disabled to allow both HTTP and HTTPS)
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://cdn.jsdelivr.net"],
      scriptSrcAttr: ["'unsafe-inline'"], // Allow inline event handlers
      styleSrc: ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://fonts.googleapis.com"],
      imgSrc: ["'self'", "data:", "https:"],
      fontSrc: ["'self'", "data:", "https://fonts.gstatic.com", "https://fonts.googleapis.com"],
      connectSrc: ["'self'", "localhost", "127.0.0.1", "*.local", "http://*.local", "https://*.local", "http://192.168.0.0/16", "http://10.0.0.0/8", "https://192.168.0.0/16", "https://10.0.0.0/8"],
      objectSrc: ["'none'"],
      mediaSrc: ["'self'"],
    },
  },
  crossOriginEmbedderPolicy: false,
  crossOriginOpenerPolicy: false,
  crossOriginResourcePolicy: { policy: "cross-origin" }, // Allow loading from any origin
  originAgentCluster: false,
  hsts: false,  // Disable HSTS completely
}));

// Explicitly remove HSTS header if helmet added it
app.use((req, res, next) => {
  res.removeHeader('Strict-Transport-Security');
  
  // Remove upgrade-insecure-requests from CSP to allow HTTP
  const csp = res.getHeader('Content-Security-Policy');
  if (csp && typeof csp === 'string') {
    const updated = csp.replace(/;\s*upgrade-insecure-requests/, '')
                       .replace(/upgrade-insecure-requests;\s*/, '')
                       .replace(/upgrade-insecure-requests$/, '');
    res.setHeader('Content-Security-Policy', updated);
  }
  next();
});

// Serve favicon.ico explicitly to avoid browser errors
app.get('/favicon.ico', (req, res) => {
  const icoPath = path.join(__dirname, '../favicon.ico');
  const svgPath = path.join(__dirname, '../favicon.svg');
  if (fs.existsSync(icoPath)) {
    return res.sendFile(icoPath);
  }
  if (fs.existsSync(svgPath)) {
    return res.sendFile(svgPath);
  }
  return res.status(204).end();
});

// CORS for development
app.use(cors());

// Compression
app.use(compression());

// Logging
app.use(morgan('combined'));

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Cookie parsing for authentication
app.use(cookieParser());

// Redirect HTTP admin routes to HTTPS (for security)
const adminRoutes = ['start', 'edit', 'rules', 'design', 'maintenance', 'slideshows', 'remotes', 'screens'];

app.use((req, res, next) => {
  // Determine if this is HTTPS: check TLS socket, x-forwarded-proto, or req.secure
  const isHttps = req.socket instanceof tls.TLSSocket || 
                  req.secure || 
                  (req.get('x-forwarded-proto') === 'https');
  
  if (!isHttps && req.method === 'GET') {
    // Check if requesting an admin page
    const pageMatch = req.path.match(/^\/([^\/]+)\/?$/);
    if (pageMatch) {
      const page = pageMatch[1];
      
      // Redirect admin routes from HTTP to HTTPS
      if (adminRoutes.includes(page)) {
        const hostname = req.hostname;
        const HTTPS_PORT = process.env.HTTPS_PORT || 443;
        const redirectUrl = HTTPS_PORT === 443 
          ? `https://${hostname}${req.path}`
          : `https://${hostname}:${HTTPS_PORT}${req.path}`;
        console.log(`[HTTP->HTTPS Redirect] ${req.path} redirecting to ${redirectUrl}`);
        return res.redirect(307, redirectUrl); // 307 preserves method
      }
    }
  }
  
  next();
});

// Protect admin routes BEFORE static file serving
app.use((req, res, next) => {
  // Skip API routes
  if (req.path.startsWith('/api/')) {
    return next();
  }

  // Check if requesting an admin page
  const pageMatch = req.path.match(/^\/([^\/]+)\/?$/);
  if (pageMatch) {
    const page = pageMatch[1];

    if (adminRoutes.includes(page)) {
      // This is an admin page, prevent caching and check authentication
      res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
      res.setHeader('Pragma', 'no-cache');
      res.setHeader('Expires', '0');
      return requireAuthPage(req, res, next);
    }
  }

  next();
});

app.get(['/guest', '/guest/'], (req, res) => {
  try {
    const displays = dbHelpers.getAllDisplays();
    const guestDisplay = displays.find((display: any) => display.guest_facing);
    if (!guestDisplay) {
      return res.redirect('/');
    }

    if (guestDisplay.mode === 'slideshow' && guestDisplay.slideshow_name) {
      const slideshow = encodeURIComponent(guestDisplay.slideshow_name);
      return res.redirect(`/?slideshow=${slideshow}&guest=1`);
    }

    return res.redirect('/?guest=1');
  } catch (error) {
    console.error('Failed to resolve guest display:', error);
    return res.redirect('/');
  }
});



// Disable caching for HTML pages to ensure fresh loads
app.use((req, res, next) => {
  if (req.path.endsWith('.html') || req.path === '/' || req.path === '') {
    res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
    res.setHeader('Pragma', 'no-cache');
    res.setHeader('Expires', '0');
  }
  next();
});

// Static file serving (after authentication checks)
app.use('/bg', express.static(path.join(__dirname, '../bg')));
app.use('/fonts', express.static(path.join(__dirname, '../fonts')));
app.use('/media', express.static(path.join(__dirname, '../media')));

// Static file serving for all root directory files (pages, config, etc.)
app.use(express.static(path.join(__dirname, '../')));

// API routes
app.use('/api', statusRoutes);
app.use('/api/upload', uploadRoutes);
app.use('/api/config', configRoutes);
app.use('/api/menu', menuRoutes);
app.use('/api/rules', rulesRoutes);
app.use('/api/slideshows', slideshowsRoutes);
app.use('/api/menu-control', menuControlRoutes);
app.use('/api/system', systemRoutes);
app.use('/api/auth', authRoutes);
app.use('/api/fonts', fontsRoutes);
app.use('/api/backgrounds', backgroundsRoutes);
app.use('/api/remotes', remotesRoutes);
app.use('/api/displays', displaysRoutes);
app.use('/api/kiosk', kioskRoutes);
app.use('/api/weather', weatherRoutes);

// Debug logs endpoint (admin only)
app.get('/api/debug/logs', authenticateToken, requireAdmin, (req, res) => {
  res.json({
    success: true,
    logs: logBuffer.slice(-100), // Return last 100 log entries
    timestamp: new Date().toISOString()
  });
});

// Serve index.html for all non-API routes (SPA fallback)
app.use((req, res, next) => {
  // Skip API routes
  if (req.path.startsWith('/api/')) {
    return res.status(404).json({ error: 'API endpoint not found' });
  }

  // Check if requesting a specific page
  const pageMatch = req.path.match(/^\/([^\/]+)\/?$/);
  if (pageMatch) {
    const page = pageMatch[1];
    let pagePath = path.join(__dirname, '../', page, 'index.html');

    // Check if the page exists
    if (fs.existsSync(pagePath)) {
      // Add cache-busting headers for all pages
      res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
      res.setHeader('Pragma', 'no-cache');
      res.setHeader('Expires', '0');
      return res.sendFile(pagePath);
    }
  }

  // Default to main index.html or start page
  const indexPath = path.join(__dirname, '../index.html');
  if (fs.existsSync(indexPath)) {
    // Add cache-busting headers for index.html
    res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
    res.setHeader('Pragma', 'no-cache');
    res.setHeader('Expires', '0');
    return res.sendFile(indexPath);
  }
  res.status(404).json({ error: 'Page not found' });
});

// Error handling
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('Error:', err);
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : 'Something went wrong'
  });
});

// Initialize database before starting server
await initializeDatabase();

// Attach database instance to app locals for routes to use
app.locals.db = db;

// WebSocket server setup for master-remote sync
const wsClients = new Map<string, any[]>(); // Map of remote codes to connected WebSocket clients

function broadcastToRemote(remoteCode: string, message: any) {
  if (wsClients.has(remoteCode)) {
    const clients = wsClients.get(remoteCode)!;
    for (const client of clients) {
      if (client.readyState === 1) { // WebSocket.OPEN
        try {
          client.send(JSON.stringify(message));
        } catch (error) {
          console.error(`Failed to send message to remote ${remoteCode}:`, error);
        }
      }
    }
  }
}

function broadcastToAllRemotes(message: any) {
  for (const [remoteCode, clients] of wsClients.entries()) {
    for (const client of clients) {
      if (client.readyState === 1) { // WebSocket.OPEN
        try {
          client.send(JSON.stringify(message));
        } catch (error) {
          console.error(`Failed to broadcast to remote ${remoteCode}:`, error);
        }
      }
    }
  }
}

// Expose broadcast functions globally for routes to use
app.locals.broadcastToRemote = broadcastToRemote;
app.locals.broadcastToAllRemotes = broadcastToAllRemotes;

// Start HTTP server
const httpServer = http.createServer(app);

// Attach WebSocket server to HTTP server
const wss = new WebSocketServer({ server: httpServer, path: '/ws/remotes/:code' });

wss.on('connection', (ws: any, req: http.IncomingMessage) => {
  try {
    // Extract remote code from URL
    const urlMatch = req.url?.match(/\/ws\/remotes\/([a-zA-Z0-9]+)$/);
    if (!urlMatch || !urlMatch[1]) {
      ws.close(1008, 'Invalid remote code');
      return;
    }

    const remoteCode = urlMatch[1];

    // Verify remote is registered and sync enabled
    const remoteStmt = db.prepare('SELECT id, sync_enabled FROM remotes WHERE code = ? AND status = \'active\'');
    const remote = remoteStmt.get(remoteCode) as any;

    if (!remote || !remote.sync_enabled) {
      ws.close(1008, 'Remote not found, inactive, or sync disabled');
      return;
    }

    // Register client
    if (!wsClients.has(remoteCode)) {
      wsClients.set(remoteCode, []);
    }
    wsClients.get(remoteCode)!.push(ws);

    // Update last seen
    db.prepare('UPDATE remotes SET last_seen = datetime(\'now\') WHERE code = ?').run(remoteCode);

    console.log(`Remote ${remoteCode} connected via WebSocket`);

    // Send welcome message
    ws.send(JSON.stringify({
      type: 'connected',
      remoteCode,
      heartbeatInterval: 30000,
      timestamp: new Date().toISOString()
    }));

    // Handle messages from remote
    ws.on('message', (data: Buffer) => {
      try {
        const message = JSON.parse(data.toString());
        
        if (message.type === 'pong' || message.type === 'heartbeat') {
          // Update last seen on heartbeat
          db.prepare('UPDATE remotes SET last_seen = datetime(\'now\') WHERE code = ?').run(remoteCode);
        } else if (message.type === 'cache-update-ack') {
          // Remote acknowledged cache update
          console.log(`Remote ${remoteCode} acknowledged cache update`);
        }
      } catch (error) {
        console.error(`Failed to process WebSocket message from ${remoteCode}:`, error);
      }
    });

    // Handle client disconnect
    ws.on('close', () => {
      console.log(`Remote ${remoteCode} disconnected from WebSocket`);
      const clients = wsClients.get(remoteCode) || [];
      const index = clients.indexOf(ws);
      if (index > -1) {
        clients.splice(index, 1);
      }
      if (clients.length === 0) {
        wsClients.delete(remoteCode);
      }
    });

    ws.on('error', (error: Error) => {
      console.error(`WebSocket error for remote ${remoteCode}:`, error);
    });
  } catch (error) {
    console.error('WebSocket connection error:', error);
    ws.close(1011, 'Internal server error');
  }
});

// Start HTTP server
httpServer.listen(HTTP_PORT, () => {
  const redirectNotice = HTTPS_AVAILABLE ? ' (redirects to HTTPS)' : '';
  console.log(`314Sign HTTP server running on port ${HTTP_PORT}${redirectNotice}`);
});

// Start HTTPS server if certificates are available
if (HTTPS_AVAILABLE) {
  const sslOptions = {
    cert: fs.readFileSync(SSL_CERT_PATH),
    key: fs.readFileSync(SSL_KEY_PATH)
  };

  const httpsServer = https.createServer(sslOptions, app);
  
  // Attach WebSocket server to HTTPS server as well
  const wssSecure = new WebSocketServer({ server: httpsServer, path: '/ws/remotes/:code' });

  wssSecure.on('connection', (ws: any, req: http.IncomingMessage) => {
    try {
      // Extract remote code from URL
      const urlMatch = req.url?.match(/\/ws\/remotes\/([a-zA-Z0-9]+)$/);
      if (!urlMatch || !urlMatch[1]) {
        ws.close(1008, 'Invalid remote code');
        return;
      }

      const remoteCode = urlMatch[1];

      // Verify remote is registered and sync enabled
      const remoteStmt = db.prepare('SELECT id, sync_enabled FROM remotes WHERE code = ? AND status = \'active\'');
      const remote = remoteStmt.get(remoteCode) as any;

      if (!remote || !remote.sync_enabled) {
        ws.close(1008, 'Remote not found, inactive, or sync disabled');
        return;
      }

      // Register client
      if (!wsClients.has(remoteCode)) {
        wsClients.set(remoteCode, []);
      }
      wsClients.get(remoteCode)!.push(ws);

      // Update last seen
      db.prepare('UPDATE remotes SET last_seen = datetime(\'now\') WHERE code = ?').run(remoteCode);

      console.log(`Remote ${remoteCode} connected via WebSocket (HTTPS)`);

      // Send welcome message
      ws.send(JSON.stringify({
        type: 'connected',
        remoteCode,
        heartbeatInterval: 30000,
        timestamp: new Date().toISOString()
      }));

      // Handle messages from remote
      ws.on('message', (data: Buffer) => {
        try {
          const message = JSON.parse(data.toString());
          
          if (message.type === 'pong' || message.type === 'heartbeat') {
            // Update last seen on heartbeat
            db.prepare('UPDATE remotes SET last_seen = datetime(\'now\') WHERE code = ?').run(remoteCode);
          } else if (message.type === 'cache-update-ack') {
            // Remote acknowledged cache update
            console.log(`Remote ${remoteCode} acknowledged cache update`);
          }
        } catch (error) {
          console.error(`Failed to process WebSocket message from ${remoteCode}:`, error);
        }
      });

      // Handle client disconnect
      ws.on('close', () => {
        console.log(`Remote ${remoteCode} disconnected from WebSocket (HTTPS)`);
        const clients = wsClients.get(remoteCode) || [];
        const index = clients.indexOf(ws);
        if (index > -1) {
          clients.splice(index, 1);
        }
        if (clients.length === 0) {
          wsClients.delete(remoteCode);
        }
      });

      ws.on('error', (error: Error) => {
        console.error(`WebSocket error for remote ${remoteCode}:`, error);
      });
    } catch (error) {
      console.error('WebSocket connection error (HTTPS):', error);
      ws.close(1011, 'Internal server error');
    }
  });

  httpsServer.listen(HTTPS_PORT, () => {
    console.log(`314Sign HTTPS server running on port ${HTTPS_PORT}`);
    console.log(`Serving static files from: ${path.join(__dirname, '../')}`);
    console.log(`Database initialized at: ${path.join(process.cwd(), '314sign.db')}`);
    console.log(`SSL Certificate: ${SSL_CERT_PATH}`);
  });
} else {
  console.warn('SSL certificate or key not found. HTTPS server not started.');
}

export default app;