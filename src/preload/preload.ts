import { contextBridge, ipcRenderer } from 'electron'

const api = {
  // Display control
  setOrientation: (port: number, orientation: number) =>
    ipcRenderer.invoke('set-orientation', port, orientation),

  getDisplayConfig: () =>
    ipcRenderer.invoke('get-display-config'),

  getXrandrStatus: () =>
    ipcRenderer.invoke('get-xrandr-status'),

  // Menu API
  fetchMenu: (menuName: string) =>
    ipcRenderer.invoke('fetch-menu', menuName),

  fetchConfig: () =>
    ipcRenderer.invoke('fetch-config'),

  // Orientation lock via Screen Orientation API
  lockOrientation: async (orientationType: string) => {
    if (!window.screen?.orientation?.lock) {
      console.warn('Screen Orientation API not available')
      return false
    }
    try {
      await window.screen.orientation.lock(orientationType)
      console.log('[PRELOAD] Locked orientation to:', orientationType)
      return true
    } catch (error) {
      console.error('[PRELOAD] Failed to lock orientation:', error)
      return false
    }
  },

  unlockOrientation: () => {
    if (window.screen?.orientation?.unlock) {
      window.screen.orientation.unlock()
      console.log('[PRELOAD] Unlocked orientation')
    }
  },
}

declare global {
  interface Window {
    electronAPI: typeof api
  }
}

contextBridge.exposeInMainWorld('electronAPI', api)
