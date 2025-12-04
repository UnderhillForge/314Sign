<?php
/**
 * List or restore menu history
 */

header('Content-Type: application/json');

$action = $_GET['action'] ?? 'list';
$menuName = $_GET['menu'] ?? '';

// Sanitize menu name
$menuName = preg_replace('/[^a-z]/', '', strtolower($menuName));
if (!in_array($menuName, ['breakfast', 'lunch', 'dinner', 'closed', ''])) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid menu name']);
    exit;
}

$historyDir = __DIR__ . '/history';

if ($action === 'list') {
    // List all history files, optionally filtered by menu
    $pattern = empty($menuName) 
        ? $historyDir . '/*.txt'
        : $historyDir . '/' . $menuName . '_*.txt';
    
    $files = glob($pattern);
    $history = [];
    
    foreach ($files as $file) {
        $basename = basename($file, '.txt');
        $parts = explode('_', $basename);
        
        // Format: MENUNAME_YYYY-MM-DD_DayOfWeek (3 parts)
        if (count($parts) >= 3) {
            $history[] = [
                'filename' => basename($file),
                'menu' => $parts[0],
                'date' => $parts[1],
                'dayOfWeek' => $parts[2],
                'timestamp' => filemtime($file),
                'size' => filesize($file)
            ];
        }
    }
    
    // Sort by timestamp, newest first
    usort($history, function($a, $b) {
        return $b['timestamp'] - $a['timestamp'];
    });
    
    echo json_encode(['history' => $history]);
    
} elseif ($action === 'get') {
    // Get content of a specific history file
    $filename = $_GET['filename'] ?? '';
    $filename = basename($filename); // Security: prevent directory traversal
    
    $filepath = $historyDir . '/' . $filename;
    
    if (!file_exists($filepath)) {
        http_response_code(404);
        echo json_encode(['error' => 'History file not found']);
        exit;
    }
    
    $content = file_get_contents($filepath);
    echo json_encode(['content' => $content]);
    
} else {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid action']);
}
