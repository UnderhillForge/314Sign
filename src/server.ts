import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import morgan from 'morgan';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import cookieParser from 'cookie-parser';

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
import { requireAuthPage } from './middleware/auth.js';
import { initializeDatabase } from './database.js';
import db from './database.js';

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

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://cdn.jsdelivr.net"],
      scriptSrcAttr: ["'unsafe-inline'"], // Allow inline event handlers
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
      fontSrc: ["'self'", "data:"],
      connectSrc: ["'self'", "*.local", "http://*.local", "https://*.local", "http://192.168.0.0/16", "http://10.0.0.0/8", "https://192.168.0.0/16", "https://10.0.0.0/8"],
      objectSrc: ["'none'"],
      upgradeInsecureRequests: [],
    },
  },
  crossOriginEmbedderPolicy: false
}));

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

// Protect admin routes BEFORE static file serving
const adminRoutes = ['start', 'edit', 'rules', 'design', 'maintenance', 'slideshows', 'remotes'];

app.use((req, res, next) => {
  // Skip API routes
  if (req.path.startsWith('/api/')) {
    return next();
  }

  // Check if requesting an admin page
  const pageMatch = req.path.match(/^\/([^\/]+)\/?$/);
  if (pageMatch) {
    const page = pageMatch[1];

    // Login page is accessible to everyone (cookies handle authentication)

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



// Static file serving (after authentication checks)
app.use(express.static(path.join(__dirname, '../public')));
app.use('/bg', express.static(path.join(__dirname, '../bg')));
app.use('/fonts', express.static(path.join(__dirname, '../fonts')));
app.use('/media', express.static(path.join(__dirname, '../media')));

// Static file serving for root directory config files (page.json, rules.json, etc.)
app.use(express.static(path.join(__dirname, '../')));

// API routes
app.use('/api/status', statusRoutes);
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

    // Check if the page exists in root directory first (like login)
    if (!fs.existsSync(pagePath)) {
      pagePath = path.join(__dirname, '../public', page, 'index.html');
    }

    // Check if the page exists
    if (fs.existsSync(pagePath)) {
      // Add cache-busting headers for all pages
      res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
      res.setHeader('Pragma', 'no-cache');
      res.setHeader('Expires', '0');
      return res.sendFile(pagePath);
    }
  }

  // Default to main index.html
  res.sendFile(path.join(__dirname, '../public/index.html'));
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

app.listen(PORT, () => {
  console.log(`314Sign server running on port ${PORT}`);
  console.log(`Serving static files from: ${path.join(__dirname, '../public')}`);
  console.log(`Database initialized at: ${path.join(process.cwd(), '314sign.db')}`);
});

export default app;