<?php
/**
 * Check for available updates from GitHub
 * Runs the update script in dry-run mode to check for changes
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

$script_path = __DIR__ . '/scripts/update-from-github.sh';

if (!file_exists($script_path)) {
    echo json_encode([
        'success' => false,
        'error' => 'Update script not found',
        'message' => 'Install the update script from GitHub repository'
    ]);
    exit;
}

// Run update script in dry-run mode
$output = [];
$return_var = 0;
exec("bash " . escapeshellarg($script_path) . " --dry-run 2>&1", $output, $return_var);

// Parse output to detect if updates are available
$output_text = implode("\n", $output);
$updates_available = false;
$changed_files = [];

// Look for "Would update:" or "Different:" in output
if (preg_match_all('/(?:Would update|Different):\s*(.+)$/m', $output_text, $matches)) {
    $updates_available = true;
    $changed_files = $matches[1];
}

// Check for "No updates needed" message
if (strpos($output_text, 'No updates needed') !== false || 
    strpos($output_text, 'All files are up to date') !== false) {
    $updates_available = false;
    $changed_files = [];
}

$response = [
    'success' => true,
    'updates_available' => $updates_available,
    'message' => $updates_available 
        ? count($changed_files) . ' file(s) need updating' 
        : 'All files are up to date',
    'files' => $changed_files,
    'output' => $output_text
];

echo json_encode($response);
?>
