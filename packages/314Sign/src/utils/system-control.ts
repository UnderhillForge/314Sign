import { exec } from 'child_process';
import { promisify } from 'util';
import { execSync } from 'child_process';

const execPromise = promisify(exec);

/**
 * Get the XAUTHORITY from the running X server process
 */
function getXauthority(): string {
  try {
    const result = execSync("ps aux | grep '[X] ' | grep -o '\\-auth [^ ]*'", { 
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'ignore']
    })
      .trim();
    
    if (result) {
      const match = result.match(/\-auth\s+(.+)$/);
      if (match && match[1]) {
        const path = match[1];
        // Verify it exists before returning
        try {
          require('fs').statSync(path);
          return path;
        } catch {
          // Path doesn't exist
        }
      }
    }
  } catch (error) {
    // Fallback if grep fails
  }
  
  // Fallback paths in order
  const fs = require('fs');
  const fallbacks = [
    '/home/pi/.Xauthority',
    '/root/.Xauthority'
  ];
  
  for (const path of fallbacks) {
    try {
      fs.statSync(path);
      return path;
    } catch {
      // Continue to next
    }
  }
  
  // Last resort - return empty string which will let X use default
  return '';
}

// Get environment for xrandr and display commands
function getDisplayEnv() {
  const xauth = getXauthority();
  const env: NodeJS.ProcessEnv = {
    ...process.env,
    DISPLAY: process.env.DISPLAY || ':0'
  };
  
  if (xauth) {
    env.XAUTHORITY = xauth;
  }
  
  return env;
}

export interface DisplayConfig {
  hdmi_port: number;
  xrandr_output: string;
  enabled: number;
  orientation: number; // 0=0°, 1=90°, 2=180°, 3=270°
  position_x: number;
  position_y: number;
  refresh_rate?: number;
  resolution?: string;
}

/**
 * Parse xrandr output to detect connected monitors
 */
export async function getXrandrOutputs(): Promise<string[]> {
  try {
    const { stdout } = await execPromise('xrandr --listmonitors', { env: getDisplayEnv() });
    const outputs: string[] = [];
    
    // Parse xrandr output: Monitors: 2
    // +HDMI-1 connected primary 1080x1920+0+0 (normal left inverted right x axis y axis)
    const lines = stdout.split('\n');
    for (const line of lines) {
      if (line.includes('connected') && !line.includes('disconnected')) {
        const match = line.match(/^\+?(\S+)\s+connected/);
        if (match) {
          outputs.push(match[1]);
        }
      }
    }
    
    return outputs;
  } catch (error) {
    console.error('Failed to get xrandr outputs:', error);
    return [];
  }
}

/**
 * Get available display resolutions for an xrandr output
 */
function getAvailableResolutions(xrandrOutput: string): string[] {
  try {
    const { stdout } = execSync(`xrandr --query`, { encoding: 'utf-8', env: getDisplayEnv(), stdio: ['pipe', 'pipe', 'ignore'] }) as any;
    const lines = stdout.split('\n');
    let inOutput = false;
    const resolutions: string[] = [];
    
    for (const line of lines) {
      // Look for the output line (e.g., "HDMI-1 connected")
      if (line.startsWith(xrandrOutput)) {
        inOutput = true;
        continue;
      }
      
      // Stop when we hit another output or end
      if (inOutput && line.match(/^[A-Z]/)) {
        break;
      }
      
      if (inOutput) {
        // Parse resolution lines (they start with whitespace and contain an 'x')
        const match = line.trim().match(/^(\d+x\d+)/);
        if (match) {
          resolutions.push(match[1]);
        }
      }
    }
    
    return resolutions;
  } catch (error) {
    console.warn(`[XRANDR] Failed to get resolutions for ${xrandrOutput}, using fallback`);
    return [];
  }
}

/**
 * Build xrandr command string from display configurations
 * Returns command that can be executed with exec()
 * NOTE: Skips --rotate flag due to display stability issues on Raspberry Pi
 */
export function buildXrandrCommand(displays: DisplayConfig[]): string {
  const parts = ['xrandr'];
  
  for (const display of displays) {
    if (display.enabled) {
      let resolution = display.resolution;
      
      // Auto-detect resolution if not specified
      if (!resolution) {
        const available = getAvailableResolutions(display.xrandr_output);
        // Pick the first (highest) available resolution, or fallback to 1920x1080
        resolution = available.length > 0 ? available[0] : '1920x1080';
      }
      
      const refresh = display.refresh_rate || 60;
      
      // Build command parts with output first, then mode
      const outputParts = [`--output ${display.xrandr_output}`, `--mode ${resolution}`];
      
      // Only add refresh rate if resolution was explicitly specified in database
      if (display.resolution) {
        outputParts.push(`--rate ${refresh}`);
      }
      
      // Add position
      outputParts.push(`--pos ${display.position_x}x${display.position_y}`);
      
      parts.push(...outputParts);
      
      console.log(`[XRANDR] Enabling ${display.xrandr_output}: ${resolution}${display.resolution ? ` @ ${refresh}Hz` : ''}`);
    } else {
      // Disable output
      parts.push(`--output ${display.xrandr_output}`, `--off`);
      console.log(`[XRANDR] Disabling ${display.xrandr_output}`);
    }
  }
  
  return parts.join(' ');
}

