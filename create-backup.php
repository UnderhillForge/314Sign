<?php
/**
 * Create backup of menus and configuration
 * Runs the backup script
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

$script_path = __DIR__ . '/scripts/backup.sh';

if (!file_exists($script_path)) {
    echo json_encode([
        'success' => false,
        'error' => 'Backup script not found',
        'message' => 'Install the backup script from GitHub repository'
    ]);
    exit;
}

// Run backup script
$output = [];
$return_var = 0;
exec("bash " . escapeshellarg($script_path) . " 2>&1", $output, $return_var);

$output_text = implode("\n", $output);
$success = $return_var === 0;

// Extract backup location from output
$backup_location = '';
if (preg_match('/Backup created:\s*(.+)$/m', $output_text, $matches)) {
    $backup_location = trim($matches[1]);
}

// Count backed up files
$file_count = 0;
if (preg_match('/(\d+)\s+files? backed up/i', $output_text, $matches)) {
    $file_count = (int)$matches[1];
}

$response = [
    'success' => $success,
    'message' => $success 
        ? ($file_count > 0 ? "Backup created: $file_count files" : 'Backup completed')
        : 'Backup failed',
    'backup_location' => $backup_location,
    'file_count' => $file_count,
    'output' => $output_text,
    'exit_code' => $return_var
];

echo json_encode($response);
?>
