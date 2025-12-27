<?php
// Simple endpoint to update remote configuration
// This allows the main kiosk to push configuration to remotes

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: PUT, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

if ($_SERVER['REQUEST_METHOD'] !== 'PUT') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Get the JSON payload
$input = file_get_contents('php://input');
$data = json_decode($input, true);

if ($data === null) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON']);
    exit;
}

// Write to remote-config.json
$configFile = __DIR__ . '/remote-config.json';
$result = file_put_contents($configFile, json_encode($data, JSON_PRETTY_PRINT));

if ($result === false) {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to write config']);
    exit;
}

echo json_encode(['success' => true]);
?>
