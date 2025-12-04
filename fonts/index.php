<?php
/**
 * Scan fonts/ directory and return list of TTF files
 * Returns JSON array of font files for dynamic loading
 */

header('Content-Type: application/json');

$fonts_dir = __DIR__;
$fonts = [];

// Scan directory for .ttf files
if (is_dir($fonts_dir)) {
    $files = scandir($fonts_dir);
    foreach ($files as $file) {
        if (pathinfo($file, PATHINFO_EXTENSION) === 'ttf') {
            // Extract font name from filename
            // Convert "BebasNeue-Regular.ttf" -> "Bebas Neue"
            $name = pathinfo($file, PATHINFO_FILENAME);
            $name = preg_replace('/[-_]?(Regular|Bold|Italic|Light|Medium|Heavy|Black)$/i', '', $name);
            $name = preg_replace('/([a-z])([A-Z])/', '$1 $2', $name); // Add spaces between camelCase
            $name = trim($name);
            
            $fonts[] = [
                'name' => $name,
                'file' => $file,
                'filename' => pathinfo($file, PATHINFO_FILENAME)
            ];
        }
    }
}

// Sort by name
usort($fonts, function($a, $b) {
    return strcmp($a['name'], $b['name']);
});

echo json_encode($fonts, JSON_PRETTY_PRINT);
