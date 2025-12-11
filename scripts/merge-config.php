<?php
// scripts/merge-config.php
// Accepts a JSON body with partial config changes, merges with existing config.json
// and writes back safely. Returns JSON { success: true } or { error: ..., hint: ... }.

header('Content-Type: application/json');
error_reporting(E_ALL & ~E_WARNING & ~E_NOTICE);

$repoRoot = dirname(__DIR__);
$configPath = $repoRoot . '/config.json';

// Read incoming JSON
$body = file_get_contents('php://input');
if (!$body) {
    http_response_code(400);
    echo json_encode(['error' => 'Empty request body']);
    exit;
}

$incoming = json_decode($body, true);
if ($incoming === null) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON body']);
    exit;
}

// Load existing config (best-effort)
$existing = [];
if (is_readable($configPath)) {
    $raw = @file_get_contents($configPath);
    if ($raw !== false) {
        $decoded = json_decode($raw, true);
        if (is_array($decoded)) $existing = $decoded;
    }
}

// Merge incoming into existing, replacing scalar values and recursing into arrays
function merge_config(array $base, array $patch) {
    foreach ($patch as $k => $v) {
        if (is_array($v) && isset($base[$k]) && is_array($base[$k])) {
            $base[$k] = merge_config($base[$k], $v);
        } else {
            $base[$k] = $v;
        }
    }
    return $base;
}

$merged = merge_config($existing, $incoming);

// Write atomically using temp file + rename
$tmp = $configPath . '.tmp';
$written = @file_put_contents($tmp, json_encode($merged, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n", LOCK_EX);
if ($written === false) {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to write temp config file', 'hint' => 'Check directory permissions and owner (run permissions.sh on the host)']);
    exit;
}

if (!@rename($tmp, $configPath)) {
    // Attempt to cleanup temp file
    @unlink($tmp);
    http_response_code(500);
    echo json_encode(['error' => 'Failed to replace config.json', 'hint' => 'Check file ownership and that the webserver user can write to the repo']);
    exit;
}

// Ensure readable permissions
@chmod($configPath, 0644);

echo json_encode(['success' => true]);
?>
