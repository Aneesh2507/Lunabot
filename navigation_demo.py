#!/usr/bin/env python3
"""
LunarBot Navigation Demo with Visual Bot Figure
Enhanced version with visual bot representation and safe path navigation
"""

import numpy as np
import time
import random
import json
import math
import threading
from typing import List, Tuple, Optional
from dataclasses import dataclass

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

@dataclass
class SafePath:
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    width: float
    safety_score: float

class LunarBotFigure:
    def __init__(self, x: float = 0, y: float = 0, theta: float = 0):
        self.position = Point(x, y)
        self.theta = theta
        self.speed = 0.0
        self.angular_speed = 0.0
        self.battery_level = 100.0
        self.status = "idle"
        self.target_position = None
        self.path_to_target = []
        
        # Visual properties
        self.size = 1.0  # Bot size in meters
        self.color = "blue"
        self.direction_color = "yellow"
        
        # Movement constraints
        self.max_speed = 2.0
        self.max_angular_speed = 1.5
        self.acceleration = 0.1
        self.angular_acceleration = 0.2
    
    def update(self, dt: float):
        """Update bot position and state"""
        # Update position based on current speeds
        self.position.x += self.speed * math.cos(self.theta) * dt
        self.position.y += self.speed * math.sin(self.theta) * dt
        self.theta += self.angular_speed * dt
        
        # Normalize angle
        self.theta = self.theta % (2 * math.pi)
        
        # Drain battery based on movement
        if abs(self.speed) > 0.01 or abs(self.angular_speed) > 0.01:
            self.battery_level -= 0.1 * dt
            self.battery_level = max(0, self.battery_level)
    
    def move_forward(self, dt: float):
        """Move forward"""
        self.speed = min(self.speed + self.acceleration * dt, self.max_speed)
        self.status = "moving"
    
    def move_backward(self, dt: float):
        """Move backward"""
        self.speed = max(self.speed - self.acceleration * dt, -self.max_speed)
        self.status = "moving"
    
    def turn_left(self, dt: float):
        """Turn left"""
        self.angular_speed = min(self.angular_speed + self.angular_acceleration * dt, self.max_angular_speed)
        self.status = "moving"
    
    def turn_right(self, dt: float):
        """Turn right"""
        self.angular_speed = max(self.angular_speed - self.angular_acceleration * dt, -self.max_angular_speed)
        self.status = "moving"
    
    def stop(self):
        """Stop the bot"""
        self.speed = 0.0
        self.angular_speed = 0.0
        self.status = "stopped"
    
    def navigate_to(self, target_x: float, target_y: float, safe_paths: List[SafePath]):
        """Navigate to target using safe paths"""
        self.target_position = Point(target_x, target_y)
        self.path_to_target = self.find_safe_path(safe_paths)
        self.status = "navigating"
    
    def find_safe_path(self, safe_paths: List[SafePath]) -> List[Point]:
        """Find the best safe path to target"""
        if not safe_paths or not self.target_position:
            return [self.target_position] if self.target_position else []
        
        # Simple pathfinding - find closest safe path
        best_path = None
        min_distance = float('inf')
        
        for path in safe_paths:
            # Calculate distance to path start
            dist_to_start = math.sqrt(
                (self.position.x - path.start_x) ** 2 + 
                (self.position.y - path.start_y) ** 2
            )
            
            if dist_to_start < min_distance and path.safety_score > 0.7:
                min_distance = dist_to_start
                best_path = path
        
        if best_path:
            return [
                Point(best_path.start_x, best_path.start_y),
                Point(best_path.end_x, best_path.end_y),
                self.target_position
            ]
        
        return [self.target_position]

class TerrainGenerator:
    def __init__(self, width: float = 50, height: float = 50):
        self.width = width
        self.height = height
        self.obstacles = []
        self.safe_paths = []
        self.generate_terrain()
    
    def generate_terrain(self):
        """Generate lunar terrain with obstacles and safe paths"""
        # Generate obstacles
        obstacle_types = ['rock', 'crater', 'boulder', 'pothole']
        for _ in range(15):
            obstacle = Obstacle(
                x=random.uniform(-self.width/2, self.width/2),
                y=random.uniform(-self.height/2, self.height/2),
                radius=random.uniform(0.5, 2.0),
                obstacle_type=random.choice(obstacle_types)
            )
            self.obstacles.append(obstacle)
        
        # Generate safe paths
        for _ in range(8):
            start_x = random.uniform(-self.width/2, self.width/2)
            start_y = random.uniform(-self.height/2, self.height/2)
            
            # Create path in random direction
            angle = random.uniform(0, 2 * math.pi)
            length = random.uniform(5, 15)
            
            end_x = start_x + length * math.cos(angle)
            end_y = start_y + length * math.sin(angle)
            
            # Keep path within bounds
            end_x = max(-self.width/2, min(self.width/2, end_x))
            end_y = max(-self.height/2, min(self.height/2, end_y))
            
            safe_path = SafePath(
                start_x=start_x,
                start_y=start_y,
                end_x=end_x,
                end_y=end_y,
                width=random.uniform(1.0, 2.0),
                safety_score=random.uniform(0.7, 1.0)
            )
            self.safe_paths.append(safe_path)

