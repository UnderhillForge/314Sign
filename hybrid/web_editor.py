#!/usr/bin/env python3
"""
314Sign Web LMS Content Editor
Web-based visual LMS content creation interface
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
import subprocess
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes

class LMSEditorWebServer(BaseHTTPRequestHandler):
    """
    Web server for LMS visual content editor
    Provides HTML interface for drag-and-drop LMS creation
    """

    def __init__(self, *args, templates_dir=None, output_dir=None, **kwargs):
        self.templates_dir = Path(templates_dir or "/opt/314sign/templates")
        self.output_dir = Path(output_dir or "/home/pi/lms")
        self.templates_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests"""
        path = urllib.parse.urlparse(self.path).path

        if path == "/":
            self.serve_editor_interface()
        elif path == "/api/templates":
            self.serve_templates()
        elif path == "/api/fonts":
            self.serve_fonts()
        elif path == "/api/backgrounds":
            self.serve_backgrounds()
        elif path.startswith("/static/"):
            self.serve_static_file(path)
        else:
            self.send_error(404)

    def do_POST(self):
        """Handle POST requests"""
        path = urllib.parse.urlparse(self.path).path

        if path == "/api/save":
            self.save_lms_content()
        elif path == "/api/save-template":
            self.save_template()
        elif path == "/api/preview":
            self.generate_preview()
        else:
            self.send_error(404)

    def serve_editor_interface(self):
        """Serve the main LMS editor HTML interface"""
        html = self.generate_editor_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

    def generate_editor_html(self):
        """Generate the HTML for the LMS visual editor"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>314Sign LMS Content Editor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            color: #333;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .header h1 {
            font-size: 1.5rem;
        }

        .container {
            display: flex;
            height: calc(100vh - 70px);
        }

        .sidebar {
            width: 300px;
            background: white;
            border-right: 1px solid #ddd;
            padding: 1rem;
            overflow-y: auto;
        }

        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
        }

        .toolbar {
            background: white;
            border-bottom: 1px solid #ddd;
            padding: 0.5rem;
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }

        .canvas-container {
            flex: 1;
            position: relative;
            background: #f0f0f0;
            overflow: hidden;
        }

        .canvas {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            border: 2px solid #ddd;
        }

        .element-palette {
            margin-bottom: 1rem;
        }

        .element-palette h3 {
            margin-bottom: 0.5rem;
            color: #666;
        }

        .element-item {
            padding: 0.5rem;
            margin-bottom: 0.5rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            cursor: grab;
            background: white;
            transition: all 0.2s;
        }

        .element-item:hover {
            border-color: #667eea;
            background: #f8f9ff;
        }

        .properties-panel {
            margin-top: 1rem;
        }

        .properties-panel h3 {
            margin-bottom: 0.5rem;
            color: #666;
        }

        .property-group {
            margin-bottom: 1rem;
        }

        .property-group label {
            display: block;
            margin-bottom: 0.25rem;
            font-weight: 500;
        }

        .property-group input,
        .property-group select,
        .property-group textarea {
            width: 100%;
            padding: 0.5rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 0.9rem;
        }

        .btn {
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s;
        }

        .btn-primary {
            background: #667eea;
            color: white;
        }

        .btn-primary:hover {
            background: #5a67d8;
        }

        .btn-secondary {
            background: #e2e8f0;
            color: #4a5568;
        }

        .btn-secondary:hover {
            background: #cbd5e0;
        }

        .element {
            position: absolute;
            min-width: 50px;
            min-height: 30px;
            border: 1px solid #ddd;
            background: rgba(255, 255, 255, 0.8);
            cursor: move;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            resize: both;
            overflow: hidden;
        }

        .element.selected {
            border-color: #667eea;
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
        }

        .element.text-element {
            background: rgba(255, 255, 255, 0.9);
            color: #333;
        }

        .element.image-element {
            background: rgba(200, 200, 200, 0.5);
            color: #666;
        }

        .resize-handle {
            position: absolute;
            width: 8px;
            height: 8px;
            background: #667eea;
            border-radius: 50%;
            bottom: -4px;
            right: -4px;
            cursor: nw-resize;
        }

        .templates-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }

        .template-item {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 0.5rem;
            cursor: pointer;
            text-align: center;
            transition: all 0.2s;
        }

        .template-item:hover {
            border-color: #667eea;
            background: #f8f9ff;
        }

        .template-item.selected {
            border-color: #667eea;
            background: #667eea;
            color: white;
        }

        .color-picker {
            display: flex;
            gap: 0.25rem;
            flex-wrap: wrap;
            margin-top: 0.25rem;
        }

        .color-swatch {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            cursor: pointer;
            border: 1px solid #ddd;
        }

        .font-selector {
            max-height: 150px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-top: 0.25rem;
        }

        .font-option {
            padding: 0.5rem;
            cursor: pointer;
            border-bottom: 1px solid #eee;
            transition: background 0.2s;
        }

        .font-option:hover {
            background: #f8f9ff;
        }

        .font-option.selected {
            background: #667eea;
            color: white;
        }

        .modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }

        .modal-content {
            background: white;
            padding: 2rem;
            border-radius: 8px;
            max-width: 500px;
            width: 90%;
        }

        .modal h2 {
            margin-bottom: 1rem;
            color: #333;
        }

        .modal .btn {
            margin-right: 0.5rem;
        }

        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4caf50;
            color: white;
            padding: 1rem;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            z-index: 1001;
            animation: slideIn 0.3s ease-out;
        }

        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        /* Mobile responsiveness */
        @media (max-width: 768px) {
            .container {
                flex-direction: column;
            }
            .sidebar {
                width: 100%;
                height: 200px;
                order: 2;
            }
            .main-content {
                order: 1;
            }
            .toolbar {
                padding: 0.25rem;
                flex-wrap: wrap;
                gap: 0.25rem;
            }
            .toolbar button {
                padding: 0.5rem;
                font-size: 0.8rem;
            }
            .canvas {
                width: 100% !important;
                height: 60vh !important;
                max-width: none !important;
            }
            .header h1 {
                font-size: 1.2rem;
            }
        }

        @media (max-width: 480px) {
            .toolbar {
                justify-content: center;
            }
            .toolbar button {
                flex: 1;
                min-width: 80px;
                padding: 0.75rem 0.5rem;
                font-size: 0.75rem;
            }
            .sidebar {
                height: 150px;
            }
            .element-palette {
                display: flex;
                overflow-x: auto;
                padding-bottom: 0.5rem;
            }
            .element-item {
                flex-shrink: 0;
                width: 60px;
                height: 60px;
                margin-right: 0.5rem;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                font-size: 0.7rem;
                text-align: center;
            }
            .properties-panel {
                height: 120px;
                overflow-y: auto;
            }
            .canvas {
                height: 50vh !important;
            }
        }

        /* Touch-friendly interactions */
        @media (hover: none) and (pointer: coarse) {
            .element-item {
                min-height: 50px;
                padding: 1rem;
            }
            .element-item:active {
                background: #667eea;
                color: white;
            }
            .btn:active {
                transform: scale(0.95);
            }
            .element {
                touch-action: none;
            }
        }

        /* High DPI displays */
        @media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
            .element-item {
                font-size: 1.2em;
            }
            .btn {
                font-size: 1.1em;
            }
        }

        /* Tablet optimizations */
        @media (min-width: 481px) and (max-width: 768px) {
            .sidebar {
                height: 180px;
            }
            .canvas {
                height: 70vh !important;
            }
            .element-palette {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
                gap: 0.5rem;
            }
            .element-item {
                height: 70px;
                font-size: 0.8rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>314Sign LMS Content Editor</h1>
    </div>

    <div class="container">
        <div class="sidebar">
            <div class="element-palette">
                <h3>Elements</h3>
                <div class="element-item" data-type="text">📝 Text</div>
                <div class="element-item" data-type="image">🖼️ Image</div>
                <div class="element-item" data-type="rectangle">▭ Rectangle</div>
                <div class="element-item" data-type="circle">⭕ Circle</div>
                <div class="element-item" data-type="time">🕐 Current Time</div>
                <div class="element-item" data-type="date">📅 Current Date</div>
            </div>

            <div class="properties-panel">
                <h3>Properties</h3>
                <div id="properties-container">
                    <p>Select an element to edit properties</p>
                </div>
            </div>
        </div>

        <div class="main-content">
            <div class="toolbar">
                <button class="btn btn-secondary" id="load-template">📋 Load Template</button>
                <button class="btn btn-secondary" id="save-template">📝 Save as Template</button>
                <button class="btn btn-secondary" id="save-lms">💾 Save LMS</button>
                <button class="btn btn-primary" id="preview">👁️ Preview</button>
                <button class="btn btn-secondary" id="clear-canvas">🗑️ Clear</button>
                <span id="status">Ready</span>
            </div>

            <div class="canvas-container">
                <div class="canvas" id="canvas" style="width: 1080px; height: 1920px;">
                    <!-- Canvas elements will be added here -->
                </div>
            </div>
        </div>
    </div>

    <!-- Templates Modal -->
    <div id="templates-modal" class="modal" style="display: none;">
        <div class="modal-content">
            <h2>Choose Template</h2>
            <div class="templates-grid" id="templates-grid">
                <div class="template-item" data-template="restaurant">
                    <div>🍽️</div>
                    <div>Restaurant Menu</div>
                </div>
                <div class="template-item" data-template="office">
                    <div>🏢</div>
                    <div>Office Directory</div>
                </div>
                <div class="template-item" data-template="school">
                    <div>🎓</div>
                    <div>School Schedule</div>
                </div>
                <div class="template-item" data-template="retail">
                    <div>🛍️</div>
                    <div>Retail Display</div>
                </div>
                <div class="template-item" data-template="blank">
                    <div>📄</div>
                    <div>Blank Canvas</div>
                </div>
            </div>
            <div style="margin-top: 1rem;">
                <button class="btn btn-secondary" onclick="closeTemplatesModal()">Cancel</button>
            </div>
        </div>
    </div>

    <!-- Save Template Modal -->
    <div id="save-template-modal" class="modal" style="display: none;">
        <div class="modal-content">
            <h2>Save as Template</h2>
            <div class="property-group">
                <label>Template Name:</label>
                <input type="text" id="template-name" placeholder="e.g., My Custom Layout" required>
            </div>
            <div class="property-group">
                <label>Description:</label>
                <textarea id="template-description" placeholder="Describe your template..." rows="3"></textarea>
            </div>
            <div style="margin-top: 1rem;">
                <button class="btn btn-primary" onclick="saveTemplate()">Save Template</button>
                <button class="btn btn-secondary" onclick="closeSaveTemplateModal()">Cancel</button>
            </div>
        </div>
    </div>

    <script>
        // Global state
        let selectedElement = null;
        let elements = [];
        let elementCounter = 0;
        const canvas = document.getElementById('canvas');

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            setupEventListeners();
            updateCanvasSize();
        });

        function setupEventListeners() {
            // Element palette drag and drop - mouse and touch
            document.querySelectorAll('.element-item').forEach(item => {
                item.addEventListener('mousedown', startDrag);
                item.addEventListener('touchstart', startDragTouch, { passive: false });
            });

            // Canvas interactions - mouse and touch
            canvas.addEventListener('mousedown', handleCanvasClick);
            canvas.addEventListener('touchstart', handleCanvasTouch, { passive: false });
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('touchmove', handleTouchMove, { passive: false });
            document.addEventListener('mouseup', stopDrag);
            document.addEventListener('touchend', stopDrag);

            // Toolbar buttons
            document.getElementById('load-template').addEventListener('click', showTemplatesModal);
            document.getElementById('save-template').addEventListener('click', showSaveTemplateModal);
            document.getElementById('save-lms').addEventListener('click', saveLMS);
            document.getElementById('preview').addEventListener('click', previewLMS);
            document.getElementById('clear-canvas').addEventListener('click', clearCanvas);

            // Template selection
            document.getElementById('templates-grid').addEventListener('click', handleTemplateSelect);

            // Window resize
            window.addEventListener('resize', updateCanvasSize);
        }

        function updateCanvasSize() {
            // This would dynamically adjust canvas size based on display configuration
            // For now, keep it fixed at portrait dimensions
        }

        let draggedElement = null;
        let dragOffset = { x: 0, y: 0 };
        let isDragging = false;
        let isResizing = false;

        function startDrag(e) {
            e.preventDefault();
            const elementType = e.target.dataset.type;
            draggedElement = createElement(elementType, e.clientX, e.clientY);
            isDragging = true;
        }

        function handleMouseMove(e) {
            if (!isDragging || !draggedElement) return;

            const canvasRect = canvas.getBoundingClientRect();
            const x = e.clientX - canvasRect.left - dragOffset.x;
            const y = e.clientY - canvasRect.top - dragOffset.y;

            draggedElement.style.left = Math.max(0, Math.min(x, canvasRect.width - draggedElement.offsetWidth)) + 'px';
            draggedElement.style.top = Math.max(0, Math.min(y, canvasRect.height - draggedElement.offsetHeight)) + 'px';
        }

        function stopDrag() {
            if (draggedElement) {
                draggedElement.style.cursor = 'move';
                draggedElement = null;
            }
            isDragging = false;
            isResizing = false;
        }

        // Touch event handlers for mobile support
        function startDragTouch(e) {
            e.preventDefault();
            const touch = e.touches[0];
            const elementType = e.target.dataset.type;
            draggedElement = createElement(elementType, touch.clientX, touch.clientY);
            isDragging = true;
        }

        function handleCanvasTouch(e) {
            e.preventDefault();
            // Deselect all elements
            document.querySelectorAll('.element').forEach(el => el.classList.remove('selected'));
            selectedElement = null;
            updatePropertiesPanel();
        }

        function handleTouchMove(e) {
            e.preventDefault();
            if (!isDragging || !draggedElement) return;

            const touch = e.touches[0];
            const canvasRect = canvas.getBoundingClientRect();
            const x = touch.clientX - canvasRect.left - dragOffset.x;
            const y = touch.clientY - canvasRect.top - dragOffset.y;

            draggedElement.style.left = Math.max(0, Math.min(x, canvasRect.width - draggedElement.offsetWidth)) + 'px';
            draggedElement.style.top = Math.max(0, Math.min(y, canvasRect.height - draggedElement.offsetHeight)) + 'px';
        }

        function handleCanvasClick(e) {
            // Deselect all elements
            document.querySelectorAll('.element').forEach(el => el.classList.remove('selected'));
            selectedElement = null;
            updatePropertiesPanel();
        }

        function createElement(type, x, y) {
            elementCounter++;
            const element = document.createElement('div');
            element.className = `element ${type}-element`;
            element.id = `element-${elementCounter}`;
            element.dataset.type = type;
            element.dataset.id = elementCounter;

            // Position element
            const canvasRect = canvas.getBoundingClientRect();
            element.style.left = (x - canvasRect.left - 50) + 'px';
            element.style.top = (y - canvasRect.top - 15) + 'px';

            // Set default content and size based on type
            switch (type) {
                case 'text':
                    element.textContent = 'Sample Text';
                    element.style.width = '200px';
                    element.style.height = '50px';
                    break;
                case 'image':
                    element.textContent = '📷 Image';
                    element.style.width = '150px';
                    element.style.height = '100px';
                    break;
                case 'rectangle':
                    element.style.width = '100px';
                    element.style.height = '80px';
                    element.style.backgroundColor = '#e0e0e0';
                    break;
                case 'circle':
                    element.style.width = '80px';
                    element.style.height = '80px';
                    element.style.borderRadius = '50%';
                    element.style.backgroundColor = '#e0e0e0';
                    break;
                case 'time':
                    element.textContent = '12:34 PM';
                    element.style.width = '120px';
                    element.style.height = '40px';
                    break;
                case 'date':
                    element.textContent = 'Dec 29, 2023';
                    element.style.width = '140px';
                    element.style.height = '40px';
                    break;
            }

            // Add resize handle
            const resizeHandle = document.createElement('div');
            resizeHandle.className = 'resize-handle';
            element.appendChild(resizeHandle);

            // Add event listeners
            element.addEventListener('mousedown', (e) => {
                if (e.target.classList.contains('resize-handle')) {
                    isResizing = true;
                } else {
                    selectElement(element, e);
                }
                e.stopPropagation();
            });

            canvas.appendChild(element);
            elements.push({
                id: elementCounter,
                type: type,
                element: element,
                properties: getDefaultProperties(type)
            });

            return element;
        }

        function selectElement(element, e) {
            // Deselect all
            document.querySelectorAll('.element').forEach(el => el.classList.remove('selected'));

            // Select this one
            element.classList.add('selected');
            selectedElement = element;

            // Calculate drag offset
            const rect = element.getBoundingClientRect();
            dragOffset.x = e.clientX - rect.left;
            dragOffset.y = e.clientY - rect.top;

            isDragging = true;
            updatePropertiesPanel();
        }

        function getDefaultProperties(type) {
            const defaults = {
                text: {
                    content: 'Sample Text',
                    font: 'Arial',
                    size: 24,
                    color: '#000000',
                    align: 'left'
                },
                image: {
                    src: '',
                    alt: 'Image'
                },
                rectangle: {
                    fillColor: '#e0e0e0',
                    strokeColor: '#000000',
                    strokeWidth: 1
                },
                circle: {
                    fillColor: '#e0e0e0',
                    strokeColor: '#000000',
                    strokeWidth: 1
                },
                time: {
                    format: 'HH:MM',
                    font: 'Arial',
                    size: 24,
                    color: '#000000'
                },
                date: {
                    format: 'Day, Month DD, YYYY',
                    font: 'Arial',
                    size: 24,
                    color: '#000000'
                }
            };
            return defaults[type] || {};
        }

        function updatePropertiesPanel() {
            const container = document.getElementById('properties-container');

            if (!selectedElement) {
                container.innerHTML = '<p>Select an element to edit properties</p>';
                return;
            }

            const elementData = elements.find(el => el.id == selectedElement.dataset.id);
            if (!elementData) return;

            const properties = elementData.properties;
            let html = `<h4>${elementData.type.charAt(0).toUpperCase() + elementData.type.slice(1)} Properties</h4>`;

            // Position properties (common to all)
            html += `
                <div class="property-group">
                    <label>Position X:</label>
                    <input type="number" id="prop-x" value="${parseInt(selectedElement.style.left)}" onchange="updatePosition()">
                </div>
                <div class="property-group">
                    <label>Position Y:</label>
                    <input type="number" id="prop-y" value="${parseInt(selectedElement.style.top)}" onchange="updatePosition()">
                </div>
                <div class="property-group">
                    <label>Width:</label>
                    <input type="number" id="prop-width" value="${parseInt(selectedElement.style.width)}" onchange="updateSize()">
                </div>
                <div class="property-group">
                    <label>Height:</label>
                    <input type="number" id="prop-height" value="${parseInt(selectedElement.style.height)}" onchange="updateSize()">
                </div>
            `;

            // Type-specific properties
            switch (elementData.type) {
                case 'text':
                    html += `
                        <div class="property-group">
                            <label>Text Content:</label>
                            <textarea id="prop-content" onchange="updateText()">${properties.content || ''}</textarea>
                        </div>
                        <div class="property-group">
                            <label>Font:</label>
                            <select id="prop-font" onchange="updateText()">
                                <option value="Arial" ${properties.font === 'Arial' ? 'selected' : ''}>Arial</option>
                                <option value="Times" ${properties.font === 'Times' ? 'selected' : ''}>Times</option>
                                <option value="Courier" ${properties.font === 'Courier' ? 'selected' : ''}>Courier</option>
                            </select>
                        </div>
                        <div class="property-group">
                            <label>Font Size:</label>
                            <input type="number" id="prop-size" value="${properties.size || 24}" onchange="updateText()">
                        </div>
                        <div class="property-group">
                            <label>Text Color:</label>
                            <div class="color-picker">
                                <div class="color-swatch" style="background: #000000;" onclick="setTextColor('#000000')"></div>
                                <div class="color-swatch" style="background: #ffffff;" onclick="setTextColor('#ffffff')"></div>
                                <div class="color-swatch" style="background: #ff0000;" onclick="setTextColor('#ff0000')"></div>
                                <div class="color-swatch" style="background: #00ff00;" onclick="setTextColor('#00ff00')"></div>
                                <div class="color-swatch" style="background: #0000ff;" onclick="setTextColor('#0000ff')"></div>
                                <div class="color-swatch" style="background: #ffff00;" onclick="setTextColor('#ffff00')"></div>
                            </div>
                        </div>
                    `;
                    break;

                case 'image':
                    html += `
                        <div class="property-group">
                            <label>Image Source:</label>
                            <input type="text" id="prop-src" value="${properties.src || ''}" onchange="updateImage()">
                        </div>
                        <div class="property-group">
                            <label>Alt Text:</label>
                            <input type="text" id="prop-alt" value="${properties.alt || ''}" onchange="updateImage()">
                        </div>
                    `;
                    break;

                case 'rectangle':
                case 'circle':
                    html += `
                        <div class="property-group">
                            <label>Fill Color:</label>
                            <div class="color-picker">
                                <div class="color-swatch" style="background: #e0e0e0;" onclick="setFillColor('#e0e0e0')"></div>
                                <div class="color-swatch" style="background: #ffffff;" onclick="setFillColor('#ffffff')"></div>
                                <div class="color-swatch" style="background: #f0f0f0;" onclick="setFillColor('#f0f0f0')"></div>
                            </div>
                        </div>
                    `;
                    break;
            }

            container.innerHTML = html;
        }

        function updatePosition() {
            if (!selectedElement) return;
            const x = document.getElementById('prop-x').value;
            const y = document.getElementById('prop-y').value;
            selectedElement.style.left = x + 'px';
            selectedElement.style.top = y + 'px';
        }

        function updateSize() {
            if (!selectedElement) return;
            const width = document.getElementById('prop-width').value;
            const height = document.getElementById('prop-height').value;
            selectedElement.style.width = width + 'px';
            selectedElement.style.height = height + 'px';
        }

        function updateText() {
            if (!selectedElement) return;
            const content = document.getElementById('prop-content').value;
            const font = document.getElementById('prop-font').value;
            const size = document.getElementById('prop-size').value;

            selectedElement.textContent = content;
            selectedElement.style.fontFamily = font;
            selectedElement.style.fontSize = size + 'px';

            // Update element data
            const elementData = elements.find(el => el.id == selectedElement.dataset.id);
            if (elementData) {
                elementData.properties.content = content;
                elementData.properties.font = font;
                elementData.properties.size = parseInt(size);
            }
        }

        function setTextColor(color) {
            if (!selectedElement) return;
            selectedElement.style.color = color;

            const elementData = elements.find(el => el.id == selectedElement.dataset.id);
            if (elementData) {
                elementData.properties.color = color;
            }
        }

        function updateImage() {
            const elementData = elements.find(el => el.id == selectedElement.dataset.id);
            if (elementData) {
                elementData.properties.src = document.getElementById('prop-src').value;
                elementData.properties.alt = document.getElementById('prop-alt').value;
            }
        }

        function setFillColor(color) {
            if (!selectedElement) return;
            selectedElement.style.backgroundColor = color;

            const elementData = elements.find(el => el.id == selectedElement.dataset.id);
            if (elementData) {
                elementData.properties.fillColor = color;
            }
        }

        function showTemplatesModal() {
            document.getElementById('templates-modal').style.display = 'flex';
        }

        function closeTemplatesModal() {
            document.getElementById('templates-modal').style.display = 'none';
        }

        function handleTemplateSelect(e) {
            const template = e.target.closest('.template-item')?.dataset.template;
            if (template) {
                loadTemplate(template);
                closeTemplatesModal();
            }
        }

        function loadTemplate(template) {
            // Clear current canvas
            clearCanvas();

            // Check if it's a built-in template
            const builtInTemplates = {
                'restaurant': {
                    overlays: [
                        { type: 'text', content: 'Welcome to Our Restaurant', font: 'Arial', size: 48, color: '#FFD700', position: [50, 100], size: [980, 80] },
                        { type: 'text', content: 'Daily Specials', font: 'Arial', size: 36, color: '#FFFFFF', position: [50, 250], size: [980, 60] },
                        { type: 'text', content: 'Grilled Salmon with seasonal vegetables', font: 'Arial', size: 28, color: '#FFFFFF', position: [80, 350], size: [920, 50] },
                        { type: 'text', content: '$24.99', font: 'Arial', size: 32, color: '#FFD700', position: [80, 420], size: [200, 50] },
                        { type: 'time', format: 'HH:MM', font: 'Arial', size: 36, color: '#FFD700', position: [800, 50], size: [200, 50] }
                    ]
                },
                'office': {
                    overlays: [
                        { type: 'text', content: 'Company Directory', font: 'Arial', size: 42, color: '#2D3748', position: [50, 80], size: [980, 70] },
                        { type: 'text', content: 'Welcome to Our Office', font: 'Arial', size: 28, color: '#4A5568', position: [50, 220], size: [980, 50] },
                        { type: 'text', content: 'John Smith\\nCEO & Founder\\njohn@company.com', font: 'Arial', size: 22, color: '#2D3748', position: [80, 320], size: [400, 120] },
                        { type: 'date', format: 'Day, Month DD, YYYY', font: 'Arial', size: 24, color: '#2D3748', position: [50, 560], size: [300, 40] }
                    ]
                },
                'school': {
                    overlays: [
                        { type: 'text', content: 'School Schedule', font: 'Arial', size: 42, color: '#2D3748', position: [50, 80], size: [980, 70] },
                        { type: 'text', content: 'Today\'s Classes', font: 'Arial', size: 32, color: '#4A5568', position: [50, 200], size: [980, 60] },
                        { type: 'text', content: 'Math - Room 101\\nScience - Room 203\\nEnglish - Room 305', font: 'Arial', size: 26, color: '#2D3748', position: [80, 300], size: [600, 150] },
                        { type: 'time', format: 'HH:MM', font: 'Arial', size: 36, color: '#2D3748', position: [800, 50], size: [200, 50] }
                    ]
                },
                'retail': {
                    overlays: [
                        { type: 'text', content: 'Special Offer', font: 'Arial', size: 48, color: '#FFD700', position: [50, 100], size: [980, 80] },
                        { type: 'text', content: '50% Off All Items', font: 'Arial', size: 36, color: '#FFFFFF', position: [50, 250], size: [980, 60] },
                        { type: 'rectangle', fillColor: '#FFD700', position: [100, 350], size: [200, 100] },
                        { type: 'text', content: 'Limited Time!', font: 'Arial', size: 24, color: '#000000', position: [120, 380], size: [160, 40] }
                    ]
                },
                'blank': {
                    overlays: []
                }
            };

            if (builtInTemplates[template]) {
                // Load built-in template
                const templateData = builtInTemplates[template];
                templateData.overlays.forEach(overlay => {
                    const element = createElementFromOverlay(overlay);
                    if (element) {
                        canvas.appendChild(element);
                    }
                });
                showNotification(`Loaded ${template} template`);
            } else {
                // Load custom template from server
                fetch(`/api/templates/${template}.json`)
                    .then(response => response.json())
                    .then(templateData => {
                        if (templateData.overlays) {
                            templateData.overlays.forEach(overlay => {
                                const element = createElementFromOverlay(overlay);
                                if (element) {
                                    canvas.appendChild(element);
                                }
                            });
                        }
                        showNotification(`Loaded custom template: ${template}`);
                    })
                    .catch(error => {
                        showNotification('Error loading template', 'error');
                    });
            }
        }

        function createElementFromOverlay(overlay) {
            // Create element from overlay data
            const type = overlay.type;
            const x = overlay.position[0] + 50; // Add some offset
            const y = overlay.position[1] + 50;

            const element = createElement(type, x, y);

            // Apply overlay properties
            const elementData = elements.find(el => el.id == element.dataset.id);
            if (elementData && overlay) {
                elementData.properties = { ...elementData.properties, ...overlay };
                elementData.properties.position = overlay.position;
                elementData.properties.size = overlay.size;

                // Apply visual properties
                if (overlay.content) {
                    element.textContent = overlay.content.replace(/\\\\n/g, '\\n');
                }
                if (overlay.font) {
                    element.style.fontFamily = overlay.font;
                }
                if (overlay.size) {
                    element.style.fontSize = overlay.size + 'px';
                }
                if (overlay.color) {
                    element.style.color = overlay.color;
                }
                if (overlay.fillColor) {
                    element.style.backgroundColor = overlay.fillColor;
                }

                // Set position and size
                element.style.left = overlay.position[0] + 'px';
                element.style.top = overlay.position[1] + 'px';
                element.style.width = overlay.size[0] + 'px';
                element.style.height = overlay.size[1] + 'px';
            }

            return element;
        }

        function saveLMS() {
            const lmsData = generateLMS();
            const lmsJson = JSON.stringify(lmsData, null, 2);

            // Send to server (would be implemented in the Python server)
            fetch('/api/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: lmsJson
            })
            .then(response => response.json())
            .then(data => {
                showNotification('LMS file saved successfully!');
            })
            .catch(error => {
                showNotification('Error saving LMS file', 'error');
            });
        }

        function previewLMS() {
            const lmsData = generateLMS();
            // Would send to preview endpoint
            showNotification('Preview generated (would open preview window)');
        }

        function generateLMS() {
            const lms = {
                version: "1.0",
                display_size: [1080, 1920], // Portrait default
                orientation: "portrait",
                overlays: []
            };

            elements.forEach(elementData => {
                const element = elementData.element;
                const rect = element.getBoundingClientRect();
                const canvasRect = canvas.getBoundingClientRect();

                const overlay = {
                    type: elementData.type,
                    position: [
                        parseInt(element.style.left),
                        parseInt(element.style.top)
                    ],
                    size: [
                        parseInt(element.style.width),
                        parseInt(element.style.height)
                    ],
                    ...elementData.properties
                };

                lms.overlays.push(overlay);
            });

            return lms;
        }

        function clearCanvas() {
            elements.forEach(el => el.element.remove());
            elements = [];
            elementCounter = 0;
            selectedElement = null;
            updatePropertiesPanel();
        }

        function showSaveTemplateModal() {
            document.getElementById('save-template-modal').style.display = 'flex';
            // Pre-fill template name
            const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
            document.getElementById('template-name').value = `Custom Layout ${timestamp}`;
        }

        function closeSaveTemplateModal() {
            document.getElementById('save-template-modal').style.display = 'none';
            document.getElementById('template-name').value = '';
            document.getElementById('template-description').value = '';
        }

        function saveTemplate() {
            const name = document.getElementById('template-name').value.trim();
            const description = document.getElementById('template-description').value.trim();

            if (!name) {
                showNotification('Template name is required', 'error');
                return;
            }

            const templateData = {
                name: name,
                description: description,
                display_size: [1080, 1920],
                orientation: "portrait",
                overlays: []
            };

            // Convert elements to overlays
            elements.forEach(elementData => {
                const element = elementData.element;
                const overlay = {
                    type: elementData.type,
                    position: [
                        parseInt(element.style.left),
                        parseInt(element.style.top)
                    ],
                    size: [
                        parseInt(element.style.width),
                        parseInt(element.style.height)
                    ],
                    ...elementData.properties
                };
                templateData.overlays.push(overlay);
            });

            // Send to server
            fetch('/api/save-template', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(templateData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('Template saved successfully!');
                    closeSaveTemplateModal();
                    // Refresh templates list
                    loadTemplatesList();
                } else {
                    showNotification('Error saving template', 'error');
                }
            })
            .catch(error => {
                showNotification('Error saving template', 'error');
            });
        }

        function loadTemplatesList() {
            fetch('/api/templates')
                .then(response => response.json())
                .then(templates => {
                    updateTemplatesModal(templates);
                })
                .catch(error => {
                    console.error('Error loading templates:', error);
                });
        }

        function updateTemplatesModal(templates) {
            const grid = document.getElementById('templates-grid');

            // Keep built-in templates
            const builtInTemplates = [
                { name: 'restaurant', icon: '🍽️', label: 'Restaurant Menu' },
                { name: 'office', icon: '🏢', label: 'Office Directory' },
                { name: 'school', icon: '🎓', label: 'School Schedule' },
                { name: 'retail', icon: '🛍️', label: 'Retail Display' },
                { name: 'blank', icon: '📄', label: 'Blank Canvas' }
            ];

            let html = '';

            // Add built-in templates
            builtInTemplates.forEach(template => {
                html += `
                    <div class="template-item" data-template="${template.name}">
                        <div>${template.icon}</div>
                        <div>${template.label}</div>
                    </div>
                `;
            });

            // Add user-created templates
            if (templates && templates.length > 0) {
                html += '<div style="width: 100%; text-align: center; margin: 1rem 0; color: #666; font-size: 0.9rem;">Custom Templates</div>';
                templates.forEach(template => {
                    html += `
                        <div class="template-item" data-template="${template.name}">
                            <div>🎨</div>
                            <div>${template.name}</div>
                        </div>
                    `;
                });
            }

            grid.innerHTML = html;
        }

        function showNotification(message, type = 'success') {
            const notification = document.createElement('div');
            notification.className = 'notification';
            notification.textContent = message;

            if (type === 'error') {
                notification.style.background = '#f44336';
            }

            document.body.appendChild(notification);

            setTimeout(() => {
                notification.remove();
            }, 3000);
        }

        // Initialize with a blank canvas and load templates
        showNotification('314Sign LMS Editor Ready');
        loadTemplatesList();
    </script>
</body>
</html>"""

    def serve_templates(self):
        """Serve available LMS templates"""
        try:
            templates = []
            if self.templates_dir.exists():
                for template_file in self.templates_dir.glob("*.json"):
                    try:
                        with open(template_file, 'r') as f:
                            template = json.load(f)
                            templates.append({
                                'name': template_file.stem,
                                'description': template.get('description', ''),
                                'preview': template.get('preview', '')
                            })
                    except:
                        pass

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(templates).encode())

        except Exception as e:
            self.send_error(500, str(e))

    def serve_fonts(self):
        """Serve available fonts"""
        fonts = [
            'Arial', 'Times New Roman', 'Courier New',
            'Helvetica', 'Georgia', 'Verdana'
        ]
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(fonts).encode())

    def serve_backgrounds(self):
        """Serve available background images"""
        backgrounds = []
        bg_dir = Path('/var/lib/314sign/backgrounds')
        if bg_dir.exists():
            for bg_file in bg_dir.glob("*"):
                if bg_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                    backgrounds.append({
                        'name': bg_file.name,
                        'path': str(bg_file),
                        'size': bg_file.stat().st_size
                    })

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(backgrounds).encode())

    def serve_static_file(self, path):
        """Serve static files (CSS, JS, images)"""
        # This would serve static assets
        self.send_error(404)

    def save_lms_content(self):
        """Save LMS content from the editor"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            lms_data = json.loads(post_data.decode())

            # Generate filename
            timestamp = int(time.time())
            filename = f"editor-created-{timestamp}.lms"
            filepath = self.output_dir / filename

            # Save LMS file
            with open(filepath, 'w') as f:
                json.dump(lms_data, f, indent=2)

            response = {
                'success': True,
                'filename': filename,
                'path': str(filepath)
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            self.send_error(500, f"Error saving LMS: {str(e)}")

    def generate_preview(self):
        """Generate preview of LMS content"""
        # This would render the LMS and return preview data
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'preview': 'Not implemented yet'}).encode())

    def save_template(self):
        """Save template content from the editor"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            template_data = json.loads(post_data.decode())

            # Validate required fields
            if not template_data.get('name'):
                self.send_error(400, "Template name is required")
                return

            # Sanitize filename (remove special characters)
            name = template_data['name']
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_').lower()

            # Create filename
            filename = f"{safe_name}.json"
            filepath = self.templates_dir / filename

            # Add metadata
            template_data['created_at'] = int(time.time())
            template_data['version'] = "1.0"

            # Save template file
            with open(filepath, 'w') as f:
                json.dump(template_data, f, indent=2)

            response = {
                'success': True,
                'filename': filename,
                'path': str(filepath),
                'name': template_data['name']
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            self.send_error(500, f"Error saving template: {str(e)}")

class LMSWebEditor:
    """
    Web-based LMS content creation interface
    Allows visual drag-and-drop content creation
    """

    def __init__(self, host='0.0.0.0', port=8080, templates_dir=None, output_dir=None):
        self.host = host
        self.port = port
        self.templates_dir = templates_dir or "/opt/314sign/templates"
        self.output_dir = output_dir or "/home/pi/lms"

        # Create directories
        Path(self.templates_dir).mkdir(exist_ok=True)
        Path(self.output_dir).mkdir(exist_ok=True)

    def start(self):
        """Start the web server"""
        server_address = (self.host, self.port)

        # Create custom handler class with parameters
        def handler_class(*args, **kwargs):
            return LMSEditorWebServer(*args, templates_dir=self.templates_dir,
                                    output_dir=self.output_dir, **kwargs)

        httpd = HTTPServer(server_address, handler_class)

        print(f"🚀 314Sign LMS Web Editor started at http://{self.host}:{self.port}")
        print(f"📁 Templates: {self.templates_dir}")
        print(f"💾 Output: {self.output_dir}")
        print("Press Ctrl+C to stop")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down web editor...")
            httpd.shutdown()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='314Sign LMS Web Content Editor')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    parser.add_argument('--templates', help='Templates directory')
    parser.add_argument('--output', help='Output LMS directory')

    args = parser.parse_args()

    editor = LMSWebEditor(
        host=args.host,
        port=args.port,
        templates_dir=args.templates,
        output_dir=args.output
    )

    editor.start()

if __name__ == "__main__":
    main()