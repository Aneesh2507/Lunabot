#!/usr/bin/env python3
"""
LunarBot Top-View Terrain Analysis & Navigation
Specialized web interface for lunar surface navigation
"""

from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import base64
import json
import threading
import time
import numpy as np
import random
import io
from PIL import Image, ImageDraw, ImageFilter
import math

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lunarbot_topview_2024'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

class LunarBotTopView:
    def __init__(self):
        self.robot_position = {'x': 0, 'y': 0}
        self.robot_angle = 0
        self.navigation_path = []
        self.terrain_map = None
        self.obstacles = []
        self.safe_paths = []
        
    def analyze_top_view_image(self, image_data):
        """Analyze top-view lunar terrain image"""
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data.split(',')[1])
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to grayscale for analysis
            gray_image = image.convert('L')
            img_array = np.array(gray_image)
            
            # Analyze terrain features
            analysis = self.detect_terrain_features(img_array)
            
            # Generate navigation path
            path = self.generate_navigation_path(img_array, analysis)
            
            return {
                'analysis': analysis,
                'navigation_path': path,
                'recommendations': self.get_navigation_recommendations(analysis)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def detect_terrain_features(self, img_array):
        """Detect craters, hills, and safe areas in top-view image"""
        height, width = img_array.shape
        
        # Detect dark areas (craters/potholes)
        dark_threshold = np.mean(img_array) - np.std(img_array)
        crater_mask = img_array < dark_threshold
        
        # Detect bright areas (hills/elevations)
        bright_threshold = np.mean(img_array) + np.std(img_array)
        hill_mask = img_array > bright_threshold
        
        # Find crater centers
        craters = self.find_circular_features(crater_mask, 'crater')
        
        # Find hill centers
        hills = self.find_circular_features(hill_mask, 'hill')
        
        # Find safe areas (medium brightness, low variance)
        safe_areas = self.find_safe_areas(img_array)
        
        return {
            'craters': craters,
            'hills': hills,
            'safe_areas': safe_areas,
            'terrain_complexity': self.calculate_terrain_complexity(img_array),
            'image_size': {'width': width, 'height': height}
        }
    
    def find_circular_features(self, mask, feature_type):
        """Find circular features in binary mask"""
        features = []
        height, width = mask.shape
        
        # Simple circular feature detection
        for y in range(20, height - 20, 15):
            for x in range(20, width - 20, 15):
                if mask[y, x]:
                    # Check if this is a circular feature
                    radius = self.estimate_feature_radius(mask, x, y)
                    if radius > 5:  # Minimum feature size
                        features.append({
                            'x': x,
                            'y': y,
                            'radius': radius,
                            'type': feature_type
                        })
        
        return features
    
    def estimate_feature_radius(self, mask, center_x, center_y):
        """Estimate radius of circular feature"""
        max_radius = 0
        height, width = mask.shape
        
        for r in range(1, min(50, min(center_x, center_y, width - center_x, height - center_y))):
            # Check if circle at this radius is mostly filled
            filled_pixels = 0
            total_pixels = 0
            
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if dx*dx + dy*dy <= r*r:
                        y, x = center_y + dy, center_x + dx
                        if 0 <= y < height and 0 <= x < width:
                            total_pixels += 1
                            if mask[y, x]:
                                filled_pixels += 1
            
            if total_pixels > 0 and filled_pixels / total_pixels > 0.6:
                max_radius = r
            else:
                break
        
        return max_radius
    
    def find_safe_areas(self, img_array):
        """Find safe areas for navigation"""
        height, width = img_array.shape
        safe_areas = []
        
        # Look for areas with medium brightness and low variance
        mean_brightness = np.mean(img_array)
        std_brightness = np.std(img_array)
        
        for y in range(30, height - 30, 20):
            for x in range(30, width - 30, 20):
                # Check local area
                local_area = img_array[y-15:y+15, x-15:x+15]
                local_mean = np.mean(local_area)
                local_std = np.std(local_area)
                
                # Safe if brightness is close to mean and low variance
                if (abs(local_mean - mean_brightness) < std_brightness * 0.5 and 
                    local_std < std_brightness * 0.7):
                    safe_areas.append({
                        'x': x,
                        'y': y,
                        'safety_score': 1.0 - (local_std / std_brightness)
                    })
        
        return safe_areas
    
    def calculate_terrain_complexity(self, img_array):
        """Calculate terrain complexity score"""
        # Use edge detection to measure complexity
        edges = self.detect_edges(img_array)
        edge_density = np.sum(edges > 128) / edges.size
        return min(100, edge_density * 200)
    
    def detect_edges(self, img_array):
        """Simple edge detection"""
        # Convert to PIL Image for edge detection
        img = Image.fromarray(img_array)
        edges = img.filter(ImageFilter.FIND_EDGES)
        return np.array(edges)
    
    def generate_navigation_path(self, img_array, analysis):
        """Generate optimal navigation path avoiding obstacles"""
        height, width = img_array.shape
        
        # Create cost map
        cost_map = np.ones((height, width)) * 100
        
        # Add high cost to craters
        for crater in analysis['craters']:
            self.add_circular_cost(cost_map, crater['x'], crater['y'], crater['radius'] * 1.5, 1000)
        
        # Add medium cost to hills
        for hill in analysis['hills']:
            self.add_circular_cost(cost_map, hill['x'], hill['y'], hill['radius'], 500)
        
        # Add low cost to safe areas
        for safe_area in analysis['safe_areas']:
            self.add_circular_cost(cost_map, safe_area['x'], safe_area['y'], 20, 10)
        
        # Generate path using simple A* algorithm
        start = (height // 2, width // 2)  # Center of image
        goal = self.find_best_goal_position(cost_map, analysis)
        
        path = self.a_star_pathfinding(cost_map, start, goal)
        
        return {
            'path_points': path,
            'start': start,
            'goal': goal,
            'total_cost': self.calculate_path_cost(path, cost_map)
        }
    
    def add_circular_cost(self, cost_map, center_x, center_y, radius, cost):
        """Add circular cost area to cost map"""
        height, width = cost_map.shape
        for dy in range(-int(radius), int(radius) + 1):
            for dx in range(-int(radius), int(radius) + 1):
                if dx*dx + dy*dy <= radius*radius:
                    y, x = center_y + dy, center_x + dx
                    if 0 <= y < height and 0 <= x < width:
                        cost_map[y, x] = min(cost_map[y, x], cost)
    
    def find_best_goal_position(self, cost_map, analysis):
        """Find best goal position based on safe areas"""
        if analysis['safe_areas']:
            # Choose safest area
            best_area = max(analysis['safe_areas'], key=lambda x: x['safety_score'])
            return (best_area['y'], best_area['x'])
        else:
            # Default to edge of image
            height, width = cost_map.shape
            return (height - 50, width - 50)
    
    def a_star_pathfinding(self, cost_map, start, goal):
        """Simple A* pathfinding algorithm"""
        height, width = cost_map.shape
        
        # Simple pathfinding - move towards goal avoiding high cost areas
        path = [start]
        current = start
        
        while current != goal:
            # Find next best move
            next_move = self.find_next_move(cost_map, current, goal)
            if next_move is None:
                break
            path.append(next_move)
            current = next_move
            
            # Prevent infinite loops
            if len(path) > 100:
                break
        
        return path
    
    def find_next_move(self, cost_map, current, goal):
        """Find next move towards goal"""
        y, x = current
        goal_y, goal_x = goal
        
        # Calculate direction to goal
        dy = 1 if goal_y > y else -1 if goal_y < y else 0
        dx = 1 if goal_x > x else -1 if goal_x < x else 0
        
        # Try moves in order of preference
        moves = [
            (y + dy, x + dx),  # Direct towards goal
            (y + dy, x),       # Move vertically
            (y, x + dx),       # Move horizontally
            (y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)  # All directions
        ]
        
        # Find best move (lowest cost)
        best_move = None
        best_cost = float('inf')
        
        for move_y, move_x in moves:
            if (0 <= move_y < cost_map.shape[0] and 
                0 <= move_x < cost_map.shape[1]):
                cost = cost_map[move_y, move_x]
                if cost < best_cost:
                    best_cost = cost
                    best_move = (move_y, move_x)
        
        return best_move
    
    def calculate_path_cost(self, path, cost_map):
        """Calculate total cost of path"""
        total_cost = 0
        for y, x in path:
            total_cost += cost_map[y, x]
        return total_cost
    
    def get_navigation_recommendations(self, analysis):
        """Get navigation recommendations based on analysis"""
        recommendations = []
        
        if len(analysis['craters']) > 5:
            recommendations.append("High crater density - proceed with extreme caution")
        elif len(analysis['craters']) > 2:
            recommendations.append("Moderate crater density - use recommended path")
        else:
            recommendations.append("Low crater density - terrain appears safe")
        
        if len(analysis['hills']) > 3:
            recommendations.append("Multiple elevation changes detected")
        
        if analysis['terrain_complexity'] > 70:
            recommendations.append("Complex terrain - slow navigation recommended")
        
        if len(analysis['safe_areas']) > 10:
            recommendations.append("Multiple safe paths available")
        
        return recommendations

# Global bot instance
lunar_bot = LunarBotTopView()

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LunarBot Top-View Navigation</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
            color: #ffffff;
            min-height: 100vh;
        }
        
        .header {
            background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        
        .main-container {
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 20px;
            padding: 20px;
            height: calc(100vh - 120px);
        }
        
        .control-panel {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        
        .control-panel h3 {
            font-size: 1.3em;
            margin-bottom: 20px;
            color: #64b5f6;
            border-bottom: 2px solid #64b5f6;
            padding-bottom: 10px;
        }
        
        .control-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .control-btn {
            padding: 15px;
            border: none;
            border-radius: 10px;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .control-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        
        .forward { background: linear-gradient(45deg, #4caf50, #66bb6a); }
        .backward { background: linear-gradient(45deg, #ff9800, #ffb74d); }
        .left { background: linear-gradient(45deg, #2196f3, #42a5f5); }
        .right { background: linear-gradient(45deg, #9c27b0, #ba68c8); }
        .emergency { background: linear-gradient(45deg, #f44336, #ef5350); }
        
        .upload-section {
            margin-top: 20px;
        }
        
        .upload-area {
            border: 2px dashed #64b5f6;
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            margin-bottom: 15px;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .upload-area:hover {
            border-color: #42a5f5;
            background: rgba(100, 181, 246, 0.1);
        }
        
        .upload-area.dragover {
            border-color: #42a5f5;
            background: rgba(100, 181, 246, 0.2);
        }
        
        .analysis-panel {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            position: relative;
        }
        
        .image-container {
            position: relative;
            width: 100%;
            height: 100%;
            border-radius: 10px;
            overflow: hidden;
            background: rgba(0, 0, 0, 0.3);
        }
        
        .terrain-image {
            width: 100%;
            height: 100%;
            object-fit: contain;
            border-radius: 10px;
        }
        
        .overlay-canvas {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
        }
        
        .analysis-results {
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(0, 0, 0, 0.8);
            padding: 15px;
            border-radius: 10px;
            max-width: 300px;
        }
        
        .recommendation {
            font-size: 1.1em;
            font-weight: bold;
            margin-bottom: 10px;
            padding: 8px;
            border-radius: 5px;
            text-align: center;
        }
        
        .safe { background: rgba(76, 175, 80, 0.3); color: #4caf50; }
        .caution { background: rgba(255, 152, 0, 0.3); color: #ff9800; }
        .danger { background: rgba(244, 67, 54, 0.3); color: #f44336; }
        
        .analysis-details {
            font-size: 0.9em;
            line-height: 1.4;
        }
        
        .analysis-details div {
            margin-bottom: 5px;
            padding: 3px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .loading {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            background: rgba(0, 0, 0, 0.8);
            padding: 20px;
            border-radius: 10px;
        }
        
        .loading-spinner {
            width: 40px;
            height: 40px;
            border: 4px solid rgba(100, 181, 246, 0.3);
            border-top: 4px solid #64b5f6;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .robot-status {
            margin-top: 20px;
            padding: 15px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
        }
        
        .status-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
        }
        
        .status-label {
            opacity: 0.8;
        }
        
        .status-value {
            font-weight: bold;
            color: #64b5f6;
        }
        
        @media (max-width: 768px) {
            .main-container {
                grid-template-columns: 1fr;
                height: auto;
            }
            
            .control-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌙 LunarBot Top-View Navigation</h1>
        <p>Upload lunar surface images for intelligent path planning</p>
    </div>
    
    <div class="main-container">
        <!-- Control Panel -->
        <div class="control-panel">
            <h3>🎮 Robot Control</h3>
            
            <div class="control-grid">
                <button class="control-btn forward" onclick="moveRobot('forward')">↑ Forward</button>
                <button class="control-btn backward" onclick="moveRobot('backward')">↓ Backward</button>
                <button class="control-btn left" onclick="moveRobot('left')">← Left</button>
                <button class="control-btn right" onclick="moveRobot('right')">→ Right</button>
            </div>
            
            <button class="control-btn emergency" onclick="emergencyStop()" style="width: 100%; margin-bottom: 20px;">
                🚨 Emergency Stop
            </button>
            
            <div class="upload-section">
                <h4 style="color: #64b5f6; margin-bottom: 10px;">📷 Upload Terrain Image</h4>
                <div class="upload-area" id="upload-area" onclick="document.getElementById('image-upload').click()">
                    <div style="font-size: 2em; margin-bottom: 10px;">📷</div>
                    <div>Click to upload</div>
                    <div style="font-size: 0.8em; opacity: 0.7; margin-top: 5px;">Top-view lunar surface</div>
                </div>
                <input type="file" id="image-upload" accept="image/*" style="display: none;" onchange="handleImageUpload(event)">
            </div>
            
            <div class="robot-status">
                <h4 style="color: #64b5f6; margin-bottom: 10px;">Robot Status</h4>
                <div class="status-item">
                    <span class="status-label">Position:</span>
                    <span class="status-value" id="robot-position">(0, 0)</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Angle:</span>
                    <span class="status-value" id="robot-angle">0°</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Status:</span>
                    <span class="status-value" id="robot-status">Idle</span>
                </div>
            </div>
        </div>
        
        <!-- Analysis Panel -->
        <div class="analysis-panel">
            <div class="image-container" id="image-container">
                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); opacity: 0.5; text-align: center;">
                    <div style="font-size: 3em; margin-bottom: 20px;">🌙</div>
                    <div style="font-size: 1.2em;">Upload a top-view lunar surface image</div>
                    <div style="font-size: 0.9em; opacity: 0.7; margin-top: 10px;">The system will analyze craters, hills, and safe paths</div>
                </div>
                <img id="terrain-image" class="terrain-image" style="display: none;">
                <canvas id="overlay-canvas" class="overlay-canvas"></canvas>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        let currentAnalysis = null;
        let robotPosition = {x: 0, y: 0};
        let robotAngle = 0;
        
        // Socket event listeners
        socket.on('connect', () => {
            console.log('Connected to LunarBot server');
        });
        
        // Robot control functions
        function moveRobot(direction) {
            const commands = {
                'forward': {linear_x: 0.5, angular_z: 0},
                'backward': {linear_x: -0.5, angular_z: 0},
                'left': {linear_x: 0, angular_z: 0.5},
                'right': {linear_x: 0, angular_z: -0.5}
            };
            
            fetch('/api/robot/move', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(commands[direction])
            }).then(() => {
                updateRobotPosition(direction);
            });
        }
        
        function emergencyStop() {
            fetch('/api/robot/stop', {method: 'POST'}).then(() => {
                document.getElementById('robot-status').textContent = 'Stopped';
            });
        }
        
        function updateRobotPosition(direction) {
            const moveDistance = 10;
            const turnAngle = 15;
            
            switch(direction) {
                case 'forward':
                    robotPosition.x += moveDistance * Math.cos(robotAngle * Math.PI / 180);
                    robotPosition.y += moveDistance * Math.sin(robotAngle * Math.PI / 180);
                    break;
                case 'backward':
                    robotPosition.x -= moveDistance * Math.cos(robotAngle * Math.PI / 180);
                    robotPosition.y -= moveDistance * Math.sin(robotAngle * Math.PI / 180);
                    break;
                case 'left':
                    robotAngle += turnAngle;
                    break;
                case 'right':
                    robotAngle -= turnAngle;
                    break;
            }
            
            document.getElementById('robot-position').textContent = 
                `(${robotPosition.x.toFixed(1)}, ${robotPosition.y.toFixed(1)})`;
            document.getElementById('robot-angle').textContent = `${robotAngle.toFixed(0)}°`;
        }
        
        // Image upload and analysis
        function handleImageUpload(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                analyzeImage(e.target.result);
            };
            reader.readAsDataURL(file);
        }
        
        function analyzeImage(imageData) {
            // Show loading
            showLoading();
            
            fetch('/api/analyze-terrain', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({image: imageData})
            }).then(response => response.json()).then(data => {
                displayAnalysisResults(data, imageData);
            });
        }
        
        function showLoading() {
            const container = document.getElementById('image-container');
            container.innerHTML = `
                <div class="loading">
                    <div class="loading-spinner"></div>
                    <div>Analyzing lunar terrain...</div>
                </div>
            `;
        }
        
        function displayAnalysisResults(data, imageData) {
            const container = document.getElementById('image-container');
            
            // Display image
            const img = document.createElement('img');
            img.id = 'terrain-image';
            img.className = 'terrain-image';
            img.src = imageData;
            img.style.display = 'block';
            
            // Create overlay canvas
            const canvas = document.createElement('canvas');
            canvas.id = 'overlay-canvas';
            canvas.className = 'overlay-canvas';
            
            // Create analysis results
            const results = document.createElement('div');
            results.className = 'analysis-results';
            
            const analysis = data.analysis;
            const path = data.navigation_path;
            const recommendations = data.recommendations;
            
            // Determine recommendation class
            let recClass = 'safe';
            if (analysis.craters.length > 5) recClass = 'danger';
            else if (analysis.craters.length > 2) recClass = 'caution';
            
            results.innerHTML = `
                <div class="recommendation ${recClass}">
                    ${recommendations[0] || 'Terrain analysis complete'}
                </div>
                <div class="analysis-details">
                    <div><strong>Craters:</strong> ${analysis.craters.length}</div>
                    <div><strong>Hills:</strong> ${analysis.hills.length}</div>
                    <div><strong>Safe Areas:</strong> ${analysis.safe_areas.length}</div>
                    <div><strong>Complexity:</strong> ${analysis.terrain_complexity.toFixed(1)}%</div>
                    <div><strong>Path Cost:</strong> ${path.total_cost.toFixed(1)}</div>
                </div>
            `;
            
            container.innerHTML = '';
            container.appendChild(img);
            container.appendChild(canvas);
            container.appendChild(results);
            
            // Draw overlay
            img.onload = () => {
                drawOverlay(canvas, img, analysis, path);
            };
            
            currentAnalysis = data;
        }
        
        function drawOverlay(canvas, img, analysis, path) {
            const ctx = canvas.getContext('2d');
            canvas.width = img.offsetWidth;
            canvas.height = img.offsetHeight;
            
            const scaleX = canvas.width / analysis.image_size.width;
            const scaleY = canvas.height / analysis.image_size.height;
            
            // Draw craters (red circles)
            ctx.strokeStyle = '#f44336';
            ctx.lineWidth = 3;
            analysis.craters.forEach(crater => {
                ctx.beginPath();
                ctx.arc(crater.x * scaleX, crater.y * scaleY, crater.radius * scaleX, 0, 2 * Math.PI);
                ctx.stroke();
            });
            
            // Draw hills (orange circles)
            ctx.strokeStyle = '#ff9800';
            ctx.lineWidth = 2;
            analysis.hills.forEach(hill => {
                ctx.beginPath();
                ctx.arc(hill.x * scaleX, hill.y * scaleY, hill.radius * scaleX, 0, 2 * Math.PI);
                ctx.stroke();
            });
            
            // Draw safe areas (green circles)
            ctx.strokeStyle = '#4caf50';
            ctx.lineWidth = 1;
            analysis.safe_areas.forEach(area => {
                ctx.beginPath();
                ctx.arc(area.x * scaleX, area.y * scaleY, 10 * scaleX, 0, 2 * Math.PI);
                ctx.stroke();
            });
            
            // Draw navigation path (blue line)
            if (path.path_points.length > 1) {
                ctx.strokeStyle = '#2196f3';
                ctx.lineWidth = 4;
                ctx.beginPath();
                path.path_points.forEach((point, index) => {
                    const x = point[1] * scaleX;
                    const y = point[0] * scaleY;
                    if (index === 0) {
                        ctx.moveTo(x, y);
                    } else {
                        ctx.lineTo(x, y);
                    }
                });
                ctx.stroke();
                
                // Draw start and goal points
                ctx.fillStyle = '#4caf50';
                ctx.beginPath();
                ctx.arc(path.start[1] * scaleX, path.start[0] * scaleY, 8, 0, 2 * Math.PI);
                ctx.fill();
                
                ctx.fillStyle = '#f44336';
                ctx.beginPath();
                ctx.arc(path.goal[1] * scaleX, path.goal[0] * scaleY, 8, 0, 2 * Math.PI);
                ctx.fill();
            }
        }
        
        // Drag and drop functionality
        const uploadArea = document.getElementById('upload-area');
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const file = files[0];
                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        analyzeImage(e.target.result);
                    };
                    reader.readAsDataURL(file);
                }
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/api/robot/move', methods=['POST'])
def move_robot():
    data = request.json
    linear_x = data.get('linear_x', 0.0)
    angular_z = data.get('angular_z', 0.0)
    
    # Update robot position simulation
    lunar_bot.robot_angle += angular_z * 10
    lunar_bot.robot_position['x'] += linear_x * 10 * np.cos(np.radians(lunar_bot.robot_angle))
    lunar_bot.robot_position['y'] += linear_x * 10 * np.sin(np.radians(lunar_bot.robot_angle))
    
    return jsonify({'status': 'success'})

@app.route('/api/robot/stop', methods=['POST'])
def stop_robot():
    return jsonify({'status': 'success'})

@app.route('/api/analyze-terrain', methods=['POST'])
def analyze_terrain():
    data = request.json
    image_data = data.get('image', '')
    
    analysis = lunar_bot.analyze_top_view_image(image_data)
    return jsonify(analysis)

if __name__ == '__main__':
    print("🌙 Starting LunarBot Top-View Navigation System...")
    print("Access dashboard at: http://localhost:5000")
    print("Features: Top-view terrain analysis, crater detection, path planning")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
