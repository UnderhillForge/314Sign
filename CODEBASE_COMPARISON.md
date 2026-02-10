# 314Sign Codebase Comparison: Local vs. GitHub

## Architecture Overview

### Local Codebase (`/home/pi/314Sign`)
**Status:** Legacy PHP-based static server with minimal backend
- **Backend:** Static files + PHP endpoints (lightweight)
- **Frontend:** Vanilla HTML/CSS/JavaScript
- **Database:** File-based (JSON, TXT)
- **Server:** lighttpd + WebDAV + PHP
- **Deployment:** Direct file syncing via WebDAV, `setup-kiosk.sh` shell script

### GitHub Repository (`UnderhillForge/314Sign`)
**Status:** Modern Node.js/TypeScript full-stack application
- **Backend:** Express.js server + SQLite database
- **Frontend:** Same HTML/CSS/JavaScript (in `/public` folder)
- **Database:** SQLite (structured, queryable)
- **Server:** Node.js with PM2 process management
- **Deployment:** npm-based setup, TypeScript compilation, process manager

---

## Key Differences

### 1. **Backend Technology Stack**

| Aspect | Local | GitHub |
|--------|-------|--------|
| **Server Runtime** | PHP + lighttpd | Node.js + Express.js |
| **Language** | PHP, inline JavaScript | TypeScript, JavaScript |
| **Database** | JSON files (`config.json`, `rules.json`) | SQLite database |
| **Process Management** | Shell scripts | PM2 |
| **API Style** | PHP endpoints (`save-menu-history.php`, etc.) | RESTful API (`/api/*`) |
| **Type Safety** | None | Full TypeScript |

### 2. **File Structure**

#### Local Root Level
```
/home/pi/314Sign/
├── index.html                    (main kiosk UI)
├── config.json                   (app config)
├── rules.json                    (scheduling rules)
├── version.txt                   (version file)
├── *.php                         (PHP endpoints)
├── menus/                        (menu text files)
├── design/                       (design editor)
├── edit/                         (edit interface)
├── rules/                        (rules editor)
├── slideshows/                   (slideshow manager)
└── bg/                          (backgrounds)
```

#### GitHub Root Level
```
/
├── index.html                   (kiosk UI)
├── edit/
├── design/
├── rules/
├── slideshows/
├── login/
├── maintenance/
├── start/
├── remotes/
├── src/                         (Node.js backend)
│   ├── server.ts               (Express setup)
│   ├── database.ts             (SQLite)
│   ├── routes/                 (API endpoints)
│   ├── middleware/
│   └── utils/
├── scripts/                     (bash + npm scripts)
├── remclient/                   (remote kiosk system - NEW)
├── package.json
├── tsconfig.json
└── setup-kiosk.sh
```

### 3. **Database & Configuration**

| Feature | Local | GitHub |
|---------|-------|--------|
| **Menu Storage** | `menus/*.txt` files | SQLite `menus` table |
| **Config** | `config.json` (file) | SQLite + API (structured) |
| **Rules** | `rules.json` (file) | SQLite `rules` table |
| **Menu History** | `history/*.txt` | SQLite `menu_history` table |
| **Queries** | None (file-based) | Full SQL support |

### 4. **New Features in GitHub Version**

#### 🔄 **Remote Kiosk System** (`/remclient`)
- Multi-display support (main + remote Pi Zero devices)
- Real-time config sync across devices
- Per-remote display modes (mirror, specific menu, slideshow)
- Hardware-based unique device IDs (6-character codes)
- Remote management dashboard

#### 🎨 **Modern UI & Customization**
- Per-menu font and size control
- Multiple professional fonts (Lato, Bebas Neue, Caveat, etc.)
- Logo overlay with transparency/size control
- Background brightness adjustment (20-150%)
- 6 slideshow transitions

#### 🚀 **Production Features**
- PM2 process management
- Auto-boot with systemd
- Health monitoring endpoints
- Comprehensive logging
- Database backups
- RESTful API documentation

### 5. **API Endpoints**

#### Local (PHP Endpoints)
```
POST   /save-menu-history.php
GET    /get-menu-history.php
POST   /design/upload-bg.php
POST   /design/upload-logo.php
POST   /design/upload.php
POST   /rules/save-set.php
POST   /slideshows/save-set.php
POST   /slideshows/upload-media.php
GET    /fonts/index.php
GET    /menus/index.php
GET    /bg/index.php
GET    /status.php
```

