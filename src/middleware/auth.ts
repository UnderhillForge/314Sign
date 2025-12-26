import { Request, Response, NextFunction } from 'express';
import { authenticateToken } from '../routes/auth.js';

// Middleware to protect admin routes
export function requireAuth(req: Request, res: Response, next: NextFunction) {
  // Check for token in Authorization header
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    // Check for token in query parameter (for GET requests from frontend)
    const queryToken = req.query.token as string;
    if (queryToken) {
      req.headers['authorization'] = `Bearer ${queryToken}`;
    } else {
      return res.redirect('/login/');
    }
  }

  // Use the existing authentication middleware
  authenticateToken(req, res, next);
}

// Middleware for admin pages (redirects to login if not authenticated)
export function requireAuthPage(req: Request, res: Response, next: NextFunction) {
  // Use the existing authentication middleware (now works with cookies)
  authenticateToken(req, res, (err?: any) => {
    if (err || !req.user) {
      // Authentication failed, redirect to login
      console.log('[Auth] Authentication failed, redirecting to login:', err);
      return res.redirect('/login/');
    }
    console.log('[Auth] Authentication successful for:', req.user.username);
    next();
  });
}

// Middleware for API routes (returns JSON error)
export function requireAuthApi(req: Request, res: Response, next: NextFunction) {
  authenticateToken(req, res, next);
}
