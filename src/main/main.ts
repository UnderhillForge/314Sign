import { app, BrowserWindow, screen } from 'electron'
import { spawn, spawnSync, execSync, type ChildProcess } from 'child_process'
import { join } from 'path'
import { existsSync } from 'fs'

const SERVER_HOST = process.env.KIOSK_HOST || '127.0.0.1'
const SERVER_PORT = Number(process.env.KIOSK_PORT || process.env.PORT || 80)
const SERVER_URL = `http://${SERVER_HOST}:${SERVER_PORT}`
const DISPLAY_POLL_MS = 5000

type DisplayConfig = {
  hdmi_port: number
  enabled: number | boolean
  orientation: number
  mode: 'main' | 'slideshow' | 'disabled' | 'identify' | 'test-pattern'
  slideshow_name?: string | null
  position_x?: number
  position_y?: number
  xrandr_output?: string
}

type DisplayWindowState = {
  window: BrowserWindow
  url: string
  displayId: number
}

// Disable GPU acceleration to prevent crashes on resource-constrained systems like Raspberry Pi
app.disableHardwareAcceleration()

let serverProcess: ChildProcess | null = null
const nodeBinary = process.env.KIOSK_NODE_BINARY || 'node'
const displayWindows = new Map<number, DisplayWindowState>()
let lastDisplayConfigHash = ''

function getAppRoot(): string {
  if (!app.isPackaged) {
    return process.cwd()
  }
  return app.getAppPath()
}

function getServerRoot(): string {
  return join(getAppRoot(), 'packages', '314Sign')
}

function getServerScript(): { script: string; usesTsNode: boolean } {
  const serverRoot = getServerRoot()
  const distServer = join(serverRoot, 'dist', 'server.js')
  if (existsSync(distServer)) {
    return { script: distServer, usesTsNode: false }
  }

  const tsServer = join(serverRoot, 'src', 'server.ts')
  return { script: tsServer, usesTsNode: true }
}

function startServer(): void {
  if (serverProcess) return

  const serverRoot = getServerRoot()
  const { script, usesTsNode } = getServerScript()
  const args = usesTsNode
    ? ['--loader', 'ts-node/esm', script]
    : [script]

  serverProcess = spawn(nodeBinary, args, {
    cwd: serverRoot,
    env: {
      ...process.env,
      ELECTRON_RUN_AS_NODE: '1',
      PORT: String(SERVER_PORT),
      HTTP_PORT: String(SERVER_PORT),
    },
    stdio: ['ignore', 'pipe', 'pipe'],
  })

  serverProcess.stdout?.on('data', (data) => {
    console.log(`[314Sign] ${String(data).trim()}`)
  })

  serverProcess.stderr?.on('data', (data) => {
    console.error(`[314Sign] ${String(data).trim()}`)
  })

  serverProcess.on('exit', (code, signal) => {
    console.warn(`[314Sign] Server exited: code=${code} signal=${signal}`)
    serverProcess = null
  })
}

async function waitForServer(timeoutMs = 30000): Promise<boolean> {
  const started = Date.now()
  while (Date.now() - started < timeoutMs) {
    try {
      const response = await fetch(`${SERVER_URL}/api`)
      if (response.ok) {
        return true
      }
    } catch {
      // Retry until timeout
    }
    await new Promise((resolve) => setTimeout(resolve, 500))
  }
  return false
}

async function fetchDisplayConfig(): Promise<DisplayConfig[]> {
  const response = await fetch(`${SERVER_URL}/api/kiosk/displays`)
  if (!response.ok) {
    throw new Error(`Failed to fetch display config (${response.status})`)
  }
  const payload = (await response.json()) as { data?: DisplayConfig[] }
  return payload.data || []
}

function buildDisplayUrl(config: DisplayConfig): string | null {
  if (!config.enabled || config.mode === 'disabled') {
    return null
  }

  const port = config.hdmi_port
  const displayNumber = port + 1
  let orientation = config.orientation || 0
  const cacheBuster = Date.now() // Add cache buster to force fresh page loads

  // HDMI-2 (port=1) has a -90° hardware offset, so compensate by adding 90° to the orientation value
  // This way, orientation=0 always means 0°, regardless of which HDMI port is used
  if (port === 1) {
    orientation = (orientation + 1) % 4
  }

  if (config.mode === 'identify') {
    return `${SERVER_URL}/identify.html?display=${displayNumber}&orientation=${orientation}&bust=${cacheBuster}`
  }

  if (config.mode === 'test-pattern') {
    return `${SERVER_URL}/test-pattern.html?display=${displayNumber}&orientation=${orientation}&bust=${cacheBuster}`
  }

  if (config.mode === 'slideshow' && config.slideshow_name) {
    const slideshow = encodeURIComponent(config.slideshow_name)
    const resolution = config.resolution || 'auto'
    return `${SERVER_URL}/slideshows/reveal-player.html?slideshow=${slideshow}&orientation=${orientation}&resolution=${resolution}&bust=${cacheBuster}`
  }

  return `${SERVER_URL}/?port=${port}&orientation=${orientation}&bust=${cacheBuster}`
}

