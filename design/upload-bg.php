<?php
header('Content-Type: application/json');

// --- simple JSON-line logger (logs/uploads.log) -----------------------
$logDir = dirname(__DIR__) . '/logs';
if (!is_dir($logDir)) {
    @mkdir($logDir, 0755, true);
}
$logFile = $logDir . '/uploads.log';

function log_entry($level, $msg, $meta = []) {
    global $logFile;
    $entry = [
        'ts' => date('c'),
        'level' => $level,
        'msg' => $msg,
        'meta' => $meta
    ];
    // best-effort append; don't break upload flow on logging failure
    @file_put_contents($logFile, json_encode($entry) . "\n", FILE_APPEND | LOCK_EX);
}

// Only allow POST
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    log_entry('warn', 'Method not allowed', ['method' => $_SERVER['REQUEST_METHOD']]);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Helper to translate upload error codes to messages
function upload_error_message($code) {
    $map = [
        UPLOAD_ERR_OK => 'There is no error, the file uploaded with success.',
        UPLOAD_ERR_INI_SIZE => 'The uploaded file exceeds the upload_max_filesize directive.',
        UPLOAD_ERR_FORM_SIZE => 'The uploaded file exceeds the MAX_FILE_SIZE directive that was specified in the HTML form.',
        UPLOAD_ERR_PARTIAL => 'The uploaded file was only partially uploaded.',
        UPLOAD_ERR_NO_FILE => 'No file was uploaded.',
        UPLOAD_ERR_NO_TMP_DIR => 'Missing a temporary folder.',
        UPLOAD_ERR_CANT_WRITE => 'Failed to write file to disk.',
        UPLOAD_ERR_EXTENSION => 'A PHP extension stopped the file upload.'
    ];
    return isset($map[$code]) ? $map[$code] : 'Unknown upload error.';
}

// Validate presence
if (!isset($_FILES['image'])) {
    http_response_code(400);
    log_entry('error', 'No file field named "image" found');
    echo json_encode(['error' => 'No file field named "image" found.']);
    exit;
}

$file = $_FILES['image'];
if (!isset($file['error']) || $file['error'] !== UPLOAD_ERR_OK) {
    $msg = isset($file['error']) ? upload_error_message($file['error']) : 'Missing error code';
    http_response_code(400);
    log_entry('error', 'Upload failed', ['detail' => $msg, 'code' => $file['error'] ?? null, 'client_ip' => $_SERVER['REMOTE_ADDR'] ?? null]);
    echo json_encode(['error' => "Upload failed", 'detail' => $msg, 'code' => $file['error'] ?? null]);
    exit;
}

// Basic extension check
$ext = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
$allowed_ext = ['jpg','jpeg','png','gif','webp'];
if (!in_array($ext, $allowed_ext, true)) {
    http_response_code(400);
    log_entry('warn', 'Invalid file extension', ['ext' => $ext, 'original_name' => $file['name']]);
    echo json_encode(['error' => 'Invalid file extension', 'ext' => $ext]);
    exit;
}

// MIME type check using finfo to avoid spoofed extensions
$finfo = finfo_open(FILEINFO_MIME_TYPE);
$mime = finfo_file($finfo, $file['tmp_name']);
finfo_close($finfo);
$allowed_mimes = [
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp'
];
if (!in_array($mime, $allowed_mimes, true)) {
    http_response_code(400);
    log_entry('warn', 'Invalid MIME type', ['mime' => $mime, 'original_name' => $file['name']]);
    echo json_encode(['error' => 'Invalid MIME type', 'mime' => $mime]);
    exit;
}

// Ensure bg directory exists and is writable
$bgDir = dirname(__DIR__) . '/bg';
if (!is_dir($bgDir)) {
    if (!mkdir($bgDir, 0755, true)) {
        http_response_code(500);
        log_entry('error', 'Failed to create bg directory', ['bgDir' => $bgDir]);
        echo json_encode(['error' => 'Failed to create bg directory']);
        exit;
    }
}
if (!is_writable($bgDir)) {
    // Attempt to chmod; if it fails, return an error
    @chmod($bgDir, 0755);
    if (!is_writable($bgDir)) {
        http_response_code(500);
        log_entry('error', 'bg directory is not writable', ['bgDir' => $bgDir]);
        echo json_encode(['error' => 'bg directory is not writable']);
        exit;
    }
}

// Save to bg/ with unique name
try {
    $filename = 'uploaded_' . time() . '_' . bin2hex(random_bytes(4)) . '.' . $ext;
} catch (Exception $e) {
    // random_bytes can throw; fallback to less-strong random
    $filename = 'uploaded_' . time() . '_' . substr(md5(uniqid('', true)), 0, 8) . '.' . $ext;
}
$path = $bgDir . '/' . $filename;

// Ensure the temporary file was indeed uploaded via HTTP POST
if (!is_uploaded_file($file['tmp_name'])) {
    http_response_code(400);
    log_entry('error', 'Temporary file missing or invalid', ['tmp_name' => $file['tmp_name']]);
    echo json_encode(['error' => 'Temporary file missing or invalid']);
    exit;
}

if (!move_uploaded_file($file['tmp_name'], $path)) {
    $last = error_get_last();
    http_response_code(500);
    log_entry('error', 'Failed to move uploaded file', ['detail' => $last['message'] ?? null, 'tmp_name' => $file['tmp_name'], 'target' => $path]);
    echo json_encode(['error' => 'Failed to move uploaded file', 'detail' => $last['message'] ?? null]);
    exit;
}

// Set permissive but safe permissions
@chmod($path, 0644);

// Log success with useful metadata
log_entry('info', 'Upload successful', ['filename' => $filename, 'mime' => $mime, 'size' => $file['size'] ?? null, 'client_ip' => $_SERVER['REMOTE_ADDR'] ?? null]);

// Return new filename (and MIME for client debugging)
echo json_encode(['filename' => $filename, 'mime' => $mime]);
?>