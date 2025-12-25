<?php
/**
 * Menu File Lister
 * Returns JSON array of all .txt files in menus/ directory
 * Used by editor and rules pages to dynamically discover menu files
 */

header('Content-Type: application/json');

$menusDir = __DIR__;
$files = [];

if ($handle = opendir($menusDir)) {
  while (false !== ($file = readdir($handle))) {
    if ($file !== '.' && $file !== '..' && $file !== 'index.php') {
      $ext = strtolower(pathinfo($file, PATHINFO_EXTENSION));
      if ($ext === 'txt') {
        $files[] = [
          'filename' => $file,
          'path' => 'menus/' . $file,
          'label' => ucfirst(pathinfo($file, PATHINFO_FILENAME))
        ];
      }
    }
  }
  closedir($handle);
}

// Natural sort for human-friendly ordering
usort($files, function($a, $b) {
  return strnatcasecmp($a['filename'], $b['filename']);
});

echo json_encode($files, JSON_PRETTY_PRINT);
?>
