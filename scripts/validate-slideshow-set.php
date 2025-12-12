<?php
// scripts/validate-slideshow-set.php
// Validate slideshow set JSON. Usage: POST JSON body with either { "filename": "slideshows/sets/name.json" }
// or { "content": { ... } } to validate in-memory content.

header('Content-Type: application/json');

$body = file_get_contents('php://input');
if (!$body) {
    http_response_code(400);
    echo json_encode(['success' => false, 'errors' => ['Empty request body']]);
    exit;
}

$data = json_decode($body, true);
if ($data === null) {
    http_response_code(400);
    echo json_encode(['success' => false, 'errors' => ['Invalid JSON']]);
    exit;
}

$content = null;
if (isset($data['filename'])) {
    $filename = basename($data['filename']);
    $path = __DIR__ . '/../slideshows/sets/' . $filename;
    if (!file_exists($path)) {
        http_response_code(404);
        echo json_encode(['success' => false, 'errors' => ["File not found: sets/{$filename}"]]);
        exit;
    }
    $raw = file_get_contents($path);
    $content = json_decode($raw, true);
    if ($content === null) {
        http_response_code(400);
        echo json_encode(['success' => false, 'errors' => ['File is not valid JSON']]);
        exit;
    }
} elseif (isset($data['content'])) {
    $content = $data['content'];
} else {
    http_response_code(400);
    echo json_encode(['success' => false, 'errors' => ['Provide filename or content to validate']]);
    exit;
}

$errors = [];

// Top-level checks
if (!is_array($content)) {
    $errors[] = 'Top-level content must be an object';
} else {
    if (!isset($content['slides']) || !is_array($content['slides'])) {
        $errors[] = 'Missing required array property: slides';
    }

    // Optional: defaultDuration and defaultTransition
    if (isset($content['defaultDuration']) && !is_numeric($content['defaultDuration'])) {
        $errors[] = 'defaultDuration must be numeric';
    }
    if (isset($content['defaultTransition']) && !is_string($content['defaultTransition'])) {
        $errors[] = 'defaultTransition must be a string';
    }

    // Validate slides
    if (isset($content['slides']) && is_array($content['slides'])) {
        foreach ($content['slides'] as $i => $slide) {
            $path = "slides[$i]";
            if (!is_array($slide)) {
                $errors[] = "$path must be an object";
                continue;
            }
            // type
            if (empty($slide['type']) || !is_string($slide['type'])) {
                $errors[] = "$path.type is required and must be a string";
                continue;
            }
            $type = $slide['type'];
            if (!in_array($type, ['text', 'image', 'video'])) {
                $errors[] = "$path.type must be one of: text, image, video";
                continue;
            }
            // duration
            if (isset($slide['duration']) && !is_numeric($slide['duration'])) {
                $errors[] = "$path.duration must be numeric";
            }
            // type-specific
            if ($type === 'text') {
                if (!isset($slide['content']) || !is_string($slide['content'])) {
                    $errors[] = "$path.content is required for text slides";
                }
            } elseif ($type === 'image' || $type === 'video') {
                if (empty($slide['media']) || !is_string($slide['media'])) {
                    $errors[] = "$path.media is required for $type slides and must be a string (e.g., media/file.jpg)";
                } else {
                    // simple path validation: should not contain .. and should be relative
                    if (strpos($slide['media'], '..') !== false) {
                        $errors[] = "$path.media contains invalid path segments";
                    }
                }
            }
        }
    }
}

if (count($errors) > 0) {
    echo json_encode(['success' => false, 'errors' => $errors]);
    exit;
}

// All good
echo json_encode(['success' => true, 'message' => 'Valid slideshow set']);
exit;
