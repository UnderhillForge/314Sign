<?php
/**
 * Save menu history and prune old versions
 * Called when a menu file is saved
 */

header('Content-Type: application/json');

// Get the menu name and content from POST
$menuName = $_POST['menu'] ?? '';
$content = $_POST['content'] ?? '';

if (empty($menuName) || empty($content)) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing menu name or content']);
    exit;
}

// Sanitize menu name (breakfast, lunch, dinner, closed)
$menuName = preg_replace('/[^a-z]/', '', strtolower($menuName));
if (!in_array($menuName, ['breakfast', 'lunch', 'dinner', 'closed'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid menu name']);
    exit;
}

$historyDir = __DIR__ . '/history';
if (!is_dir($historyDir)) {
    mkdir($historyDir, 0775, true);
}

// Create filename with format: MENUNAME_YYYY-MM-DD_DayOfWeek_HHMMSS.txt
$timestamp = time();
$date = date('Y-m-d', $timestamp);
$dayOfWeek = date('l', $timestamp); // Monday, Tuesday, etc.
$time = date('His', $timestamp);
$filename = "{$menuName}_{$date}_{$dayOfWeek}_{$time}.txt";
$filepath = $historyDir . '/' . $filename;

// Save history file
if (file_put_contents($filepath, $content) === false) {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to save history']);
    exit;
}

// Prune old history files (older than 7 days)
$cutoffTime = $timestamp - (7 * 24 * 60 * 60);
$files = glob($historyDir . '/*.txt');
$pruned = 0;

foreach ($files as $file) {
    if (filemtime($file) < $cutoffTime) {
        unlink($file);
        $pruned++;
    }
}

// Log the save
$logFile = __DIR__ . '/logs/history.log';
$logDir = dirname($logFile);
if (!is_dir($logDir)) {
    mkdir($logDir, 0775, true);
}

$logEntry = json_encode([
    'timestamp' => date('c', $timestamp),
    'menu' => $menuName,
    'filename' => $filename,
    'pruned' => $pruned
]) . "\n";

file_put_contents($logFile, $logEntry, FILE_APPEND);

echo json_encode([
    'success' => true,
    'filename' => $filename,
    'pruned' => $pruned
]);
