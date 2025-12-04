<?php
/**
 * Check for available updates from GitHub
 * This is a simplified endpoint that returns mock data
 * Real update checking is done via scripts/update-from-github.sh
 */

header('Content-Type: application/json');

// This endpoint is a placeholder
// Actual update checking requires shell access to run the update script
// For now, return that manual checking is required

$response = [
    'success' => true,
    'updates_available' => false,
    'message' => 'Run scripts/update-from-github.sh --dry-run to check for updates',
    'files' => []
];

echo json_encode($response);
?>
