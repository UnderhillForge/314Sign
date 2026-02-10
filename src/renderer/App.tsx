import React, { useState, useEffect } from 'react'
import './App.css'

interface MenuConfig {
  version: string
  displayOrientation?: number
  headerText: string
  showClock: boolean
  clock24Hour: boolean
  [key: string]: unknown
}

interface MenuItem {
  success: boolean
  data?: { content: string }
  error?: string
}

declare global {
  interface Window {
    electronAPI: {
      fetchMenu: (name: string) => Promise<MenuItem>
      fetchConfig: () => Promise<{ data: MenuConfig; success: boolean }>
      setOrientation: (port: number, orientation: number) => Promise<{ success: boolean; error?: string }>
      lockOrientation: (type: string) => Promise<boolean>
      unlockOrientation: () => void
    }
  }
}

export function App() {
  const [menuContent, setMenuContent] = useState<string>('Loading...')
  const [config, setConfig] = useState<MenuConfig | null>(null)
  const [currentTime, setCurrentTime] = useState<string>('')
  const [orientation, setOrientation] = useState<number>(1)

  useEffect(() => {
    loadConfig()
    loadMenu()

    // Update clock every second
    const clockInterval = setInterval(() => {
      const now = new Date()
      const hours = String(now.getHours()).padStart(2, '0')
      const minutes = String(now.getMinutes()).padStart(2, '0')
      const seconds = String(now.getSeconds()).padStart(2, '0')
      setCurrentTime(`${hours}:${minutes}:${seconds}`)
    }, 1000)

    return () => clearInterval(clockInterval)
  }, [])

  // Lock orientation on first load
  useEffect(() => {
    if (config?.displayOrientation !== undefined) {
      applyOrientation(config.displayOrientation)
    }
  }, [config])

  async function loadConfig() {
    try {
      const response = await window.electronAPI.fetchConfig()
      if (response.success && response.data) {
        setConfig(response.data)
      }
    } catch (error) {
      console.error('Failed to load config:', error)
    }
  }

  async function loadMenu() {
    try {
      const response = await window.electronAPI.fetchMenu('dinner')
      if (response.success && response.data) {
        setMenuContent(response.data.content)
      } else {
        setMenuContent('Failed to load menu')
      }
    } catch (error) {
      console.error('Failed to load menu:', error)
      setMenuContent('Error loading menu')
    }
  }

  async function applyOrientation(value: number) {
    setOrientation(value)

    // Map orientation to Screen Orientation API type
    const orientationMap: Record<number, string> = {
      0: 'portrait-primary',
      1: 'landscape-secondary',
      2: 'portrait-secondary',
      3: 'landscape-primary',
    }

    const orientationType = orientationMap[value] || 'landscape-primary'

    // Try Screen Orientation API first
    const locked = await window.electronAPI.lockOrientation(orientationType)
    if (!locked) {
      console.log('Screen Orientation API not available, using xrandr via main process')
      // Main process will handle xrandr if available
    }

    // Also tell main process to use xrandr
    try {
      await window.electronAPI.setOrientation(0, value)
    } catch (error) {
      console.error('xrandr orientation failed:', error)
    }
  }

  return (
    <div className="kiosk-container">
      <header className="kiosk-header">
        <h1>{config?.headerText || 'Specials'}</h1>
        {config?.showClock && <div className="clock">{currentTime}</div>}
      </header>

      <main className="kiosk-content">
        <div dangerouslySetInnerHTML={{ __html: menuContent }} />
      </main>

      <footer className="kiosk-footer">
        <small>314Sign © 2026</small>
      </footer>
    </div>
  )
}

export default App
