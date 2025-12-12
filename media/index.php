<?php
/**
 * Media File Lister
 * Returns JSON array of files in media/ directory
 * Similar to bg/index.php but for logos and media assets
 */

header('Content-Type: application/json');

$mediaDir = __DIR__;
$files = [];

// Supported media formats for logos
$allowedExtensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'avif', 'svg'];

// Debug: log the directory being scanned
error_log('[Media Index] Scanning directory: ' . $mediaDir);

if ($handle = opendir($mediaDir)) {
  while (false !== ($file = readdir($handle))) {
    error_log('[Media Index] Found file: ' . $file);
    if ($file !== '.' && $file !== '..' && $file !== 'index.php') {
      $ext = strtolower(pathinfo($file, PATHINFO_EXTENSION));
      error_log('[Media Index] File extension: ' . $ext);
      if (in_array($ext, $allowedExtensions)) {
        $files[] = $file;
        error_log('[Media Index] Added to list: ' . $file);
      }
    }
  }
  closedir($handle);
} else {
  error_log('[Media Index] ERROR: Could not open directory: ' . $mediaDir);
}

error_log('[Media Index] Total files found: ' . count($files));

// Natural sort for human-friendly ordering
natsort($files);
$files = array_values($files); // Re-index after sort

echo json_encode($files, JSON_PRETTY_PRINT);