class LunarBotDemo:
    def __init__(self):
        print("Initializing LunarBot Navigation Demo with Visual Bot Figure...")
        
        # Initialize bot figure
        self.bot = LunarBotFigure(0.0, 0.0, 0.0)
        
        # Initialize terrain
        self.terrain = TerrainGenerator(50, 50)
        
        # Navigation goals
        self.goals = [
            {'x': 5.0, 'y': 0.0, 'name': 'Exploration Point Alpha'},
            {'x': 0.0, 'y': 5.0, 'name': 'Exploration Point Beta'},
            {'x': -5.0, 'y': 0.0, 'name': 'Exploration Point Gamma'},
            {'x': 0.0, 'y': -5.0, 'name': 'Base Station'}
        ]
        self.current_goal_index = 0
        
        # Sensor data simulation
        self.lidar_data = []
        self.camera_data = None
        
    def generate_lidar_data(self):
        """Generate simulated LiDAR readings"""
        ranges = []
        angles = np.linspace(0, 2*np.pi, 360)
        
        for angle in angles:
            # Simulate obstacles at various distances
            if random.random() < 0.15:  # 15% chance of obstacle
                range_val = random.uniform(0.5, 2.0)
            else:
                range_val = random.uniform(2.0, 8.0)
            
            ranges.append({
                'angle': float(angle),
                'range': float(range_val),
                'x': float(range_val * np.cos(angle)),
                'y': float(range_val * np.sin(angle))
            })
        
        return ranges
    
    def generate_camera_data(self):
        """Generate simulated camera data"""
        # Simulate lunar terrain features
        features = []
        
        # Add rocks
        for _ in range(random.randint(3, 8)):
            features.append({
                'type': 'rock',
                'x': random.uniform(-3, 3),
                'y': random.uniform(-3, 3),
                'size': random.uniform(0.2, 1.0),
                'confidence': random.uniform(0.7, 0.95)
            })
        
        # Add craters
        for _ in range(random.randint(1, 3)):
            features.append({
                'type': 'crater',
                'x': random.uniform(-4, 4),
                'y': random.uniform(-4, 4),
                'size': random.uniform(1.0, 3.0),
                'confidence': random.uniform(0.8, 0.95)
            })
        
        # Add safe paths
        for _ in range(random.randint(2, 5)):
            features.append({
                'type': 'safe_path',
                'x': random.uniform(-5, 5),
                'y': random.uniform(-5, 5),
                'size': random.uniform(0.5, 2.0),
                'confidence': random.uniform(0.6, 0.9)
            })
        
        return features
    
    def move_robot(self, linear_x, angular_z, duration=1.0):
        """Simulate robot movement using bot figure"""
        print(f"Moving robot: linear={linear_x:.2f} m/s, angular={angular_z:.2f} rad/s")
        
        # Update bot speeds
        if linear_x > 0:
            self.bot.speed = min(linear_x, self.bot.max_speed)
        elif linear_x < 0:
            self.bot.speed = max(linear_x, -self.bot.max_speed)
        
        if angular_z > 0:
            self.bot.angular_speed = min(angular_z, self.bot.max_angular_speed)
        elif angular_z < 0:
            self.bot.angular_speed = max(angular_z, -self.bot.max_angular_speed)
        
        # Simulate movement over time
        dt = 0.1
        steps = int(duration / dt)
        
        for _ in range(steps):
            self.bot.update(dt)
            time.sleep(dt)
        
        # Stop the bot
        self.bot.stop()
        
        print(f"New position: ({self.bot.position.x:.2f}, {self.bot.position.y:.2f}, {self.bot.theta:.2f})")
        print(f"Bot status: {self.bot.status}, Battery: {self.bot.battery_level:.1f}%")
    
    def navigate_to_goal(self, goal):
        """Navigate to a specific goal using bot figure and safe paths"""
        print(f"Navigating to {goal['name']} at ({goal['x']}, {goal['y']})")
        self.bot.status = 'navigating'
        
        # Set navigation target for bot
        self.bot.navigate_to(goal['x'], goal['y'], self.terrain.safe_paths)
        
        # Calculate path
        dx = goal['x'] - self.bot.position.x
        dy = goal['y'] - self.bot.position.y
        distance = np.sqrt(dx**2 + dy**2)
        
        print(f"Distance to goal: {distance:.2f} meters")
        print(f"Safe paths available: {len(self.terrain.safe_paths)}")
        
        # Display planned path
        if self.bot.path_to_target:
            print("Planned navigation path:")
            for i, point in enumerate(self.bot.path_to_target):
                print(f"  Waypoint {i+1}: ({point.x:.2f}, {point.y:.2f})")
        
        # Simulate navigation
        if distance > 0.1:
            # Move towards goal
            angle_to_goal = np.arctan2(dy, dx)
            angle_diff = angle_to_goal - self.bot.theta
            
            # Normalize angle
            while angle_diff > np.pi:
                angle_diff -= 2*np.pi
            while angle_diff < -np.pi:
                angle_diff += 2*np.pi
            
            # Turn towards goal
            if abs(angle_diff) > 0.1:
                self.move_robot(0.0, np.sign(angle_diff) * 0.5, abs(angle_diff) / 0.5)
            
            # Move forward
            move_distance = min(distance, 1.0)
            self.move_robot(0.5, 0.0, move_distance / 0.5)
            
            # Recursive call to continue navigation
            self.navigate_to_goal(goal)
        else:
            print(f"Reached {goal['name']}!")
            self.bot.status = 'idle'
    
    def run_autonomous_mission(self):
        """Run autonomous exploration mission"""
        print("\n" + "="*60)
        print("🚀 Starting LunarBot Autonomous Mission")
        print("="*60)
        
        for i, goal in enumerate(self.goals):
            print(f"\nMission Phase {i+1}/{len(self.goals)}")
            print(f"Current battery: {self.bot.battery_level:.1f}%")
            print(f"Bot position: ({self.bot.position.x:.2f}, {self.bot.position.y:.2f})")
            print(f"Bot status: {self.bot.status}")
            
            if self.bot.battery_level < 20:
                print("⚠️  Low battery! Returning to base...")
                base_goal = {'x': 0.0, 'y': 0.0, 'name': 'Emergency Base Return'}
                self.navigate_to_goal(base_goal)
                break
            
            # Generate sensor data
            self.lidar_data = self.generate_lidar_data()
            self.camera_data = self.generate_camera_data()
            
            print(f"LiDAR: {len(self.lidar_data)} points")
            print(f"Camera: {len(self.camera_data)} features detected")
            
            # Navigate to goal
            self.navigate_to_goal(goal)
            
            # Simulate exploration time
            print("Conducting exploration...")
            time.sleep(2)
            
            # Update battery
            self.bot.battery_level -= 5
        
        print("\n" + "="*60)
        print("Mission completed!")
        print(f"Final position: ({self.bot.position.x:.2f}, {self.bot.position.y:.2f})")
        print(f"Final battery: {self.bot.battery_level:.1f}%")
        print(f"Final status: {self.bot.status}")
        print("="*60)
    
    def run_interactive_demo(self):
        """Run interactive demo"""
        print("\n" + "="*60)
        print("🎮 LunarBot Interactive Demo")
        print("="*60)
        print("Commands:")
        print("  w - Move forward")
        print("  s - Move backward") 
        print("  a - Turn left")
        print("  d - Turn right")
        print("  g - Go to next goal")
        print("  r - Run autonomous mission")
        print("  v - View detailed bot status")
        print("  q - Quit")
        print("="*60)
        
        while True:
            print(f"\nBot Position: ({self.bot.position.x:.2f}, {self.bot.position.y:.2f}, {self.bot.theta:.2f})")
            print(f"Battery: {self.bot.battery_level:.1f}% | Status: {self.bot.status}")
            print(f"Terrain: {len(self.terrain.obstacles)} obstacles, {len(self.terrain.safe_paths)} safe paths")
            
            command = input("Enter command: ").lower().strip()
            
            if command == 'q':
                break
            elif command == 'w':
                self.move_robot(0.5, 0.0, 1.0)
            elif command == 's':
                self.move_robot(-0.5, 0.0, 1.0)
            elif command == 'a':
                self.move_robot(0.0, 0.5, 1.0)
            elif command == 'd':
                self.move_robot(0.0, -0.5, 1.0)
            elif command == 'g':
                if self.current_goal_index < len(self.goals):
                    goal = self.goals[self.current_goal_index]
                    self.navigate_to_goal(goal)
                    self.current_goal_index = (self.current_goal_index + 1) % len(self.goals)
                else:
                    print("All goals completed!")
            elif command == 'r':
                self.run_autonomous_mission()
            elif command == 'v':
                self.display_bot_status()
            else:
                print("Invalid command!")
        
        print("Demo ended. Goodbye!")
    
    def display_bot_status(self):
        """Display detailed bot status and visual representation"""
        print("\n" + "="*50)
        print("🤖 LunarBot Status Display")
        print("="*50)
        
        # Bot position and orientation
        print(f"Position: ({self.bot.position.x:.2f}, {self.bot.position.y:.2f})")
        print(f"Orientation: {math.degrees(self.bot.theta):.1f}°")
        print(f"Speed: {self.bot.speed:.2f} m/s")
        print(f"Angular Speed: {math.degrees(self.bot.angular_speed):.1f}°/s")
        print(f"Status: {self.bot.status}")
        print(f"Battery: {self.bot.battery_level:.1f}%")
        
        # Visual representation
        print("\nBot Visual Representation:")
        print("    🌙 Lunar Surface")
        print("    " + " " * 20 + "🤖")  # Bot position indicator
        print("    Direction: " + "→" if abs(self.bot.theta) < 0.1 else 
              "↗" if 0 < self.bot.theta < math.pi/2 else
              "↑" if abs(self.bot.theta - math.pi/2) < 0.1 else
              "↖" if math.pi/2 < self.bot.theta < math.pi else
              "←" if abs(self.bot.theta - math.pi) < 0.1 else
              "↙" if math.pi < self.bot.theta < 3*math.pi/2 else
              "↓" if abs(self.bot.theta - 3*math.pi/2) < 0.1 else
              "↘")
        
        # Terrain information
        print(f"\nTerrain Information:")
        print(f"  Obstacles: {len(self.terrain.obstacles)}")
        for i, obstacle in enumerate(self.terrain.obstacles[:5]):  # Show first 5
            distance = math.sqrt((obstacle.x - self.bot.position.x)**2 + 
                               (obstacle.y - self.bot.position.y)**2)
            print(f"    {obstacle.obstacle_type.capitalize()} at ({obstacle.x:.1f}, {obstacle.y:.1f}) - {distance:.1f}m away")
        
        print(f"  Safe Paths: {len(self.terrain.safe_paths)}")
        for i, path in enumerate(self.terrain.safe_paths[:3]):  # Show first 3
            print(f"    Path {i+1}: Safety {path.safety_score:.2f}, Width {path.width:.1f}m")
        
        # Navigation target
        if self.bot.target_position:
            distance = math.sqrt((self.bot.target_position.x - self.bot.position.x)**2 + 
                               (self.bot.target_position.y - self.bot.position.y)**2)
            print(f"\nNavigation Target: ({self.bot.target_position.x:.2f}, {self.bot.target_position.y:.2f})")
            print(f"Distance to target: {distance:.2f}m")
            
            if self.bot.path_to_target:
                print("Planned path:")
                for i, point in enumerate(self.bot.path_to_target):
                    print(f"  Waypoint {i+1}: ({point.x:.2f}, {point.y:.2f})")
        
        print("="*50)

def main():
    """Main function"""
    print("=" * 60)
    print("🚀 LunarBot Navigation System Demo")
    print("=" * 60)
    print("This demo simulates autonomous navigation on lunar terrain")
    print("Features: SLAM, object detection, path planning")
    print("=" * 60)
    
    # Initialize robot
    robot = LunarBotDemo()
    
    # Choose demo mode
    print("\nChoose demo mode:")
    print("1. Interactive Demo")
    print("2. Autonomous Mission")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == '1':
        robot.run_interactive_demo()
    elif choice == '2':
        robot.run_autonomous_mission()
    else:
        print("Invalid choice! Running autonomous mission...")
        robot.run_autonomous_mission()
    
    print("\nDemo completed successfully!")
    print("\nTo run the full system:")
    print("1. Install ROS2 Humble")
    print("2. Install Gazebo simulation")
    print("3. Run: ros2 launch lunarbot_bringup full_system.launch.py")
    print("4. Access web interface at: http://localhost:5000")

if __name__ == '__main__':
    main()
