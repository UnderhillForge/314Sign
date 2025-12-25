<?php
/**
 * Set current menu via external control
 * Updates current-menu.json to switch which menu is displayed
 * 
 * Usage: 
 *   POST with JSON body: {"menu": "menus/lunch.txt"}
 *   GET with query param: ?menu=menus/breakfast.txt
 */

header('Content-Type: application/json');

// Allow both GET and POST requests
$method = $_SERVER['REQUEST_METHOD'];
if ($method !== 'POST' && $method !== 'GET') {
    http_response_code(405);
    echo json_encode(['success' => false, 'error' => 'Method not allowed']);
    exit;
}

// Get menu from POST body or GET query
$menu = null;
if ($method === 'POST') {
    $input = file_get_contents('php://input');
    $data = json_decode($input, true);
    $menu = $data['menu'] ?? null;
} else {
    $menu = $_GET['menu'] ?? null;
}

// Validate menu parameter
if (!$menu) {
    http_response_code(400);
    echo json_encode(['success' => false, 'error' => 'Missing menu parameter']);
    exit;
}

// Validate menu format (should be menus/*.txt)
if (!preg_match('#^menus/[a-zA-Z0-9_-]+\.txt$#', $menu)) {
    http_response_code(400);
    echo json_encode([
        'success' => false, 
        'error' => 'Invalid menu format. Expected: menus/[name].txt',
        'provided' => $menu
    ]);
    exit;
}

// Check if menu file exists
$menu_path = __DIR__ . '/' . $menu;
if (!file_exists($menu_path)) {
    http_response_code(404);
    echo json_encode([
        'success' => false,
        'error' => 'Menu file not found',
        'menu' => $menu,
        'path' => $menu_path
    ]);
    exit;
}

$current_menu_file = __DIR__ . '/current-menu.json';

// Create JSON content
$content = json_encode(['menu' => $menu], JSON_PRETTY_PRINT) . "\n";

// Write to current-menu.json
$result = file_put_contents($current_menu_file, $content);

if ($result === false) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => 'Failed to write current-menu.json',
        'path' => $current_menu_file,
        'permissions' => file_exists($current_menu_file) ? substr(sprintf('%o', fileperms($current_menu_file)), -4) : 'N/A'
    ]);
    exit;
}

echo json_encode([
    'success' => true,
    'message' => 'Current menu updated',
    'menu' => $menu,
    'timestamp' => time()
]);
?>
