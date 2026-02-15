import { execSync } from 'child_process'
import { spawn } from 'child_process'

export interface DisplayConfig {
  hdmi_port: number
  orientation: number
  enabled: boolean
  mode: 'main' | 'slideshow' | 'disabled'
  slideshow_name?: string
  resolution?: string | null
  xrandr_output?: string
  position_x?: number
  position_y?: number
}

export class DisplayController {
  private xauthFile: string | null = null
  private display = ':0'

  constructor() {
    this.findXauthority()
  }

  private findXauthority() {
    try {
      // Try to find X auth file from running X process
      const ps = execSync("ps aux | grep -i 'X\\|xvfb' | grep -v grep").toString()
      const match = ps.match(/XAUTHORITY=([^ ]+)/)
      if (match) {
        this.xauthFile = match[1]
        console.log('[DISPLAY] Found XAUTHORITY:', this.xauthFile)
        return
      }
    } catch (error) {
      // Fallback to common locations
    }

    const commonPaths = [
      '/root/.Xauthority',
      `/tmp/.X${this.display.substring(1)}-unix`,
      '/tmp/serverauth.*',
    ]

    for (const path of commonPaths) {
      try {
        execSync(`ls ${path}`, { stdio: 'ignore' })
        this.xauthFile = path
        console.log('[DISPLAY] Using XAUTHORITY:', this.xauthFile)
        return
      } catch {
        // Continue to next path
      }
    }

    console.warn('[DISPLAY] Could not find XAUTHORITY file')
  }

  private getXrandrEnv() {
    const env = { ...process.env }
    env.DISPLAY = this.display
    if (this.xauthFile) {
      env.XAUTHORITY = this.xauthFile
    }
    return env
  }

  async setOrientation(port: number, orientation: number): Promise<{angle: number, port: number}> {
    // Orientation mapping:
    // 0: normal (0°)
    // 1: left/90° (landscape-secondary on Pi)
    // 2: inverted (180°)
    // 3: right/270° (landscape-primary)

    const orientationMap: Record<number, string> = {
      0: 'normal',
      1: 'left',
      2: 'inverted',
      3: 'right',
    }

    const xrandrRotation = orientationMap[orientation] || 'normal'
    const hdmiOutput = port === 0 ? 'HDMI-1' : 'HDMI-2'

    try {
      console.log(`[DISPLAY] Setting ${hdmiOutput} to ${xrandrRotation}...`)

      const cmd = `xrandr --output ${hdmiOutput} --rotate ${xrandrRotation}`
      const result = execSync(cmd, { 
        env: this.getXrandrEnv(),
        encoding: 'utf-8',
        stdio: ['pipe', 'pipe', 'pipe'],
        timeout: 5000,
      })

      console.log('[DISPLAY] xrandr result:', result)

      return {
        angle: orientation * 90,
        port,
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error)
      console.error('[DISPLAY] xrandr failed:', errorMsg)
      throw new Error(`Failed to set orientation: ${errorMsg}`)
    }
  }

  getConfig(): DisplayConfig[] {
    return [
      {
        hdmi_port: 0,
        orientation: 1, // Default to portrait (left 90°)
        enabled: true,
        mode: 'main',
      },
      {
        hdmi_port: 1,
        orientation: 0,
        enabled: false,
        mode: 'disabled',
      },
    ]
  }

  getXrandrStatus() {
    try {
      const output = execSync('xrandr', { 
        env: this.getXrandrEnv(),
        encoding: 'utf-8',
      })

      const hdmi1Connected = output.includes('HDMI-1 connected')
      const hdmi2Connected = output.includes('HDMI-2 connected')

      return {
        available: true,
        hdmi1: hdmi1Connected,
        hdmi2: hdmi2Connected,
        output,
      }
    } catch (error) {
      return {
        available: false,
        error: error instanceof Error ? error.message : 'xrandr not available',
      }
    }
  }
}
