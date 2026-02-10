<?php
/**
 * Restart lighttpd web server
 * Requires www-data to have sudo access for systemctl restart lighttpd
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

// Try to restart lighttpd
$output = [];
$return_var = 0;
exec("sudo systemctl restart lighttpd 2>&1", $output, $return_var);

$output_text = implode("\n", $output);
$success = $return_var === 0;

// If sudo fails, provide instructions
if (!$success && strpos($output_text, 'sudo') !== false) {
    echo json_encode([
        'success' => false,
        'error' => 'sudo permission required',
        'message' => 'Add to /etc/sudoers.d/www-data: www-data ALL=(ALL) NOPASSWD: /bin/systemctl restart lighttpd',
        'output' => $output_text
    ]);
    exit;
}

$response = [
    'success' => $success,
    'message' => $success ? 'Server restarted successfully' : 'Restart failed',
    'output' => $output_text,
    'exit_code' => $return_var
];

echo json_encode($response);
?>