function findBestDisplay(config: DisplayConfig) {
  const allDisplays = screen.getAllDisplays()
  if (allDisplays.length === 0) {
    return null
  }

  const targetX = config.position_x ?? 0
  const targetY = config.position_y ?? 0

  let bestDisplay = allDisplays[0]
  let bestScore = Number.POSITIVE_INFINITY
  for (const display of allDisplays) {
    const dx = Math.abs(display.bounds.x - targetX)
    const dy = Math.abs(display.bounds.y - targetY)
    const score = dx + dy
    if (score < bestScore) {
      bestScore = score
      bestDisplay = display
    }
  }

  return bestDisplay
}

function ensureWindowForDisplay(config: DisplayConfig, url: string) {
  const existing = displayWindows.get(config.hdmi_port)
  const display = findBestDisplay(config)

  if (!display) {
    return
  }

  if (existing) {
    if (existing.url !== url) {
      existing.window.loadURL(url)
      existing.url = url
    }
    if (existing.displayId !== display.id) {
      existing.window.setBounds(display.bounds)
      existing.displayId = display.id
    }
    if (existing.window.isMinimized()) {
      existing.window.restore()
    }
    existing.window.show()
    return
  }

  const window = new BrowserWindow({
    x: display.bounds.x,
    y: display.bounds.y,
    width: display.bounds.width,
    height: display.bounds.height,
    show: true,
    fullscreen: true,
    kiosk: true,
    frame: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  })

  window.loadURL(url)
  window.on('closed', () => {
    displayWindows.delete(config.hdmi_port)
  })

  displayWindows.set(config.hdmi_port, {
    window,
    url,
    displayId: display.id,
  })
}

function closeWindowForPort(port: number) {
  const existing = displayWindows.get(port)
  if (!existing) return
  existing.window.close()
  displayWindows.delete(port)
}

/**
 * Check if a command exists on the system
 */
function commandExists(cmd: string): boolean {
  try {
    execSync(`which ${cmd}`, { stdio: 'ignore' })
    return true
  } catch {
    return false
  }
}

/**
 * Get current display rotation using Electron Display API
 */
function getDisplayRotation(displayId: number): number {
  const allDisplays = screen.getAllDisplays()
  const display = allDisplays.find(d => d.id === displayId)
  if (!display) {
    return 0
  }
  // Electron returns rotation as 0, 90, 180, 270
  // We need to convert to our format: 0, 1, 2, 3
  const displayRotation = (display.rotation ?? 0) as number
  const normalizedRotation = Math.round(displayRotation / 90) % 4
  console.log(`[ROTATE] Display ${displayId} current rotation: ${displayRotation}° (normalized: ${normalizedRotation})`)
  return normalizedRotation
}

/**
 * List all available displays with their properties
 */
function logDisplayInfo(): void {
  const allDisplays = screen.getAllDisplays()
  console.log(`[ROTATE] ===== DISPLAY INFO (${allDisplays.length} total) =====`)
  for (const display of allDisplays) {
    console.log(`[ROTATE] Display ID: ${display.id}`)
    console.log(`[ROTATE]   - Bounds: ${display.bounds.x},${display.bounds.y} (${display.bounds.width}x${display.bounds.height})`)
    console.log(`[ROTATE]   - Resolution: ${display.bounds.width}x${display.bounds.height}`)
    console.log(`[ROTATE]   - Rotation: ${display.rotation}° (value: ${Math.round((display.rotation ?? 0) / 90)})`)
    console.log(`[ROTATE]   - Scale: ${display.scaleFactor}`)
    console.log(`[ROTATE]   - Virtual: ${display.internal ? 'Yes' : 'No'}`)
  }
  console.log(`[ROTATE] ===== END DISPLAY INFO =====`)
}

/**
 * Apply OS-level display rotation via xrandr on Linux/Raspberry Pi
 * @param xrandrOutput - The xrandr output name (e.g., 'HDMI-1', 'HDMI1')
 * @param orientation - Rotation value: 0=normal, 1=left (90°), 2=inverted (180°), 3=right (270°)
 */
