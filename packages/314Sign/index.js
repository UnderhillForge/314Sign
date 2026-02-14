// Main menu page JavaScript

// Test: Fetch a unique URL to verify JavaScript is running
(function() {
  const img = new Image();
  img.src = `/qr-menu.png?test-js-running=${Date.now()}`;
  img.onload = () => console.log('[TEST] Image loaded, JS confirmed running from index.js');
  img.onerror = () => console.error('[TEST] Image failed to load from index.js');
})();

// Get URL parameters
const urlParams = new URLSearchParams(window.location.search);
const isGuestView = urlParams.get('guest') === '1';
const slideshowParam = urlParams.get('slideshow');
const orientationParam = parseInt(urlParams.get('orientation') || '0', 10);

// Apply CSS rotation
function applyRotation() {
  console.log(`[MAIN INDEX] Applying rotation. Orientation param: ${orientationParam}`);
  console.log(`[MAIN INDEX] document.body exists: ${!!document.body}`);
  console.log(`[MAIN INDEX] Viewport: ${window.innerWidth}x${window.innerHeight}`);

  if (orientationParam !== 0) {
    console.log(`[ORIENTATION] Applying CSS rotation from URL parameter: ${orientationParam}`);
    console.log(`[ORIENTATION] Body element:`, document.body);
    
    if (orientationParam === 1 || orientationParam === 3) {
      // 90° or 270° rotation - swap dimensions
      const vw = window.innerWidth;
      const vh = window.innerHeight;
      
      document.body.style.cssText = `
        position: fixed !important;
        width: ${vh}px !important;
        height: ${vw}px !important;
        transform-origin: 0 0 !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
        background: #333;
        color: white;
        font-family: Arial, sans-serif;
        display: flex;
        flex-direction: column;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.7);
      `;
      
      if (orientationParam === 1) {
        // 90° CW
        document.body.style.transform = `rotate(90deg) translate(0, -100%)`;
        console.log(`[ORIENTATION] Applied 90° rotation. Transform: ${document.body.style.transform}`);
      } else {
        // 270° CW  
        document.body.style.transform = `rotate(270deg) translate(-100%, 0)`;
        console.log(`[ORIENTATION] Applied 270° rotation. Transform: ${document.body.style.transform}`);
      }
    } else if (orientationParam === 2) {
      // 180° rotation
      document.body.style.cssText = `
        position: fixed !important;
        width: 100vw !important;
        height: 100vh !important;
        transform: rotate(180deg) !important;
        transform-origin: center center !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
        background: #333;
        color: white;
        font-family: Arial, sans-serif;
        display: flex;
        flex-direction: column;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.7);
      `;
    }
    
    console.log(`[ORIENTATION] Final body styles:`, {
      position: document.body.style.position,
      transform: document.body.style.transform,
      width: document.body.style.width,
      height: document.body.style.height
    });
  }
}

// Apply rotation immediately and also on DOMContentLoaded
applyRotation();
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', applyRotation);
}

// Store references to DOM elements
let headerEl, clockEl, specialsEl, qrBadgeEl, qrImageEl, qrTitleEl, qrUrlEl;

// Once DOM is ready, initialize
document.addEventListener('DOMContentLoaded', function() {
  headerEl = document.getElementById('header');
  clockEl = document.getElementById('clock');
  specialsEl = document.getElementById('specials');
  qrBadgeEl = document.getElementById('qr-badge');
  qrImageEl = document.getElementById('qr-image');
  qrTitleEl = document.getElementById('qr-title');
  qrUrlEl = document.getElementById('qr-url');
  
  console.log('[INIT] DOM ready, elements initialized');
  
  // Start initialization
  initializeMenu();
});

// Variables
let currentMenu = 'dinner';
let isPlayingSlideshow = false;
let clock24Hour = true;
let lastConfig = {};
let reloadTriggerValue = null;
let currentOrientation = 'portrait-primary';

// Fetch custom fonts
function loadCustomFonts() {
  console.log('[FONTS] Loading custom fonts...');
  return fetch('/api/fonts')
    .then(r => r.ok ? r.json() : { data: { customFonts: [] } })
    .then(response => {
      console.log('[FONTS] Fonts response:', response);
      const fonts = response.data?.customFonts || [];
      if (fonts.length === 0) return;

      const formatMap = { WOFF2: 'woff2', WOFF: 'woff', TTF: 'truetype' };
      const fontFaceCSS = fonts.map(font => {
        const format = formatMap[font.format] || 'truetype';
        return `@font-face {\n  font-family: '${font.filename}';\n  src: url('${font.url}') format('${format}');\n  font-display: swap;\n}`;
      }).join('\n');
      
      let styleTag = document.getElementById('customFonts');
      if (!styleTag) {
        styleTag = document.createElement('style');
        styleTag.id = 'customFonts';
        document.head.appendChild(styleTag);
      }
      styleTag.textContent = fontFaceCSS;
      console.log('[FONTS] Custom fonts loaded');
    })
    .catch(err => {
      console.error('[FONTS] Error loading fonts:', err);
    });
}

// Load and display menu
function loadMenu(menuName) {
  console.log(`[MENU] loadMenu called with: ${menuName}`);
  currentMenu = menuName;
  if (specialsEl) specialsEl.innerHTML = 'Loading...';
  
  console.log(`[MENU] Fetching /api/menu/${menuName}`);
  fetch('/api/menu/' + menuName)
    .then(r => {
      console.log(`[MENU] Fetch response:`, r.ok, r.status);
      return r.json();
    })
    .then(data => {
      console.log(`[MENU] Parsed data:`, data);
      if (data.success && specialsEl) {
        const html = formatMenuContent(data.data.content);
        console.log(`[MENU] Formatted HTML length: ${html.length}`);
        specialsEl.innerHTML = html;
        console.log(`[MENU] Menu loaded successfully`);
      } else {
        console.error(`[MENU] API returned success=false or specialsEl missing`);
      }
    })
    .catch(err => {
      console.error(`[MENU] Error loading menu:`, err);
      if (specialsEl) specialsEl.innerHTML = '<span style="color:red">Error loading menu: ' + err.message + '</span>';
    });
}

// Format menu content
function formatMenuContent(content) {
  return content
    .replace(/\{w\}/g, '<span style="color:white">')
    .replace(/\{y\}/g, '<span style="color:yellow">')
    .replace(/\{lg\}/g, '<span style="font-size:0.9em">')
    .replace(/\{\/\}/g, '</span>')
    .split('\n')
    .map(line => {
      if (line === '---') return '<hr style="border:1px solid #666; margin:1rem 0;">';
      if (!line) return '';
      return line + (line.match(/<\/span>$/) ? '' : '</span>'.repeat((line.match(/<span/g) || []).length - (line.match(/<\/span>/g) || []).length));
    })
    .filter(x => x)
    .join('<br>');
}

// Initialize the menu
function initializeMenu() {
  console.log('[INIT] Starting initialization...');
  console.log('[INIT] slideshowParam:', slideshowParam);
  console.log('[INIT] isGuestView:', isGuestView);
  
  loadCustomFonts().then(() => {
    console.log('[INIT] Custom fonts loaded, loading dinner menu...');
    loadMenu('dinner');
  }).catch(err => {
    console.error('[INIT] Error in initialization:', err);
  });
}
