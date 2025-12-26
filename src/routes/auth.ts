import express from 'express';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import crypto from 'crypto';
import { dbHelpers } from '../database.js';
import db from '../database.js';
import { ApiResponse } from '../types/index.js';

const router = express.Router();

// JWT secret - in production, use environment variable
const JWT_SECRET = process.env.JWT_SECRET || '314sign-secret-key-change-in-production';
const JWT_EXPIRES_IN = '24h';

// Middleware to verify JWT token from cookie or header
export function authenticateToken(req: express.Request, res: express.Response, next: express.NextFunction) {
  console.log(`[Auth] authenticateToken called for ${req.method} ${req.path}`);

  let token: string | undefined;

  // Check for token in httpOnly cookie first (secure)
  token = req.cookies?.auth_token;

  // Fallback: Check Authorization header (for API clients)
  if (!token) {
    const authHeader = req.headers['authorization'];
    token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN
  }

  // Final fallback: Check query parameter (legacy support)
  if (!token) {
    token = req.query.token as string;
  }

  if (!token) {
    console.log('[Auth] No token found');
    return res.status(401).json({
      success: false,
      error: 'Access token required',
      message: 'Please provide a valid authentication token'
    } as ApiResponse);
  }

  jwt.verify(token, JWT_SECRET, (err: any, user: any) => {
    if (err) {
      console.log('[Auth] Token verification failed:', err.message);
      return res.status(403).json({
        success: false,
        error: 'Invalid token',
        message: 'Authentication token is invalid or expired'
      } as ApiResponse);
    }

    req.user = user;
    console.log(`[Auth] Token verified for user: ${user.username}, role: ${user.role}`);
    next();
  });
}

// Middleware to check admin role
export function requireAdmin(req: express.Request, res: express.Response, next: express.NextFunction) {
  console.log('[Auth] requireAdmin check:', {
    hasUser: !!req.user,
    userRole: req.user?.role,
    userId: req.user?.id,
    userName: req.user?.username
  });

  if (!req.user || req.user.role !== 'admin') {
    console.log('[Auth] Access denied: not admin');
    return res.status(403).json({
      success: false,
      error: 'Admin access required',
      message: 'This operation requires administrator privileges'
    } as ApiResponse);
  }

  console.log('[Auth] Access granted: admin confirmed');
  next();
}

// Middleware to check editor or admin role
export function requireEditor(req: express.Request, res: express.Response, next: express.NextFunction) {
  if (!req.user || (req.user.role !== 'admin' && req.user.role !== 'editor')) {
    return res.status(403).json({
      success: false,
      error: 'Editor access required',
      message: 'This operation requires editor or administrator privileges'
    } as ApiResponse);
  }
  next();
}

// POST /api/auth/login
router.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({
        success: false,
        error: 'Missing credentials',
        message: 'Username and password are required'
      } as ApiResponse);
    }

    // Get user from database
    const user = dbHelpers.getUserByUsername(username) as any;

    if (!user) {
      return res.status(401).json({
        success: false,
        error: 'Invalid credentials',
        message: 'Username or password is incorrect'
      } as ApiResponse);
    }

    // Verify password
    const isValidPassword = await bcrypt.compare(password, user.password_hash);

    if (!isValidPassword) {
      return res.status(401).json({
        success: false,
        error: 'Invalid credentials',
        message: 'Username or password is incorrect'
      } as ApiResponse);
    }

    // Update last login
    dbHelpers.updateUserLastLogin(user.id);

    // Generate JWT token
    const token = jwt.sign(
      {
        id: user.id,
        username: user.username,
        role: user.role
      },
      JWT_SECRET,
      { expiresIn: JWT_EXPIRES_IN }
    );

    // Set HTTP-only cookie (secure, automatic, XSS-safe)
    res.cookie('auth_token', token, {
      httpOnly: true,           // Prevents JavaScript access (XSS protection)
      secure: process.env.NODE_ENV === 'production', // HTTPS only in production
      sameSite: 'strict',       // CSRF protection
      maxAge: 24 * 60 * 60 * 1000, // 24 hours in milliseconds
      path: '/'                 // Available on all paths
    });

    res.json({
      success: true,
      data: {
        user: {
          id: user.id,
          username: user.username,
          role: user.role,
          lastLogin: user.last_login
        }
      },
      message: 'Login successful'
    } as ApiResponse);

  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({
      success: false,
      error: 'Login failed',
      message: 'An error occurred during login'
    } as ApiResponse);
  }
});

// POST /api/auth/logout
router.post('/logout', authenticateToken, (req, res) => {
  // Clear the authentication cookie
  res.clearCookie('auth_token', {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict',
    path: '/'
  });

  res.json({
    success: true,
    message: 'Logout successful'
  } as ApiResponse);
});

// GET /api/auth/me - Get current user info
router.get('/me', authenticateToken, (req, res) => {
  const user = dbHelpers.getUserByUsername(req.user!.username) as any;

  res.json({
    success: true,
    data: {
      id: user.id,
      username: user.username,
      role: user.role,
      lastLogin: user.last_login,
      createdAt: user.created_at
    }
  } as ApiResponse);
});

