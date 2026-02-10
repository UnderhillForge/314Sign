import fs from 'fs/promises';
import path from 'path';
import { KioskConfig } from '../types/index.js';

/**
 * Safely merges configuration updates into the existing config file
 * @param updates - The configuration updates to apply
 * @param configPath - Path to the config file (optional, defaults to config.json in project root)
 * @returns The merged configuration object
 */
export async function mergeConfig(
  updates: Partial<KioskConfig>,
  configPath?: string
): Promise<KioskConfig> {
  const defaultConfigPath = path.join(process.cwd(), 'config.json');
  const targetPath = configPath || defaultConfigPath;

  // Read existing config
  let existingConfig: KioskConfig = {
    version: '1.0.0'
  };

  try {
    const configData = await fs.readFile(targetPath, 'utf-8');
    existingConfig = JSON.parse(configData);
  } catch (error) {
    // Config file doesn't exist, use defaults
    console.log('Config file not found, using defaults');
  }

  // Merge configs (updates take precedence, but preserve unknown keys)
  const mergedConfig: KioskConfig = {
    ...existingConfig,
    ...updates,
    // Ensure version is preserved or updated appropriately
    version: updates.version || existingConfig.version || '1.0.0'
  };

  // Write back to file
  await fs.writeFile(targetPath, JSON.stringify(mergedConfig, null, 2), 'utf-8');

  return mergedConfig;
}

/**
 * Reads the current configuration from file
 * @param configPath - Path to the config file (optional, defaults to config.json in project root)
 * @returns The current configuration object
 */
export async function readConfig(configPath?: string): Promise<KioskConfig> {
  const defaultConfigPath = path.join(process.cwd(), 'config.json');
  const targetPath = configPath || defaultConfigPath;

  let config: KioskConfig = {
    version: '1.0.0'
  };

  try {
    const configData = await fs.readFile(targetPath, 'utf-8');
    config = { ...config, ...JSON.parse(configData) };
  } catch (error) {
    // Config file doesn't exist or is invalid, return defaults
    console.log('Config file not found or invalid, using defaults');
  }

  return config;
}

/**
 * Validates a configuration object
 * @param config - The configuration object to validate
 * @returns True if valid, throws error if invalid
 */
export function validateConfig(config: any): config is KioskConfig {
  if (!config || typeof config !== 'object') {
    throw new Error('Configuration must be an object');
  }

  // Version is required
  if (!config.version || typeof config.version !== 'string') {
    throw new Error('Configuration must have a valid version string');
  }

  // Optional string fields
  const stringFields = ['background', 'fontFamily', 'fontSize', 'textColor', 'backgroundColor', 'logo', 'theme'];
  for (const field of stringFields) {
    if (config[field] !== undefined && typeof config[field] !== 'string') {
      throw new Error(`Configuration field '${field}' must be a string`);
    }
  }

  return true;
}