<?php
// Simple endpoint to update remote configuration
// This allows the main kiosk to push configuration to remotes

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: PUT, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

if ($_SERVER['REQUEST_METHOD'] !== 'PUT' && $_SERVER['REQUEST_METHOD'] !== 'POST') {
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

// Read existing configuration
$configFile = __DIR__ . '/remote-config.json';
$existingConfig = [];
if (file_exists($configFile)) {
    $existingData = file_get_contents($configFile);
    if ($existingData !== false) {
        $existingConfig = json_decode($existingData, true) ?: [];
    }
}

// For PUT: replace entire config
// For POST: merge with existing config
if ($_SERVER['REQUEST_METHOD'] === 'PUT') {
    $finalConfig = $data;
} else { // POST
    $finalConfig = array_merge($existingConfig, $data);
}

// Write updated configuration
$result = file_put_contents($configFile, json_encode($finalConfig, JSON_PRETTY_PRINT));

if ($result === false) {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to write config']);
    exit;
}

echo json_encode(['success' => true, 'method' => $_SERVER['REQUEST_METHOD']]);
?>