// POST /api/auth/register - Create new user (admin only)
router.post('/register', authenticateToken, requireAdmin, async (req, res) => {
  try {
    const { username, password, role } = req.body;

    if (!username || !password) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields',
        message: 'Username and password are required'
      } as ApiResponse);
    }

    // Validate role
    const validRoles = ['viewer', 'editor', 'admin'];
    const userRole = role || 'viewer';

    if (!validRoles.includes(userRole)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid role',
        message: 'Role must be one of: viewer, editor, admin'
      } as ApiResponse);
    }

    // Check if user already exists
    const existingUser = dbHelpers.getUserByUsername(username) as any;
    if (existingUser) {
      return res.status(409).json({
        success: false,
        error: 'User already exists',
        message: 'A user with this username already exists'
      } as ApiResponse);
    }

    // Hash password
    const saltRounds = 10;
    const passwordHash = await bcrypt.hash(password, saltRounds);

    // Create user
    const result = dbHelpers.createUser(username, passwordHash, userRole);

    res.status(201).json({
      success: true,
      data: {
        id: result.lastInsertRowid,
        username,
        role: userRole
      },
      message: 'User created successfully'
    } as ApiResponse);

  } catch (error) {
    console.error('User registration error:', error);
    res.status(500).json({
      success: false,
      error: 'Registration failed',
      message: 'An error occurred while creating the user'
    } as ApiResponse);
  }
});

// PUT /api/auth/password - Change password
router.put('/password', authenticateToken, async (req, res) => {
  try {
    const { currentPassword, newPassword } = req.body;

    if (!currentPassword || !newPassword) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields',
        message: 'Current password and new password are required'
      } as ApiResponse);
    }

    // Get current user
    const user = dbHelpers.getUserByUsername(req.user!.username) as any;

    // Verify current password
    const isValidPassword = await bcrypt.compare(currentPassword, user.password_hash);

    if (!isValidPassword) {
      return res.status(401).json({
        success: false,
        error: 'Invalid current password',
        message: 'The current password you entered is incorrect'
      } as ApiResponse);
    }

    // Hash new password
    const saltRounds = 10;
    const newPasswordHash = await bcrypt.hash(newPassword, saltRounds);

    // Update password
    db.prepare('UPDATE users SET password_hash = ? WHERE id = ?').run(newPasswordHash, user.id);

    res.json({
      success: true,
      message: 'Password changed successfully'
    } as ApiResponse);

  } catch (error) {
    console.error('Password change error:', error);
    res.status(500).json({
      success: false,
      error: 'Password change failed',
      message: 'An error occurred while changing the password'
    } as ApiResponse);
  }
});

// GET /api/auth/users - List users (admin only)
router.get('/users', authenticateToken, requireAdmin, (req, res) => {
  try {
    const users = db.prepare('SELECT id, username, role, created_at, last_login FROM users ORDER BY username').all();

    res.json({
      success: true,
      data: users
    } as ApiResponse);

  } catch (error) {
    console.error('Users list error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve users',
      message: 'An error occurred while fetching the user list'
    } as ApiResponse);
  }
});

// PUT /api/auth/users/:id/password - Change user password (admin only)
router.put('/users/:id/password', authenticateToken, requireAdmin, async (req, res) => {
  try {
    const userId = parseInt(req.params.id);
    const { newPassword } = req.body;

    if (!userId || isNaN(userId)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid user ID',
        message: 'A valid user ID is required'
      } as ApiResponse);
    }

    if (!newPassword) {
      return res.status(400).json({
        success: false,
        error: 'Missing new password',
        message: 'New password is required'
      } as ApiResponse);
    }

    // Check if user exists
    const user = db.prepare('SELECT username FROM users WHERE id = ?').get(userId) as { username: string } | undefined;

    if (!user) {
      return res.status(404).json({
        success: false,
        error: 'User not found',
        message: 'The specified user does not exist'
      } as ApiResponse);
    }

    // Hash new password
    const saltRounds = 10;
    const newPasswordHash = await bcrypt.hash(newPassword, saltRounds);

    // Update password
    const result = db.prepare('UPDATE users SET password_hash = ? WHERE id = ?').run(newPasswordHash, userId);

    if (result.changes > 0) {
      res.json({
        success: true,
        message: `Password for user "${user.username}" updated successfully`
      } as ApiResponse);
    } else {
      throw new Error('No rows affected');
    }

  } catch (error) {
    console.error('User password update error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to update password',
      message: 'An error occurred while updating the user password'
    } as ApiResponse);
  }
});

// DELETE /api/auth/users/:id - Delete user (admin only)
router.delete('/users/:id', authenticateToken, requireAdmin, (req, res) => {
  try {
    const userId = parseInt(req.params.id);

    if (!userId || isNaN(userId)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid user ID',
        message: 'A valid user ID is required'
      } as ApiResponse);
    }

    // Prevent deleting the current user
    if (req.user!.id === userId) {
      return res.status(400).json({
        success: false,
        error: 'Cannot delete current user',
        message: 'You cannot delete your own account'
      } as ApiResponse);
    }

    // Check if user exists
    const user = db.prepare('SELECT username FROM users WHERE id = ?').get(userId) as { username: string } | undefined;

    if (!user) {
      return res.status(404).json({
        success: false,
        error: 'User not found',
        message: 'The specified user does not exist'
      } as ApiResponse);
    }

    // Delete user
    const result = db.prepare('DELETE FROM users WHERE id = ?').run(userId);

    if (result.changes > 0) {
      res.json({
        success: true,
        message: `User "${user.username}" deleted successfully`
      } as ApiResponse);
    } else {
      throw new Error('No rows affected');
    }

  } catch (error) {
    console.error('User deletion error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to delete user',
      message: 'An error occurred while deleting the user'
    } as ApiResponse);
  }
});

export default router;
