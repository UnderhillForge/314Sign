<?php
// slideshows/save-set.php
// Accepts JSON: { filename: "sets/<name>.json", content: { ... } }
// Writes atomically to slideshows/sets/<name>.json and returns JSON status.

header('Content-Type: application/json');

$repoDir = __DIR__;
$body = file_get_contents('php://input');
if (!$body) {
    echo json_encode(['success' => false, 'error' => 'Empty request']);
    exit;
}

$data = json_decode($body, true);
if (!is_array($data) || empty($data['filename']) || !isset($data['content'])) {
    echo json_encode(['success' => false, 'error' => 'Invalid JSON body, expected { filename, content }']);
    exit;
}

$filenameRaw = $data['filename'];

// Normalize filename: accept either 'sets/name.json' or 'name.json'
$filename = basename($filenameRaw);

// Validate filename strictly
if (!preg_match('/^[a-z0-9-]+\.json$/i', $filename)) {
    echo json_encode(['success' => false, 'error' => 'Invalid filename']);
    exit;
}

$setsDir = $repoDir . '/sets';
if (!is_dir($setsDir)) {
    if (!mkdir($setsDir, 0755, true)) {
        echo json_encode(['success' => false, 'error' => 'Failed to create sets directory']);
        exit;
    }
}

$targetPath = $setsDir . '/' . $filename;

// Prepare JSON content
$jsonContent = json_encode($data['content'], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
if ($jsonContent === false) {
    echo json_encode(['success' => false, 'error' => 'Failed to encode content to JSON']);
    exit;
}

// Atomic write: temp file then rename
$tmp = tempnam($setsDir, 'tmp');
if ($tmp === false) {
    echo json_encode(['success' => false, 'error' => 'Failed to create temp file']);
    exit;
}

if (file_put_contents($tmp, $jsonContent) === false) {
    @unlink($tmp);
    echo json_encode(['success' => false, 'error' => 'Failed to write temp file']);
    exit;
}

if (!@rename($tmp, $targetPath)) {
    @unlink($tmp);
    echo json_encode(['success' => false, 'error' => 'Failed to move file into place; check permissions']);
    exit;
}

// Ensure permissions are reasonable
@chmod($targetPath, 0644);

echo json_encode(['success' => true, 'filename' => 'sets/' . $filename]);
exit;
