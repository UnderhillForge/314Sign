<?php
/**
 * Apply updates from GitHub
 * Runs the update script with --backup flag
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

// Run update script with --backup flag
$output = [];
$return_var = 0;
exec("sudo bash " . escapeshellarg($script_path) . " --backup 2>&1", $output, $return_var);

$output_text = implode("\n", $output);
$success = $return_var === 0;

// Check if backup was created
$backup_created = strpos($output_text, 'Backup created') !== false;

// Count updated files
$updated_count = 0;
if (preg_match_all('/Updated:\s*(.+)$/m', $output_text, $matches)) {
    $updated_count = count($matches[1]);
}

$response = [
    'success' => $success,
    'message' => $success 
        ? ($updated_count > 0 ? "Updated $updated_count file(s)" : 'No updates applied')
        : 'Update failed',
    'backup_created' => $backup_created,
    'files_updated' => $updated_count,
    'output' => $output_text,
    'exit_code' => $return_var
];

echo json_encode($response);
?>
