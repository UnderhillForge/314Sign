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

        @media (max-width: 768px) {
            .container {
                flex-direction: column;
            }
            .sidebar {
                width: 100%;
                height: 200px;
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
            // Element palette drag and drop
            document.querySelectorAll('.element-item').forEach(item => {
                item.addEventListener('mousedown', startDrag);
            });

            // Canvas interactions
            canvas.addEventListener('mousedown', handleCanvasClick);
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', stopDrag);

            // Toolbar buttons
            document.getElementById('load-template').addEventListener('click', showTemplatesModal);
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

            // Load template elements (simplified - would load from server)
            switch (template) {
                case 'restaurant':
                    createElement('text', 100, 100);
                    createElement('text', 100, 200);
                    createElement('time', 800, 50);
                    break;
                case 'office':
                    createElement('text', 100, 100);
                    createElement('text', 100, 150);
                    createElement('date', 800, 50);
                    break;
                case 'school':
                    createElement('text', 100, 100);
                    createElement('text', 100, 160);
                    createElement('time', 800, 50);
                    break;
                case 'retail':
                    createElement('text', 100, 100);
                    createElement('image', 100, 200);
                    createElement('rectangle', 400, 100);
                    break;
            }

            showNotification(`Loaded ${template} template`);
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

        // Initialize with a blank canvas
        showNotification('314Sign LMS Editor Ready');
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