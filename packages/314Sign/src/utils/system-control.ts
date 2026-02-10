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
 * Build xrandr command string from display configurations
 * Returns command that can be executed with exec()
 * NOTE: Skips --rotate flag due to display stability issues on Raspberry Pi
 */
export function buildXrandrCommand(displays: DisplayConfig[]): string {
  const parts = ['xrandr'];
  
  for (const display of displays) {
    if (display.enabled) {
      // Safe parameters only - skip rotation to prevent display blanking
      const resolution = display.resolution || '3840x2160'; // Default 4K resolution
      const refresh = display.refresh_rate || 60;
      
      // Build the command with only safe parameters
      parts.push(
        `--output ${display.xrandr_output}`,
        `--mode ${resolution}`,
        `--rate ${refresh}`,
        `--pos ${display.position_x}x${display.position_y}`
      );
      
      console.log(`[XRANDR] Enabling ${display.xrandr_output}: ${resolution} @ ${refresh}Hz`);
    } else {
      // Disable output
      parts.push(`--output ${display.xrandr_output} --off`);
      console.log(`[XRANDR] Disabling ${display.xrandr_output}`);
    }
  }
  
  return parts.join(' ');
}

/**
 * Apply xrandr configuration
 */
export async function applyXrandrConfig(displays: DisplayConfig[]): Promise<boolean> {
  try {
    const command = buildXrandrCommand(displays);
    console.log(`Executing: ${command}`);
    await execPromise(command, { env: getDisplayEnv() });
    console.log('xrandr configuration applied successfully');
    return true;
  } catch (error) {
    console.error('Failed to apply xrandr configuration:', error);
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
  
  if (config.mode !== undefined && !['main', 'slideshow', 'disabled'].includes(config.mode)) {
    errors.push('mode must be "main", "slideshow", or "disabled"');
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
