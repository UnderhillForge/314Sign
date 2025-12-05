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

  // Validate file extension
  $allowedExts = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'webm', 'mov'];
  $ext = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
  
  if (!in_array($ext, $allowedExts)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid file extension']);
    logUpload('ERROR: Invalid extension: ' . $ext);
    exit;
  }

  // Generate unique filename
  $timestamp = date('Ymd_His');
  $filename = 'slide_' . $timestamp . '.' . $ext;
  $mediaDir = __DIR__ . '/media';
  
  // Create media directory if it doesn't exist
  if (!is_dir($mediaDir)) {
    mkdir($mediaDir, 0775, true);
  }
  
  $targetPath = $mediaDir . '/' . $filename;
  
  // Move uploaded file
  if (!move_uploaded_file($file['tmp_name'], $targetPath)) {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to save file']);
    logUpload('ERROR: Failed to move uploaded file to ' . $targetPath);
    exit;
  }

  // Set permissions
  chmod($targetPath, 0664);
  
  // Log success
  $fileSize = filesize($targetPath);
  logUpload("SUCCESS: Uploaded $filename ($fileSize bytes, $mimeType)");
  
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
