<?php
/**
 * Purge all menu history files
 */

header('Content-Type: application/json');

// Check if request method is POST
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

$historyDir = __DIR__ . '/history';

if (!is_dir($historyDir)) {
    echo json_encode([
        'success' => true,
        'deleted' => 0,
        'message' => 'History directory does not exist'
    ]);
    exit;
}

// Get all history files
$files = glob($historyDir . '/*.txt');
$deleted = 0;

foreach ($files as $file) {
    if (unlink($file)) {
        $deleted++;
    }
}

// Log the purge
$logFile = __DIR__ . '/logs/history.log';
$logDir = dirname($logFile);
if (!is_dir($logDir)) {
    mkdir($logDir, 0775, true);
}

$logEntry = json_encode([
    'timestamp' => date('c'),
    'action' => 'purge_all',
    'deleted' => $deleted
]) . "\n";

file_put_contents($logFile, $logEntry, FILE_APPEND);

echo json_encode([
    'success' => true,
    'deleted' => $deleted,
    'message' => "Deleted $deleted history file(s)"
]);
