import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import morgan from 'morgan';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

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
import authRoutes from './routes/auth.js';
import { requireAuthPage } from './middleware/auth.js';
import { initializeDatabase } from './database.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// Security middleware
app.use(helmet({
  contentSecurityPolicy: false, // We'll handle CSP separately for kiosk mode
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

// Static file serving
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

// Protect admin routes
const adminRoutes = ['start', 'edit', 'rules', 'design', 'maintenance', 'slideshows'];

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

app.listen(PORT, () => {
  console.log(`314Sign server running on port ${PORT}`);
  console.log(`Serving static files from: ${path.join(__dirname, '../public')}`);
  console.log(`Database initialized at: ${path.join(process.cwd(), '314sign.db')}`);
});

export default app;
