#!/usr/bin/env python3
"""
LunarBot Web Interface Backend - Demo Version
Flask application with WebSocket support for robot control simulation
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import cv2
import base64
import json
import threading
import time
import numpy as np
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lunarbot_secret_2024'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

class SimulatedRobot:
    def __init__(self):
        # Robot state
        self.robot_status = {
            'connected': True,
            'battery_level': 85,
            'current_speed': 0.0,
            'position': {'x': 0.0, 'y': 0.0, 'theta': 0.0},
            'navigation_status': 'idle',
            'last_update': time.time()
        }

        # Telemetry data
        self.telemetry = {
            'lidar_data': [],
            'camera_stream': None,
            'segmentation_stream': None,
            'map_data': None
        }
        
        # Generate simulated camera feed
        self.camera_feed_active = True
        self.camera_thread = threading.Thread(target=self.generate_camera_feed, daemon=True)
        self.camera_thread.start()
        
        # Generate simulated LiDAR data
        self.lidar_thread = threading.Thread(target=self.generate_lidar_data, daemon=True)
        self.lidar_thread.start()

    def generate_camera_feed(self):
        """Generate simulated camera feed"""
        while self.camera_feed_active:
            try:
                # Create a simulated lunar terrain image
                img = np.random.randint(50, 150, (480, 640, 3), dtype=np.uint8)
                
                # Add some lunar-like features
                # Add rocks (dark spots)
                for _ in range(random.randint(5, 15)):
                    x, y = random.randint(50, 590), random.randint(50, 430)
                    cv2.circle(img, (x, y), random.randint(10, 30), (30, 30, 30), -1)
                
                # Add craters (dark circles)
                for _ in range(random.randint(2, 5)):
                    x, y = random.randint(100, 540), random.randint(100, 380)
                    cv2.circle(img, (x, y), random.randint(20, 50), (20, 20, 20), -1)
                
                # Add safe paths (lighter areas)
                for _ in range(random.randint(3, 8)):
                    x, y = random.randint(50, 590), random.randint(50, 430)
                    cv2.circle(img, (x, y), random.randint(15, 40), (180, 180, 180), -1)
                
                # Encode to base64 for web transmission
                _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 70])
                img_base64 = base64.b64encode(buffer).decode('utf-8')
                
                self.telemetry['camera_stream'] = img_base64
                
                # Emit to web clients
                socketio.emit('camera_frame', {
                    'image': img_base64,
                    'timestamp': time.time()
                })
                
                time.sleep(0.1)  # 10 FPS
                
            except Exception as e:
                print(f"Camera feed error: {str(e)}")
                time.sleep(1)

    def generate_lidar_data(self):
        """Generate simulated LiDAR data"""
        while True:
            try:
                # Generate 360 points around the robot
                lidar_points = []
                for i in range(360):
                    angle = i * np.pi / 180
                    # Simulate obstacles at various distances
                    if random.random() < 0.1:  # 10% chance of obstacle
                        range_val = random.uniform(0.5, 3.0)
                    else:
                        range_val = random.uniform(3.0, 10.0)
                    
                    x = range_val * np.cos(angle)
                    y = range_val * np.sin(angle)
                    lidar_points.append({'x': float(x), 'y': float(y), 'range': float(range_val)})
                
                self.telemetry['lidar_data'] = lidar_points
                
                # Emit to web clients
                socketio.emit('lidar_data', {
                    'points': lidar_points,
                    'timestamp': time.time()
                })
                
                time.sleep(0.2)  # 5 Hz
                
            except Exception as e:
                print(f"LiDAR data error: {str(e)}")
                time.sleep(1)

    def send_velocity_command(self, linear_x, angular_z):
        """Send velocity command to robot"""
        self.robot_status['current_speed'] = abs(linear_x)
        
        # Simulate movement
        dt = 0.1
        self.robot_status['position']['x'] += linear_x * np.cos(self.robot_status['position']['theta']) * dt
        self.robot_status['position']['y'] += linear_x * np.sin(self.robot_status['position']['theta']) * dt
        self.robot_status['position']['theta'] += angular_z * dt
        
        print(f"Velocity command: linear={linear_x}, angular={angular_z}")
        print(f"New position: {self.robot_status['position']}")

    def send_navigation_goal(self, x, y, theta=0.0):
        """Send navigation goal to robot"""
        self.robot_status['navigation_status'] = 'navigating'
        print(f"Navigation goal sent: ({x}, {y}, {theta})")
        
        # Simulate navigation progress
        def navigate_to_goal():
            time.sleep(2)  # Simulate navigation time
            self.robot_status['position']['x'] = x
            self.robot_status['position']['y'] = y
            self.robot_status['position']['theta'] = theta
            self.robot_status['navigation_status'] = 'idle'
            print(f"Navigation completed to: ({x}, {y}, {theta})")
        
        threading.Thread(target=navigate_to_goal, daemon=True).start()

    def emergency_stop(self):
        """Emergency stop the robot"""
        self.send_velocity_command(0.0, 0.0)
        self.robot_status['navigation_status'] = 'stopped'
        print("Emergency stop activated!")

# Global robot instance
robot = SimulatedRobot()

# Flask Routes
@app.route('/')
def index():
    """Main dashboard page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LunarBot Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #1a1a1a; color: white; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 30px; }
            .dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .panel { background: #2a2a2a; padding: 20px; border-radius: 10px; }
            .controls { display: flex; gap: 10px; margin: 10px 0; }
            button { padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #45a049; }
            .stop-btn { background: #f44336; }
            .stop-btn:hover { background: #da190b; }
            .status { margin: 10px 0; }
            .video-container { text-align: center; margin: 20px 0; }
            img { max-width: 100%; border-radius: 5px; }
            .telemetry { font-family: monospace; font-size: 12px; }
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 LunarBot Autonomous Navigation System</h1>
                <p>Real-time Robot Control Dashboard</p>
            </div>
            
            <div class="dashboard">
                <div class="panel">
                    <h3>Robot Control</h3>
                    <div class="controls">
                        <button onclick="moveRobot(0.5, 0)">Forward</button>
                        <button onclick="moveRobot(-0.5, 0)">Backward</button>
                        <button onclick="moveRobot(0, 0.5)">Turn Left</button>
                        <button onclick="moveRobot(0, -0.5)">Turn Right</button>
                        <button onclick="stopRobot()" class="stop-btn">Emergency Stop</button>
                    </div>
                    
                    <h4>Navigation</h4>
                    <div class="controls">
                        <button onclick="navigateTo(5, 0)">Go to (5, 0)</button>
                        <button onclick="navigateTo(0, 5)">Go to (0, 5)</button>
                        <button onclick="navigateTo(-5, 0)">Go to (-5, 0)</button>
                    </div>
                </div>
                
                <div class="panel">
                    <h3>Robot Status</h3>
                    <div id="status" class="status">
                        <p>Battery: <span id="battery">85%</span></p>
                        <p>Position: <span id="position">(0.0, 0.0, 0.0)</span></p>
                        <p>Status: <span id="nav-status">idle</span></p>
                        <p>Speed: <span id="speed">0.0 m/s</span></p>
                    </div>
                </div>
            </div>
            
            <div class="panel">
                <h3>Camera Feed</h3>
                <div class="video-container">
                    <img id="camera-feed" src="" alt="Camera Feed">
                </div>
            </div>
            
            <div class="panel">
                <h3>LiDAR Data</h3>
                <div id="lidar-info" class="telemetry">
                    <p>LiDAR Points: <span id="lidar-count">0</span></p>
                    <p>Last Update: <span id="lidar-time">-</span></p>
                </div>
            </div>
        </div>

        <script>
            const socket = io();
            
            socket.on('connect', function() {
                console.log('Connected to LunarBot server');
                updateStatus();
            });
            
            socket.on('camera_frame', function(data) {
                document.getElementById('camera-feed').src = 'data:image/jpeg;base64,' + data.image;
            });
            
            socket.on('lidar_data', function(data) {
                document.getElementById('lidar-count').textContent = data.points.length;
                document.getElementById('lidar-time').textContent = new Date(data.timestamp * 1000).toLocaleTimeString();
            });
            
            function moveRobot(linear, angular) {
                fetch('/api/robot/move', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({linear_x: linear, angular_z: angular})
                });
            }
            
            function navigateTo(x, y) {
                fetch('/api/robot/navigate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({x: x, y: y, theta: 0})
                });
            }
            
            function stopRobot() {
                fetch('/api/robot/stop', {method: 'POST'});
            }
            
            function updateStatus() {
                fetch('/api/robot/status')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('battery').textContent = data.battery_level + '%';
                        document.getElementById('position').textContent = 
                            `(${data.position.x.toFixed(1)}, ${data.position.y.toFixed(1)}, ${data.position.theta.toFixed(1)})`;
                        document.getElementById('nav-status').textContent = data.navigation_status;
                        document.getElementById('speed').textContent = data.current_speed.toFixed(1) + ' m/s';
                    });
            }
            
            setInterval(updateStatus, 1000);
        </script>
    </body>
    </html>
    """

@app.route('/api/robot/status')
def get_robot_status():
    """Get current robot status"""
    robot.robot_status['last_update'] = time.time()
    return jsonify(robot.robot_status)

@app.route('/api/robot/move', methods=['POST'])
def move_robot():
    """Send movement command to robot"""
    data = request.json
    linear_x = data.get('linear_x', 0.0)
    angular_z = data.get('angular_z', 0.0)
    
    robot.send_velocity_command(linear_x, angular_z)
    return jsonify({'status': 'success'})

@app.route('/api/robot/navigate', methods=['POST'])
def navigate_robot():
    """Send navigation goal to robot"""
    data = request.json
    x = data.get('x', 0.0)
    y = data.get('y', 0.0)
    theta = data.get('theta', 0.0)
    
    robot.send_navigation_goal(x, y, theta)
    return jsonify({'status': 'success'})

@app.route('/api/robot/stop', methods=['POST'])
def stop_robot():
    """Emergency stop the robot"""
    robot.emergency_stop()
    return jsonify({'status': 'success'})

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('status', {'connected': True})
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {request.sid}")

@socketio.on('control_robot')
def handle_robot_control(data):
    """Handle real-time robot control"""
    linear = data.get('linear', 0.0)
    angular = data.get('angular', 0.0)
    robot.send_velocity_command(linear, angular)
    emit('control_ack', {'status': 'received'})

@socketio.on('request_telemetry')
def handle_telemetry_request():
    """Send current telemetry data"""
    emit('telemetry_update', robot.telemetry)

if __name__ == '__main__':
    print("Starting LunarBot Web Interface Demo...")
    print("Access dashboard at: http://localhost:5000")
    print("This is a simulation version that works without ROS2")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
