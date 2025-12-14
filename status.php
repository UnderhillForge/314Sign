<?php
/**
 * 314Sign Status/Health Check Endpoint
 * Returns JSON with system information for monitoring
 * 
 * Usage: curl http://kiosk-ip/status.php
 */

error_reporting(E_ALL & ~E_WARNING);
header('Content-Type: application/json');

// Get version from version.txt
$version = '0.9.2.1'; // fallback
$version_file = __DIR__ . '/version.txt';
if (file_exists($version_file)) {
  $version_content = trim(file_get_contents($version_file));
  if (!empty($version_content)) {
    $version = $version_content;
  }
}

$status = [
  'version' => $version,
  'timestamp' => date('c'),
  'uptime' => null,
  'menus' => [],
  'config' => null,
  'rules' => null,
  'disk' => null,
  'errors' => []
];

// Get system uptime (Linux only)
if (file_exists('/proc/uptime')) {
  $uptime = file_get_contents('/proc/uptime');
  $uptime_seconds = (int)explode(' ', $uptime)[0];
  $status['uptime'] = sprintf('%dd %dh %dm', 
    floor($uptime_seconds / 86400),
    floor(($uptime_seconds % 86400) / 3600),
    floor(($uptime_seconds % 3600) / 60)
  );
}

// Check menu files - dynamically discover all .txt files in menus/
$menus_dir = __DIR__ . '/menus';
$menu_files = [];
if (is_dir($menus_dir) && $handle = opendir($menus_dir)) {
  while (false !== ($file = readdir($handle))) {
    if (pathinfo($file, PATHINFO_EXTENSION) === 'txt') {
      $menu_files[] = 'menus/' . $file;
    }
  }
  closedir($handle);
  sort($menu_files);
}

if (empty($menu_files)) {
  $status['errors'][] = "No menu files found in menus/ directory";
}

foreach ($menu_files as $menu) {
  $path = __DIR__ . '/' . $menu;
  if (file_exists($path)) {
    $status['menus'][$menu] = [
      'exists' => true,
      'size' => filesize($path),
      'modified' => date('c', filemtime($path)),
      'writable' => is_writable($path)
    ];
  } else {
    $status['menus'][$menu] = ['exists' => false];
    $status['errors'][] = "Missing menu: $menu";
  }
}

// Check config.json
$config_path = __DIR__ . '/config.json';
if (file_exists($config_path)) {
  $config_content = file_get_contents($config_path);
  $config_json = json_decode($config_content, true);
  $status['config'] = [
    'exists' => true,
    'valid' => ($config_json !== null),
    'writable' => is_writable($config_path),
    'background' => $config_json['bg'] ?? 'unknown',
    'font' => $config_json['font'] ?? 'unknown',
    'pollIntervalSeconds' => $config_json['pollIntervalSeconds'] ?? 'unknown'
  ];
  if ($config_json === null) {
    $status['errors'][] = 'config.json is invalid JSON';
  }
} else {
  $status['config'] = ['exists' => false];
  $status['errors'][] = 'config.json missing';
}

// Check rules.json
$rules_path = __DIR__ . '/rules.json';
if (file_exists($rules_path)) {
  $rules_content = file_get_contents($rules_path);
  $rules_json = json_decode($rules_content, true);
  $status['rules'] = [
    'exists' => true,
    'valid' => ($rules_json !== null),
    'writable' => is_writable($rules_path),
    'enabled' => $rules_json['enabled'] ?? false,
    'ruleCount' => count($rules_json['rules'] ?? [])
  ];
  if ($rules_json === null) {
    $status['errors'][] = 'rules.json is invalid JSON';
  }
} else {
  $status['rules'] = ['exists' => false];
  // Not an error - rules.json is optional
}

// Disk space check
$disk_total = disk_total_space(__DIR__);
$disk_free = disk_free_space(__DIR__);
if ($disk_total && $disk_free) {
  $disk_used_percent = round((($disk_total - $disk_free) / $disk_total) * 100, 1);
  $status['disk'] = [
    'total_mb' => round($disk_total / 1048576),
    'free_mb' => round($disk_free / 1048576),
    'used_percent' => $disk_used_percent
  ];
  if ($disk_used_percent > 90) {
    $status['errors'][] = "Disk usage high: {$disk_used_percent}%";
  }
}

// Check logs directory
$logs_dir = __DIR__ . '/logs';
if (!file_exists($logs_dir)) {
  $status['errors'][] = 'logs/ directory missing';
} elseif (!is_writable($logs_dir)) {
  $status['errors'][] = 'logs/ directory not writable';
}

// Overall health status
$status['healthy'] = (count($status['errors']) === 0);

echo json_encode($status, JSON_PRETTY_PRINT);