#### GitHub (RESTful API)
```
GET    /api/status
GET    /api/system/info
GET    /api/config
POST   /api/config
PUT    /api/config
GET    /api/menu
GET    /api/menu/:name
PUT    /api/menu/:name
DELETE /api/menu/:name
GET    /api/menu/:name/history
GET    /api/rules
POST   /api/rules
PUT    /api/rules/:id
DELETE /api/rules/:id
GET    /api/backgrounds
GET    /api/fonts
POST   /api/upload/bg
POST   /api/upload/media
DELETE /api/upload/bg/:filename
POST   /api/system/reload
GET    /api/remotes
POST   /api/remotes/register
PUT    /api/remotes/:id
POST   /api/remotes/:id/push-config
POST   /api/auth/login
POST   /api/auth/logout
```

### 6. **Configuration Management**

#### Local
```javascript
// menus-config.json - Menu metadata
{
  "menus": [
    {
      "name": "breakfast",
      "display_name": "Breakfast",
      "font": "default",
      "font_size": 24
    }
  ]
}
```

#### GitHub
```javascript
// SQLite + API - Structured relational data
// Queries possible with SQL
// Atomic transactions
// Foreign key relationships
```

### 7. **Deployment & Operations**

| Task | Local | GitHub |
|------|-------|--------|
| **Install** | `./setup-kiosk.sh` (bash) | `npm install` → `npm run build` → PM2 |
| **Restart** | Manual server restart | `pm2 restart 314sign` |
| **Logs** | Individual PHP error logs | `pm2 logs 314sign` |
| **Monitoring** | Manual health checks | `/api/status` + `pm2 monit` |
| **Auto-Start** | lighttpd systemd | PM2 + systemd |
| **Development** | Direct file editing | `npm run dev` (auto-reload) |

### 8. **Security**

#### Local
- WebDAV-based file access control
- Basic HTTP authentication (if configured)
- No application-level authentication

#### GitHub
- RESTful API with auth middleware
- JWT-based sessions
- Per-user permissions
- Login/logout endpoints

### 9. **Frontend Similarity**

Both versions share nearly identical frontend code:
- Same HTML structure in `index.html`
- Same CSS styling
- Same JavaScript logic for:
  - Menu display and rendering
  - ETag-based polling
  - Live preview
  - Color tag formatting
  - Responsive design

**Key difference:** Frontend paths
- Local: Root-level files (`/index.html`, `/edit/`, `/design/`)
- GitHub: Root-level files (aligned with local)

### 10. **Development Workflow**

#### Local
```bash
# Start dev server
php -S localhost:8000

# Make changes directly to HTML/CSS/JS
# Edit JSON files manually
# WebDAV PUTs for remote changes
```

#### GitHub
```bash
# Install dependencies
npm install

# Start development with auto-reload
npm run dev

# TypeScript compilation
npm run build

# Start production
npm start

# Run tests
npm test
```

---

## Migration Path: Local → GitHub

If you wanted to migrate from local to GitHub version:

1. **Backend:** Replace PHP + lighttpd with Node.js + Express
2. **Database:** Migrate `config.json`, `rules.json` → SQLite
3. **Frontend:** Keep UI pages at repo root for direct static serving
4. **Deployments:** Replace WebDAV with npm + PM2
5. **Gain:** Remote kiosks, structured data, RESTful API
6. **Maintain:** Same UI/UX for end users

---

## Version Information

- **Local:** Based on older PHP-based architecture
- **GitHub:** v1.0.2.32 (2 months ago latest major commit)
- **Languages:** Local (HTML/CSS/PHP/JS) vs. GitHub (TypeScript/JavaScript)
- **Complexity:** Local (simple, minimal) vs. GitHub (production-grade, feature-rich)

---

## Summary

| Feature | Local | GitHub |
|---------|:-----:|:-------:|
| Node.js Backend | ❌ | ✅ |
| TypeScript | ❌ | ✅ |
| SQLite Database | ❌ | ✅ |
| RESTful API | ❌ | ✅ |
| PM2 Process Management | ❌ | ✅ |
| Remote Kiosk System | ❌ | ✅ |
| Multi-Device Sync | ❌ | ✅ |
| Modern fonts & styling | ⚠️ Limited | ✅ Full |
| Production-grade logging | ❌ | ✅ |
| Auto-reload in dev | ❌ | ✅ |
| API Documentation | ❌ | ✅ |
| Health monitoring | ❌ | ✅ |

**Recommendation:** GitHub version is significantly more feature-rich and production-ready, with modern architecture. Local version is a simpler, file-based alternative suitable for minimal deployments.
