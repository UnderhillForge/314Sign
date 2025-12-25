<?php
error_reporting(E_ALL & ~E_WARNING);
header('Content-Type: application/json');

// Read directory safely and return only image filenames (sorted)
$files = @scandir('.');
if ($files === false) {
    http_response_code(500);
    echo json_encode([]);
    exit;
}

$images = array_filter($files, function($f) {
    // Skip hidden files and directories
    if ($f === '.' || $f === '..' || $f[0] === '.') return false;
    if (is_dir($f)) return false;
    return preg_match('/\.(jpe?g|png|gif|webp|avif)$/i', $f);
});

// Sort by name (natural case-insensitive)
usort($images, function($a, $b) {
    return strcasecmp($a, $b);
});

echo json_encode(array_values($images));
?>