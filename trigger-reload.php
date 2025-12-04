<?php
/**
 * Trigger kiosk reload by updating reload.txt timestamp
 * This is an alternative to WebDAV PUT for reload.txt
 */

header('Content-Type: application/json');

// Security: Only allow from localhost/same host
$allowed_hosts = ['localhost', '127.0.0.1', $_SERVER['SERVER_NAME']];
if (!in_array($_SERVER['REMOTE_ADDR'], ['127.0.0.1', '::1']) && 
    !in_array($_SERVER['HTTP_HOST'], $allowed_hosts)) {
    http_response_code(403);
    echo json_encode(['success' => false, 'error' => 'Access denied']);
    exit;
}

$reload_file = __DIR__ . '/reload.txt';

// Create file if it doesn't exist
if (!file_exists($reload_file)) {
    if (!touch($reload_file)) {
        echo json_encode([
            'success' => false,
            'error' => 'Could not create reload.txt',
            'path' => $reload_file
        ]);
        exit;
    }
}

// Write current timestamp
$timestamp = (string)time();
$result = file_put_contents($reload_file, $timestamp);

if ($result === false) {
    echo json_encode([
        'success' => false,
        'error' => 'Failed to write reload token',
        'path' => $reload_file,
        'permissions' => substr(sprintf('%o', fileperms($reload_file)), -4)
    ]);
    exit;
}

echo json_encode([
    'success' => true,
    'message' => 'Reload triggered',
    'timestamp' => $timestamp
]);
?>