/**
 * Apply xrandr configuration with timeout protection
 */
export async function applyXrandrConfig(displays: DisplayConfig[]): Promise<boolean> {
  try {
    const command = buildXrandrCommand(displays);
    console.log(`[XRANDR] Executing command: ${command}`);
    
    // Apply with a 10-second timeout to prevent hanging
    const { stdout, stderr } = await Promise.race([
      execPromise(command, { env: getDisplayEnv(), maxBuffer: 1024 * 1024 }),
      new Promise<{ stdout: string; stderr: string }>((_, reject) =>
        setTimeout(() => reject(new Error('xrandr command timeout (>10s)')), 10000)
      )
    ]);
    
    if (stderr && stderr.trim()) {
      console.warn(`[XRANDR] Command warnings: ${stderr}`);
    }
    
    console.log('[XRANDR] Configuration applied successfully');
    return true;
  } catch (error) {
    console.error('[XRANDR] Failed to apply configuration:', error instanceof Error ? error.message : String(error));
    return false;
  }
}

/**
 * Test display output by briefly flashing (set brightness to 0 then back to 100)
 * Falls back to xrandr cycle if ddccontrol not available
 */
export async function testDisplayOutput(xrandrOutput: string): Promise<boolean> {
  try {
    // Try using xrandr to toggle the display off and on
    // Brief off-on cycle to draw attention to the display
    const commands = [
      `xrandr --output ${xrandrOutput} --brightness 0`,
      'sleep 0.5',
      `xrandr --output ${xrandrOutput} --brightness 1`
    ].join(' && ');
    
    await execPromise(commands, { env: getDisplayEnv() });
    console.log(`Test signal sent to ${xrandrOutput}`);
    return true;
  } catch (error) {
    console.error(`Failed to test display output for ${xrandrOutput}:`, error);
    return false;
  }
}

/**
 * Restart X server (handles display reconfiguration on next start)
 */
export async function restartXServer(): Promise<boolean> {
  try {
    // Try systemctl first for display-manager
    try {
      await execPromise('sudo systemctl restart display-manager');
      console.log('X11 display manager restarted');
      return true;
    } catch {
      // Fallback: try restarting the main X session
      await execPromise('sudo systemctl restart lightdm');
      console.log('lightdm restarted');
      return true;
    }
  } catch (error) {
    console.error('Failed to restart X server:', error);
    return false;
  }
}

/**
 * Restart the 314Sign web application
 */
export async function restartWebServer(): Promise<boolean> {
  try {
    await execPromise('sudo systemctl restart 314sign-web');
    console.log('314sign-web service restarted');
    return true;
  } catch (error) {
    console.error('Failed to restart 314sign-web:', error);
    // Fallback: try to restart via systemctl
    try {
      await execPromise('sudo systemctl restart node-314sign');
      console.log('node-314sign service restarted');
      return true;
    } catch (fallbackError) {
      console.error('Fallback restart also failed:', fallbackError);
      return false;
    }
  }
}

/**
 * Restart both X server and web application sequentially
 */
export async function restartServices(): Promise<{ xserver: boolean; webserver: boolean }> {
  console.log('Starting service restart sequence...');
  
  const xserverRestarted = await restartXServer();
  // Give X server time to start before restarting web server
  if (xserverRestarted) {
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  
  const webserverRestarted = await restartWebServer();
  
  return {
    xserver: xserverRestarted,
    webserver: webserverRestarted
  };
}

/**
 * Validate a display configuration for safety
 */
export function validateDisplayConfig(config: any): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  if (config.hdmi_port !== undefined && ![0, 1].includes(config.hdmi_port)) {
    errors.push('hdmi_port must be 0 or 1');
  }

  if (config.guest_facing !== undefined && ![0, 1, true, false].includes(config.guest_facing)) {
    errors.push('guest_facing must be boolean');
  }
  
  if (config.orientation !== undefined && ![0, 1, 2, 3].includes(config.orientation)) {
    errors.push('orientation must be 0-3 (0°, 90°, 180°, 270°)');
  }
  
  if (config.mode !== undefined && !['main', 'slideshow', 'disabled', 'identify', 'test-pattern'].includes(config.mode)) {
    errors.push('mode must be "main", "slideshow", "test-pattern", "identify", or "disabled"');
  }
  
  if (config.position_x !== undefined && (config.position_x < 0 || config.position_x > 7680)) {
    errors.push('position_x must be 0-7680');
  }
  
  if (config.position_y !== undefined && (config.position_y < 0 || config.position_y > 4320)) {
    errors.push('position_y must be 0-4320');
  }
  
  if (config.refresh_rate !== undefined && (config.refresh_rate < 24 || config.refresh_rate > 240)) {
    errors.push('refresh_rate must be 24-240 Hz');
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
}
