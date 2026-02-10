import { app, BrowserWindow, screen } from 'electron'
import { spawn, type ChildProcess } from 'child_process'
import { dirname, join } from 'path'
import { existsSync } from 'fs'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const SERVER_HOST = process.env.KIOSK_HOST || '127.0.0.1'
const SERVER_PORT = Number(process.env.KIOSK_PORT || process.env.PORT || 80)
const SERVER_URL = `http://${SERVER_HOST}:${SERVER_PORT}`
const DISPLAY_POLL_MS = 5000

type DisplayConfig = {
  hdmi_port: number
  enabled: number | boolean
  orientation: number
  mode: 'main' | 'slideshow' | 'disabled'
  slideshow_name?: string | null
  position_x?: number
  position_y?: number
}

type DisplayWindowState = {
  window: BrowserWindow
  url: string
  displayId: number
}

let serverProcess: ChildProcess | null = null
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

  serverProcess = spawn(process.execPath, args, {
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
      const response = await fetch(`${SERVER_URL}/api/status`)
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
  const payload = await response.json()
  return payload.data || []
}

function buildDisplayUrl(config: DisplayConfig): string | null {
  if (!config.enabled || config.mode === 'disabled') {
    return null
  }

  if (config.mode === 'slideshow' && config.slideshow_name) {
    const slideshow = encodeURIComponent(config.slideshow_name)
    return `${SERVER_URL}/?slideshow=${slideshow}`
  }

  return `${SERVER_URL}/`
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

async function refreshDisplayWindows() {
  const configs = await fetchDisplayConfig()
  const hash = JSON.stringify(configs)
  if (hash === lastDisplayConfigHash) {
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
  }
}

async function startKiosk() {
  startServer()

  const ready = await waitForServer()
  if (!ready) {
    console.error('[KIOSK] 314Sign server did not become ready in time')
    return
  }

  await refreshDisplayWindows()
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
