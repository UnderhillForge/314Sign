// Configuration types
export interface KioskConfig {
  version: string;
  background?: string;
  fontFamily?: string;
  fontSize?: string;
  textColor?: string;
  backgroundColor?: string;
  logo?: string;
  theme?: string;
  [key: string]: any; // Allow additional properties
}

export interface PageConfig {
  title?: string;
  background?: string;
  fontFamily?: string;
  fontSize?: string;
  textColor?: string;
  backgroundColor?: string;
  logo?: string;
  theme?: string;
  [key: string]: any;
}

// Rules types
export interface ScheduleRule {
  name: string;
  startTime: string;
  endTime: string;
  days: string[];
  menu?: string;
  slideshow?: string;
  background?: string;
  theme?: string;
}

export interface RulesConfig {
  rules: ScheduleRule[];
  defaultMenu?: string;
  defaultSlideshow?: string;
  defaultBackground?: string;
  defaultTheme?: string;
}

// Menu types
export interface MenuItem {
  name: string;
  content: string;
  lastModified: Date;
}

// Slideshow types
export interface SlideshowItem {
  filename: string;
  url: string;
  type: 'image' | 'video';
  duration?: number;
}

export interface SlideshowSet {
  name: string;
  items: SlideshowItem[];
  loop?: boolean;
  random?: boolean;
}

// API Response types
import express from 'express';

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Extend Express Request to include user property
declare global {
  namespace Express {
    interface Request {
      user?: {
        id: number;
        username: string;
        role: string;
      };
    }
  }
}

// File upload types
export interface UploadResult {
  filename: string;
  url: string;
  size: number;
  type: string;
}

// Status types
export interface ServerStatus {
  version: string;
  uptime: number;
  timestamp: string;
  config: {
    webdav: boolean;
    php: boolean;
    writable: boolean;
  };
}
