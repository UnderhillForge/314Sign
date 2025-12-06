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

if ($handle = opendir($mediaDir)) {
  while (false !== ($file = readdir($handle))) {
    if ($file !== '.' && $file !== '..' && $file !== 'index.php') {
      $ext = strtolower(pathinfo($file, PATHINFO_EXTENSION));
      if (in_array($ext, $allowedExtensions)) {
        $files[] = $file;
      }
    }
  }
  closedir($handle);
}

// Natural sort for human-friendly ordering
natsort($files);
$files = array_values($files); // Re-index after sort

echo json_encode($files, JSON_PRETTY_PRINT);
