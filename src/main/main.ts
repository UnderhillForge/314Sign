import { app, BrowserWindow, ipcMain, screen } from 'electron'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'
import { execSync } from 'child_process'
import { DisplayController } from './display-controller.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

let mainWindow: BrowserWindow | null = null
let displayController: DisplayController | null = null

function createWindow() {
  const primaryDisplay = screen.getPrimaryDisplay()
  const { width, height } = primaryDisplay.workAreaSize

  mainWindow = new BrowserWindow({
    width,
    height,
    webPreferences: {
      preload: join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    fullscreen: true,
    kiosk: true,
  })

  // Load the app
  const isDev = process.env.NODE_ENV === 'development'
  if (isDev) {
    mainWindow.loadURL('http://localhost:3000')
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(join(__dirname, 'renderer/index.html'))
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

app.on('ready', () => {
  createWindow()
  displayController = new DisplayController()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// IPC: Get display config
ipcMain.handle('get-display-config', async (_event) => {
  if (!displayController) return null
  return displayController.getConfig()
})

// IPC: Set orientation
ipcMain.handle('set-orientation', async (_event, port: number, orientation: number) => {
  if (!displayController) return { success: false, error: 'Display controller not available' }
  
  try {
    const result = await displayController.setOrientation(port, orientation)
    return { success: true, ...result }
  } catch (error) {
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'Unknown error'
    }
  }
})

// IPC: Get xrandr status
ipcMain.handle('get-xrandr-status', async (_event) => {
  if (!displayController) return { available: false }
  return displayController.getXrandrStatus()
})

// IPC: Fetch menu from server
ipcMain.handle('fetch-menu', async (_event, menuName: string) => {
  try {
    const response = await fetch(`http://localhost:3000/api/menu/${menuName}`)
    return await response.json()
  } catch (error) {
    return { success: false, error: 'Failed to fetch menu' }
  }
})

// IPC: Fetch config from server
ipcMain.handle('fetch-config', async (_event) => {
  try {
    const response = await fetch(`http://localhost:3000/api/config`)
    return await response.json()
  } catch (error) {
    return { success: false, error: 'Failed to fetch config' }
  }
})
