#!/usr/bin/env python3
"""
LunarBot Web-Based Navigation Simulator
Enhanced web interface with visual bot navigation and safe path detection
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import time
import math
import random
import threading
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lunarbot_navigation_2024'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

@dataclass
class Point:
    x: float
    y: float

@dataclass
class Obstacle:
    x: float
    y: float
    radius: float
    obstacle_type: str
    id: str

@dataclass
class SafePath:
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    width: float
    safety_score: float
    id: str

@dataclass
class BotState:
    position: Point
    theta: float
    speed: float
    angular_speed: float
    battery_level: float
    status: str
    target_position: Optional[Point]
    path_to_target: List[Point]

class LunarBotSimulator:
    def __init__(self):
        self.width = 2000
        self.height = 2000
        
        # Initialize bot
        self.bot = BotState(
            position=Point(self.width // 2, self.height // 2),
            theta=0.0,
            speed=0.0,
            angular_speed=0.0,
            battery_level=100.0,
            status="idle",
            target_position=None,
            path_to_target=[]
        )
        
        # Initialize terrain
        self.obstacles = []
        self.safe_paths = []
        self.generate_terrain()
        
        # Movement constraints
        self.max_speed = 2.0
        self.max_angular_speed = 1.5
        self.acceleration = 0.1
        self.angular_acceleration = 0.2
        
        # Simulation state
        self.running = False
        self.last_update = time.time()
        
    def generate_terrain(self):
        """Generate lunar terrain with obstacles and safe paths"""
        # Generate obstacles
        obstacle_types = ['rock', 'crater', 'boulder', 'pothole']
        for i in range(25):
            obstacle = Obstacle(
                x=random.uniform(50, self.width - 50),
                y=random.uniform(50, self.height - 50),
                radius=random.uniform(15, 40),
                obstacle_type=random.choice(obstacle_types),
                id=f"obstacle_{i}"
            )
            self.obstacles.append(obstacle)
        
        # Generate safe paths
        for i in range(12):
            start_x = random.uniform(100, self.width - 100)
            start_y = random.uniform(100, self.height - 100)
            
            # Create path in random direction
            angle = random.uniform(0, 2 * math.pi)
            length = random.uniform(150, 300)
            
            end_x = start_x + length * math.cos(angle)
            end_y = start_y + length * math.sin(angle)
            
            # Keep path within bounds
            end_x = max(100, min(self.width - 100, end_x))
            end_y = max(100, min(self.height - 100, end_y))
            
            safe_path = SafePath(
                start_x=start_x,
                start_y=start_y,
                end_x=end_x,
                end_y=end_y,
                width=random.uniform(25, 50),
                safety_score=random.uniform(0.7, 1.0),
                id=f"path_{i}"
            )
            self.safe_paths.append(safe_path)
    
    def update_bot(self, dt: float):
        """Update bot position and state"""
        # Update position based on current speeds
        self.bot.position.x += self.bot.speed * math.cos(self.bot.theta) * dt
        self.bot.position.y += self.bot.speed * math.sin(self.bot.theta) * dt
        self.bot.theta += self.bot.angular_speed * dt
        
        # Normalize angle
        self.bot.theta = self.bot.theta % (2 * math.pi)
        
        # Keep bot within bounds
        self.bot.position.x = max(20, min(self.width - 20, self.bot.position.x))
        self.bot.position.y = max(20, min(self.height - 20, self.bot.position.y))
        
        # Drain battery based on movement
        if abs(self.bot.speed) > 0.01 or abs(self.bot.angular_speed) > 0.01:
            self.bot.battery_level -= 0.05 * dt
            self.bot.battery_level = max(0, self.bot.battery_level)
        
        # Check collision with obstacles
        if self.check_collision():
            self.bot.speed = 0.0
            self.bot.angular_speed = 0.0
            self.bot.status = "collision"
        
        # Check if target reached
        if self.bot.target_position:
            distance = math.sqrt(
                (self.bot.position.x - self.bot.target_position.x) ** 2 + 
                (self.bot.position.y - self.bot.target_position.y) ** 2
            )
            if distance < 15:  # Within 15 pixels
                self.bot.target_position = None
                self.bot.path_to_target = []
                self.bot.status = "idle"
    
    def check_collision(self) -> bool:
        """Check if bot collides with any obstacle"""
        for obstacle in self.obstacles:
            distance = math.sqrt(
                (self.bot.position.x - obstacle.x) ** 2 + 
                (self.bot.position.y - obstacle.y) ** 2
            )
            if distance < obstacle.radius + 10:  # 10 pixel safety margin
                return True
        return False
    
    def move_forward(self):
        """Move forward"""
        self.bot.speed = min(self.bot.speed + self.acceleration, self.max_speed)
        self.bot.status = "moving"
    
    def move_backward(self):
        """Move backward"""
        self.bot.speed = max(self.bot.speed - self.acceleration, -self.max_speed)
        self.bot.status = "moving"
    
    def turn_left(self):
        """Turn left"""
        self.bot.angular_speed = min(self.bot.angular_speed + self.angular_acceleration, self.max_angular_speed)
        self.bot.status = "moving"
    
    def turn_right(self):
        """Turn right"""
        self.bot.angular_speed = max(self.bot.angular_speed - self.angular_acceleration, -self.max_angular_speed)
        self.bot.status = "moving"
    
    def stop(self):
        """Stop the bot"""
        self.bot.speed = 0.0
        self.bot.angular_speed = 0.0
        self.bot.status = "stopped"
    
    def navigate_to(self, target_x: float, target_y: float):
        """Navigate to target using safe paths"""
        self.bot.target_position = Point(target_x, target_y)
        self.bot.path_to_target = self.find_safe_path(target_x, target_y)
        self.bot.status = "navigating"
    
    def find_safe_path(self, target_x: float, target_y: float) -> List[Point]:
        """Find the best safe path to target"""
        if not self.safe_paths:
            return [Point(target_x, target_y)]
        
        # Simple pathfinding - find closest safe path
        best_path = None
        min_distance = float('inf')
        
        for path in self.safe_paths:
            # Calculate distance to path start
            dist_to_start = math.sqrt(
                (self.bot.position.x - path.start_x) ** 2 + 
                (self.bot.position.y - path.start_y) ** 2
            )
            
            if dist_to_start < min_distance and path.safety_score > 0.7:
                min_distance = dist_to_start
                best_path = path
        
        if best_path:
            return [
                Point(best_path.start_x, best_path.start_y),
                Point(best_path.end_x, best_path.end_y),
                Point(target_x, target_y)
            ]
        
        return [Point(target_x, target_y)]
    
    def get_state(self) -> Dict:
        """Get current simulation state"""
        return {
            'bot': {
                'position': asdict(self.bot.position),
                'theta': self.bot.theta,
                'speed': self.bot.speed,
                'angular_speed': self.bot.angular_speed,
                'battery_level': self.bot.battery_level,
                'status': self.bot.status,
                'target_position': asdict(self.bot.target_position) if self.bot.target_position else None,
                'path_to_target': [asdict(p) for p in self.bot.path_to_target]
            },
            'terrain': {
                'obstacles': [asdict(obs) for obs in self.obstacles],
                'safe_paths': [asdict(path) for path in self.safe_paths]
            },
            'world': {
                'width': self.width,
                'height': self.height
            }
        }
    
    def run_simulation(self):
        """Run simulation loop"""
        self.running = True
        while self.running:
            current_time = time.time()
            dt = current_time - self.last_update
            self.last_update = current_time
            
            self.update_bot(dt)
            
            # Emit state update to connected clients
            socketio.emit('simulation_update', self.get_state())
            
            time.sleep(0.05)  # 20 FPS

# Global simulator instance
simulator = LunarBotSimulator()
simulation_thread = None

def start_simulation():
    """Start simulation in background thread"""
    global simulation_thread
    if simulation_thread is None or not simulation_thread.is_alive():
        simulation_thread = threading.Thread(target=simulator.run_simulation, daemon=True)
        simulation_thread.start()

# Flask Routes
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('navigation_simulator.html')

@app.route('/api/simulator/state')
def get_simulator_state():
    """Get current simulator state"""
    return jsonify(simulator.get_state())

@app.route('/api/simulator/move', methods=['POST'])
def move_bot():
    """Move bot command"""
    data = request.json
    direction = data.get('direction')
    
    if direction == 'forward':
        simulator.move_forward()
    elif direction == 'backward':
        simulator.move_backward()
    elif direction == 'left':
        simulator.turn_left()
    elif direction == 'right':
        simulator.turn_right()
    elif direction == 'stop':
        simulator.stop()
    
    return jsonify({'status': 'success'})

@app.route('/api/simulator/navigate', methods=['POST'])
def navigate_bot():
    """Navigate bot to coordinates"""
    data = request.json
    x = data.get('x', 0)
    y = data.get('y', 0)
    
    simulator.navigate_to(x, y)
    return jsonify({'status': 'success'})

@app.route('/api/simulator/reset', methods=['POST'])
def reset_simulator():
    """Reset simulator to initial state"""
    simulator.bot.position = Point(simulator.width // 2, simulator.height // 2)
    simulator.bot.theta = 0.0
    simulator.bot.speed = 0.0
    simulator.bot.angular_speed = 0.0
    simulator.bot.battery_level = 100.0
    simulator.bot.status = "idle"
    simulator.bot.target_position = None
    simulator.bot.path_to_target = []
    
    return jsonify({'status': 'success'})

@app.route('/api/simulator/terrain', methods=['POST'])
def regenerate_terrain():
    """Regenerate terrain"""
    simulator.obstacles = []
    simulator.safe_paths = []
    simulator.generate_terrain()
    
    return jsonify({'status': 'success'})

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('status', {'connected': True})
    emit('simulation_update', simulator.get_state())
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {request.sid}")

@socketio.on('start_simulation')
def handle_start_simulation():
    """Start simulation"""
    start_simulation()
    emit('simulation_started', {'status': 'success'})

@socketio.on('stop_simulation')
def handle_stop_simulation():
    """Stop simulation"""
    simulator.running = False
    emit('simulation_stopped', {'status': 'success'})

@socketio.on('control_bot')
def handle_bot_control(data):
    """Handle real-time bot control"""
    direction = data.get('direction')
    
    if direction == 'forward':
        simulator.move_forward()
    elif direction == 'backward':
        simulator.move_backward()
    elif direction == 'left':
        simulator.turn_left()
    elif direction == 'right':
        simulator.turn_right()
    elif direction == 'stop':
        simulator.stop()
    
    emit('control_ack', {'status': 'received'})

@socketio.on('navigate_to')
def handle_navigate_to(data):
    """Handle navigation command"""
    x = data.get('x', 0)
    y = data.get('y', 0)
    simulator.navigate_to(x, y)
    emit('navigation_ack', {'status': 'received'})

if __name__ == '__main__':
    # Start simulation
    start_simulation()
    
    print("Starting LunarBot Navigation Simulator...")
    print("Access simulator at: http://localhost:5000")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
