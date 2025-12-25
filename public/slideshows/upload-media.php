<?php
// slideshows/upload-media.php - Handle media uploads for slideshows

header('Content-Type: application/json');
error_reporting(E_ALL);
ini_set('display_errors', '0');

// Log to file
function logUpload($message) {
  $logDir = __DIR__ . '/../logs';
  if (!is_dir($logDir)) mkdir($logDir, 0775, true);
  $logFile = $logDir . '/slideshow-uploads.log';
  $timestamp = date('Y-m-d H:i:s');
  file_put_contents($logFile, "[$timestamp] $message\n", FILE_APPEND);
}

try {
  if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    logUpload('ERROR: Invalid request method');
    exit;
  }

  if (!isset($_FILES['file'])) {
    http_response_code(400);
    echo json_encode(['error' => 'No file uploaded']);
    logUpload('ERROR: No file in request');
    exit;
  }

  $file = $_FILES['file'];
  
  // Check for upload errors
  if ($file['error'] !== UPLOAD_ERR_OK) {
    http_response_code(400);
    $errorMsg = 'Upload error code: ' . $file['error'];
    echo json_encode(['error' => $errorMsg]);
    logUpload('ERROR: ' . $errorMsg);
    exit;
  }

  // Validate MIME type (images and videos)
  $allowedMimes = [
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'video/mp4', 'video/webm', 'video/quicktime'
  ];
  
  $finfo = finfo_open(FILEINFO_MIME_TYPE);
  $mimeType = finfo_file($finfo, $file['tmp_name']);
  finfo_close($finfo);
  
  if (!in_array($mimeType, $allowedMimes)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid file type. Only images and videos allowed.']);
    logUpload('ERROR: Invalid MIME type: ' . $mimeType);
    exit;
  }

  // Size limits (bytes)
  $maxImageBytes = 10 * 1024 * 1024; // 10 MB
  $maxVideoBytes = 150 * 1024 * 1024; // 150 MB
  $size = isset($file['size']) ? intval($file['size']) : 0;

  if (strpos($mimeType, 'image/') === 0 && $size > $maxImageBytes) {
    http_response_code(413);
    echo json_encode(['error' => 'Image too large', 'hint' => 'Max image size is 10 MB']);
    logUpload('ERROR: Image too large: ' . $size);
    exit;
  }

  if (strpos($mimeType, 'video/') === 0 && $size > $maxVideoBytes) {
    http_response_code(413);
    echo json_encode(['error' => 'Video too large', 'hint' => 'Max video size is 150 MB']);
    logUpload('ERROR: Video too large: ' . $size);
    exit;
  }

  // Validate file extension
  $allowedExts = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'webm', 'mov'];
  $ext = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
  
  if (!in_array($ext, $allowedExts)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid file extension']);
    logUpload('ERROR: Invalid extension: ' . $ext);
    exit;
  }

  // Additional content validation for images
  if (strpos($mimeType, 'image/') === 0) {
    $imgInfo = @getimagesize($file['tmp_name']);
    if ($imgInfo === false) {
      http_response_code(400);
      echo json_encode(['error' => 'Uploaded file is not a valid image']);
      logUpload('ERROR: getimagesize failed for ' . $file['name']);
      exit;
    }
  }

  // Generate unique filename
  // Use timestamp + random suffix to avoid collisions and expose minimal original filename
  $timestamp = date('Ymd_His');
  $uniq = bin2hex(random_bytes(6));
  $filename = 'slide_' . $timestamp . '_' . $uniq . '.' . $ext;
  $mediaDir = __DIR__ . '/media';
  
  // Create media directory if it doesn't exist
  if (!is_dir($mediaDir)) {
    if (!mkdir($mediaDir, 0775, true)) {
      http_response_code(500);
      echo json_encode(['error' => 'Failed to create media directory', 'hint' => 'Check permissions and owner; run permissions.sh on the host']);
      logUpload('ERROR: Failed to create media directory: ' . $mediaDir);
      exit;
    }
  }
  
  $targetPath = $mediaDir . '/' . $filename;
  
  // Move uploaded file
  if (!is_uploaded_file($file['tmp_name'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Temporary upload missing or invalid']);
    logUpload('ERROR: tmp file not recognized as uploaded file: ' . $file['tmp_name']);
    exit;
  }

  if (!move_uploaded_file($file['tmp_name'], $targetPath)) {
    $last = error_get_last();
    $lastMsg = $last['message'] ?? null;
    http_response_code(500);
    echo json_encode(['error' => 'Failed to save file', 'detail' => $lastMsg, 'hint' => 'Check media directory ownership and writable permissions (run permissions.sh)']);
    logUpload('ERROR: Failed to move uploaded file to ' . $targetPath . ' - ' . ($lastMsg ?? 'unknown'));
    exit;
  }

  // Set permissions
  chmod($targetPath, 0664);
  
  // Log success
  $fileSize = filesize($targetPath);
  $remoteIp = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
  $origName = $file['name'] ?? 'unknown';
  logUpload("SUCCESS: Uploaded $filename (orig: $origName, size: $fileSize bytes, mime: $mimeType, ip: $remoteIp)");
  
  // Return success response
  echo json_encode([
    'filename' => $filename,
    'path' => 'media/' . $filename,
    'size' => $fileSize,
    'type' => $mimeType
  ]);

} catch (Exception $e) {
  http_response_code(500);
  echo json_encode(['error' => 'Server error: ' . $e->getMessage()]);
  logUpload('EXCEPTION: ' . $e->getMessage());
}
?>
