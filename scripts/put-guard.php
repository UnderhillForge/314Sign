<?php
// scripts/put-guard.php
// Guard endpoint: intentionally rejects raw PUTs to /config.json and provides guidance.
header('Content-Type: application/json');

// If this script was invoked via internal rewrite for a PUT request, return 405
if ($_SERVER['REQUEST_METHOD'] === 'PUT') {
    http_response_code(405);
    echo json_encode([
        'success' => false,
        'error' => 'Direct PUT to config.json is disallowed',
        'hint' => 'Use scripts/merge-config.php POST with partial JSON to update config.json safely'
    ]);
    exit;
}

// Fallback: for any other method, return 200 with info
echo json_encode([
    'success' => true,
    'note' => 'config.json is managed; use scripts/merge-config.php to make non-destructive updates'
]);
exit;
