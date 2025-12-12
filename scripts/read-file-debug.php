<?php
// scripts/read-file-debug.php
// Debug helper: return metadata and base64 content for allowed files (menus/*.txt)
header('Content-Type: application/json');

$path = $_GET['path'] ?? '';
// Only allow menu files (any .txt file in menus/ directory)
if (!preg_match('#^menus/[a-z0-9_-]+\.txt$#i', $path)) {
    http_response_code(400);
    echo json_encode(['success' => false, 'error' => 'Invalid path (must be menus/[name].txt)']);
    exit;
}

$full = __DIR__ . '/../' . $path;
if (!file_exists($full)) {
    http_response_code(404);
    echo json_encode(['success' => false, 'error' => 'Not found']);
    exit;
}

$content = file_get_contents($full);
$size = strlen($content);
$sha = hash('sha256', $content);
$b64 = base64_encode($content);

echo json_encode([
    'success' => true,
    'path' => $path,
    'size' => $size,
    'sha256' => $sha,
    'content_base64' => $b64
]);
exit;
