# File Structure Guide

Understanding the 314Sign project organization and key files.

## Root Directory Structure

```
314Sign/
├── src/                    # TypeScript source code
├── public/                 # Static web assets
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── tests/                  # Test files
├── bg/                     # Background images
├── fonts/                  # Custom fonts
├── media/                  # Media assets
├── menus/                  # Menu data (legacy)
├── slideshows/             # Slideshow data
├── rules/                  # Schedule rules (legacy)
├── logs/                   # Application logs
├── history/                # Menu history
├── package.json            # Node.js dependencies
├── tsconfig.json           # TypeScript configuration
├── ecosystem.config.js     # PM2 configuration
├── setup-kiosk.sh          # Installation script
├── remote-setup.sh         # Remote device setup
├── permissions.sh          # File permissions script
├── 314sign.db             # SQLite database
├── config.json            # Application configuration
├── version.txt            # Version information
└── README.md              # Main documentation
```

## Source Code (`src/`)

### Core Files
```
src/
├── server.ts              # Express server setup and configuration
├── database.ts            # SQLite database connection and utilities
└── types/
    └── index.ts           # TypeScript type definitions
```

### API Routes (`src/routes/`)
```
src/routes/
├── auth.ts                # Authentication endpoints (/api/auth/*)
├── backgrounds.ts         # Background management (/api/backgrounds)
├── config.ts              # Configuration management (/api/config)
├── fonts.ts               # Font management (/api/fonts)
├── menu.ts                # Menu CRUD operations (/api/menu/*)
├── menu-control.ts        # Menu display control (/api/menu/control)
├── remotes.ts             # Remote viewer management (/api/remotes)
├── rules.ts               # Schedule rules (/api/rules)
├── slideshows.ts          # Slideshow management (/api/slideshows)
├── status.ts              # System status (/api/status)
├── system.ts              # System utilities (/api/system)
└── upload.ts              # File upload handling (/api/upload/*)
```

### Middleware (`src/middleware/`)
```
src/middleware/
└── auth.ts                # Authentication middleware
```

### Utilities (`src/utils/`)
```
src/utils/
└── config.ts              # Configuration utilities
```

## Web Interface (`public/`)

### Main Pages
```
public/
├── index.html             # Main kiosk display page
├── edit/                  # Menu editing interface
├── design/                # Design customization
├── rules/                 # Schedule rule management
├── slideshows/            # Slideshow creation
├── login/                 # Authentication page
├── maintenance/           # System maintenance
├── start/                 # Quick access landing page
└── remotes/               # Remote viewer management
```

### Page Structure
Each page directory contains:
- `index.html` - Main page content
- Associated CSS/JS files (bundled)
- Static assets as needed

## Scripts (`scripts/`)

### Installation & Setup
```
scripts/
├── setup-kiosk.sh         # Full system installation
├── remote-setup.sh        # Remote device setup
├── os-lite-kiosk.sh       # Raspberry Pi kiosk mode setup
└── permissions.sh         # File permission management
```

### Maintenance & Utilities
```
scripts/
├── backup.sh              # System backup creation
├── deploy-check.sh        # Deployment verification
├── increment-version.sh   # Version number management
├── install-fonts.sh       # Font installation utilities
├── migrate-to-db.js       # Database migration
├── update-from-github.sh  # Remote update system
└── validate-slideshow-set.php  # Legacy validation (deprecated)
```

## Data Storage

### Database (`314sign.db`)
SQLite database containing:
- Menus and menu items
- Slideshow configurations
- Schedule rules
- System settings
- User sessions

### Configuration (`config.json`)
Application settings:
```json
{
  "server": {
    "port": 80,
    "host": "0.0.0.0"
  },
  "display": {
    "orientation": "horizontal",
    "brightness": 80
  },
  "fonts": {
    "default": "Lato",
    "size": 16
  }
}
```

### File-Based Storage
```
bg/                        # Background images
├── backgd.jpg            # Default background
├── backgd2.avif          # Alternative background
└── uploaded_*.jpg        # User-uploaded backgrounds

fonts/                     # Custom fonts
├── .htaccess             # Web access control
├── Lato-Regular.ttf      # Google Fonts
├── BebasNeue-Regular.ttf # Display font
└── *.ttf                 # Additional fonts

media/                     # General media assets
├── logo.avif             # Business logo
└── sample.avif           # Sample content

slideshows/media/         # Slideshow media files
└── *.jpg,*.mp4,*.png     # User-uploaded content
```

## Legacy Files (Migrated to Database)

### Menu Data (`menus/`) - **LEGACY**
```
menus/
├── breakfast.txt         # Breakfast menu (migrated to DB)
├── lunch.txt             # Lunch menu (migrated to DB)
├── dinner.txt            # Dinner menu (migrated to DB)
└── closed.txt            # Closed message (migrated to DB)
```

### Rules (`rules/`) - **LEGACY**
```
rules/
├── examples/             # Sample rule configurations
│   ├── full-day.json
│   ├── midnight-boundary.json
│   └── midnight-span-1.json
└── index.html            # Rules management UI
```

## Build & Development

### Build Output
```
dist/                     # Compiled TypeScript (generated)
├── server.js            # Main server
├── routes/              # Compiled routes
├── middleware/          # Compiled middleware
└── *.js                 # All TypeScript compiled to JS
```

### Development Files
```
node_modules/            # NPM dependencies
.env                     # Environment variables (gitignored)
.gitignore              # Git ignore rules
jest.config.cjs         # Test configuration
tsconfig.json           # TypeScript configuration
```

## Configuration Files

### PM2 Configuration (`ecosystem.config.js`)
```javascript
module.exports = {
  apps: [{
    name: '314sign',
    script: 'dist/server.js',
    instances: 1,
    exec_mode: 'fork',
    env: {
      NODE_ENV: 'production',
      PORT: 80
    }
  }]
}
```

### TypeScript Configuration (`tsconfig.json`)
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "outDir": "./dist",
    "strict": true,
    "esModuleInterop": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

## Important Notes

### File Permissions
- Web root (`/var/www/html`) owned by `www-data`
- Scripts executable by owner
- Database file (`314sign.db`) writable by web user
- Upload directories (`bg/`, `fonts/`) writable by web user

### Migration Status
- **Menus**: Migrated from `menus/*.txt` → database
- **Rules**: Migrated from `rules.json` → database
- **Slideshows**: Migrated from JSON files → database
- **Settings**: Migrated from multiple files → `config.json`

### Backup Strategy
Critical files to backup:
- `314sign.db` (database)
- `config.json` (settings)
- `bg/uploaded_*` (custom backgrounds)
- `fonts/*.ttf` (custom fonts)
- PM2 configuration

## Development Workflow

### Adding New Features
1. **Backend**: Add route in `src/routes/`
2. **Frontend**: Update HTML in `public/`
3. **Database**: Add migration in `scripts/migrate-to-db.js`
4. **Types**: Update `src/types/index.ts`
5. **Tests**: Add tests in `tests/`

### File Naming Conventions
- **Routes**: `feature-name.ts`
- **Pages**: `feature-name/index.html`
- **Scripts**: `feature-name.sh` or `feature-name.js`
- **Tests**: `feature-name.test.ts`

This structure ensures maintainable, scalable code organization for the 314Sign digital signage system.
