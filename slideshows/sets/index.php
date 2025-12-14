<?php
// slideshows/sets/index.php
// Returns JSON array of available slideshow set files

header('Content-Type: application/json');

$setsDir = __DIR__;
$files = glob($setsDir . '/*.json');

$sets = [];
foreach ($files as $file) {
    $filename = basename($file);
    if ($filename !== 'index.php') {
        $sets[] = $filename;
    }
}

echo json_encode($sets);
?>