function applyDisplayRotation(xrandrOutput: string, orientation: number): void {
  if (process.platform !== 'linux') {
    console.log(`[ROTATE] Display rotation not supported on ${process.platform}, skipping`)
    return
  }

  // Check if xrandr is available
  if (!commandExists('xrandr')) {
    console.warn(`[ROTATE] xrandr command not found - install with: sudo apt-get install x11-xserver-utils`)
    console.log(`[ROTATE] Skipping display rotation`)
    return
  }

  // Map orientation value to xrandr rotation flag
  const rotationMap: Record<number, string> = {
    0: 'normal',    // 0°
    1: 'left',      // 90° clockwise = xrandr 'left'
    2: 'inverted',  // 180°
    3: 'right',     // 270° clockwise = xrandr 'right'
  }

  const rotation = rotationMap[orientation] || 'normal'

  try {
    console.log(`[ROTATE] Applying rotation to ${xrandrOutput}: ${rotation} (value: ${orientation})`)

    // Execute xrandr to rotate display
    const result = spawnSync('xrandr', ['--output', xrandrOutput, '-o', rotation], {
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: 5000,
    })

    if (result.error) {
      console.error(`[ROTATE] Failed to execute xrandr: ${result.error.message}`)
      return
    }

    if (result.status !== 0) {
      const stderr = result.stderr?.toString() || 'unknown error'
      console.error(`[ROTATE] xrandr failed with status ${result.status}: ${stderr}`)
      return
    }

    console.log(`[ROTATE] Successfully rotated ${xrandrOutput} to ${rotation}`)
  } catch (error) {
    console.error(`[ROTATE] Error applying rotation: ${error instanceof Error ? error.message : String(error)}`)
  }
}

async function refreshDisplayWindows(force = false) {
  const configs = await fetchDisplayConfig()
  const hash = JSON.stringify(configs)
  if (!force && hash === lastDisplayConfigHash) {
    return
  }
  lastDisplayConfigHash = hash

  for (const config of configs) {
    const url = buildDisplayUrl(config)
    if (!url) {
      closeWindowForPort(config.hdmi_port)
      continue
    }
    ensureWindowForDisplay(config, url)

    // Apply display rotation if configured
    if (config.orientation !== undefined && config.orientation !== null && config.orientation !== 0) {
      try {
        // Use xrandr_output from config if available, otherwise try to detect
        let xrandrOutput = config.xrandr_output
        
        if (!xrandrOutput) {
          // Fallback: try to detect xrandr output name from display position
          // Common patterns: HDMI-1, HDMI1, HDMI-2, etc.
          xrandrOutput = `HDMI-${config.hdmi_port + 1}`
        }

        // Note: CSS rotation on the page handles the rotation, so we're disabling xrandr
        // to avoid double-rotation issues (xrandr + CSS transforms)
        // applyDisplayRotation(xrandrOutput, config.orientation)
      } catch (error) {
        console.error(`[ROTATE] Failed to apply rotation to display ${config.hdmi_port}: ${error}`)
      }
    }
  }
}

async function startKiosk() {
  console.log('[KIOSK] Starting 314Sign kiosk application')
  console.log(`[KIOSK] Platform: ${process.platform}`)
  
  startServer()

  const ready = await waitForServer()
  if (!ready) {
    console.error('[KIOSK] 314Sign server did not become ready in time')
    return
  }

  // Give server a moment to fully initialize all routes
  await new Promise((resolve) => setTimeout(resolve, 1000))

  // Log display information
  logDisplayInfo()
  
  // Check for xrandr availability on Linux
  if (process.platform === 'linux') {
    if (commandExists('xrandr')) {
      console.log('[KIOSK] xrandr is available for display rotation')
    } else {
      console.warn('[KIOSK] xrandr not found - display rotation will not work')
      console.warn('[KIOSK] To enable rotation, install: sudo apt-get install x11-xserver-utils')
    }
  }

  await refreshDisplayWindows(true)
  setTimeout(() => {
    refreshDisplayWindows(true).catch((error) => {
      console.error('[KIOSK] Failed to refresh display config (startup retry):', error)
    })
  }, 2000)
  setInterval(() => {
    refreshDisplayWindows().catch((error) => {
      console.error('[KIOSK] Failed to refresh display config:', error)
    })
  }, DISPLAY_POLL_MS)
}

app.on('ready', () => {
  startKiosk().catch((error) => {
    console.error('[KIOSK] Startup failed:', error)
  })
})

app.on('before-quit', () => {
  if (serverProcess) {
    serverProcess.kill('SIGTERM')
    serverProcess = null
  }
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
