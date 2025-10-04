#!/usr/bin/env python3
"""
LunarBot Navigation Simulator with Visual Bot Figure
Interactive simulation with safe path navigation and bot movement controls
"""

import pygame
import math
import random
import numpy as np
import json
import time
from typing import List, Tuple, Dict, Optional
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
    obstacle_type: str  # 'rock', 'crater', 'boulder'

@dataclass
class SafePath:
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    width: float
    safety_score: float

class LunarBot:
    def __init__(self, x: float = 0, y: float = 0, theta: float = 0):
        self.position = Point(x, y)
        self.theta = theta  # Orientation in radians
        self.speed = 0.0
        self.angular_speed = 0.0
        self.battery_level = 100.0
        self.status = "idle"  # idle, moving, navigating, stopped
        self.target_position = None
        self.path_to_target = []
        
        # Bot appearance
        self.size = 15
        self.color = (0, 150, 255)  # Blue
        self.direction_color = (255, 255, 0)  # Yellow for direction indicator
        
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
        
        # Check if target reached
        if self.target_position:
            distance = math.sqrt(
                (self.position.x - self.target_position.x) ** 2 + 
                (self.position.y - self.target_position.y) ** 2
            )
            if distance < 5:  # Within 5 pixels
                self.target_position = None
                self.path_to_target = []
                self.status = "idle"
    
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
        if not safe_paths:
            return [self.target_position]
        
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
    
    def draw(self, screen: pygame.Surface, camera_offset: Tuple[float, float]):
        """Draw the bot on screen"""
        screen_x = self.position.x - camera_offset[0]
        screen_y = self.position.y - camera_offset[1]
        
        # Draw bot body (circle)
        pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), self.size)
        
        # Draw direction indicator
        direction_x = screen_x + self.size * math.cos(self.theta)
        direction_y = screen_y + self.size * math.sin(self.theta)
        pygame.draw.line(screen, self.direction_color, 
                        (int(screen_x), int(screen_y)), 
                        (int(direction_x), int(direction_y)), 3)
        
        # Draw path to target
        if self.path_to_target:
            path_points = []
            for point in self.path_to_target:
                path_points.append((int(point.x - camera_offset[0]), 
                                  int(point.y - camera_offset[1])))
            if len(path_points) > 1:
                pygame.draw.lines(screen, (0, 255, 0), False, path_points, 2)
        
        # Draw target marker
        if self.target_position:
            target_x = self.target_position.x - camera_offset[0]
            target_y = self.target_position.y - camera_offset[1]
            pygame.draw.circle(screen, (255, 0, 0), 
                            (int(target_x), int(target_y)), 8, 2)

class TerrainGenerator:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.obstacles = []
        self.safe_paths = []
        self.generate_terrain()
    
    def generate_terrain(self):
        """Generate lunar terrain with obstacles and safe paths"""
        # Generate obstacles
        for _ in range(20):
            obstacle = Obstacle(
                x=random.uniform(50, self.width - 50),
                y=random.uniform(50, self.height - 50),
                radius=random.uniform(10, 30),
                obstacle_type=random.choice(['rock', 'crater', 'boulder'])
            )
            self.obstacles.append(obstacle)
        
        # Generate safe paths
        for _ in range(8):
            start_x = random.uniform(50, self.width - 50)
            start_y = random.uniform(50, self.height - 50)
            
            # Create path in random direction
            angle = random.uniform(0, 2 * math.pi)
            length = random.uniform(100, 200)
            
            end_x = start_x + length * math.cos(angle)
            end_y = start_y + length * math.sin(angle)
            
            # Keep path within bounds
            end_x = max(50, min(self.width - 50, end_x))
            end_y = max(50, min(self.height - 50, end_y))
            
            safe_path = SafePath(
                start_x=start_x,
                start_y=start_y,
                end_x=end_x,
                end_y=end_y,
                width=random.uniform(20, 40),
                safety_score=random.uniform(0.6, 1.0)
            )
            self.safe_paths.append(safe_path)
    
    def is_position_safe(self, x: float, y: float) -> bool:
        """Check if position is safe (not in obstacle)"""
        for obstacle in self.obstacles:
            distance = math.sqrt((x - obstacle.x) ** 2 + (y - obstacle.y) ** 2)
            if distance < obstacle.radius + 10:  # 10 pixel safety margin
                return False
        return True
    
    def draw(self, screen: pygame.Surface, camera_offset: Tuple[float, float]):
        """Draw terrain on screen"""
        # Draw obstacles
        for obstacle in self.obstacles:
            screen_x = obstacle.x - camera_offset[0]
            screen_y = obstacle.y - camera_offset[1]
            
            if -obstacle.radius < screen_x < screen.get_width() + obstacle.radius and \
               -obstacle.radius < screen_y < screen.get_height() + obstacle.radius:
                
                color = (100, 100, 100) if obstacle.obstacle_type == 'rock' else \
                       (80, 80, 80) if obstacle.obstacle_type == 'crater' else (60, 60, 60)
                
                pygame.draw.circle(screen, color, 
                                 (int(screen_x), int(screen_y)), 
                                 int(obstacle.radius))
        
        # Draw safe paths
        for path in self.safe_paths:
            start_x = path.start_x - camera_offset[0]
            start_y = path.start_y - camera_offset[1]
            end_x = path.end_x - camera_offset[0]
            end_y = path.end_y - camera_offset[1]
            
            # Only draw if path is visible
            if (0 < start_x < screen.get_width() and 0 < start_y < screen.get_height()) or \
               (0 < end_x < screen.get_width() and 0 < end_y < screen.get_height()):
                
                # Color based on safety score
                safety_color = int(255 * path.safety_score)
                color = (0, safety_color, 0)
                
                pygame.draw.line(screen, color, 
                               (int(start_x), int(start_y)), 
                               (int(end_x), int(end_y)), 
                               int(path.width / 5))

class LunarBotSimulator:
    def __init__(self):
        pygame.init()
        self.width = 1200
        self.height = 800
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("LunarBot Navigation Simulator")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Initialize components
        self.terrain = TerrainGenerator(self.width * 2, self.height * 2)
        self.bot = LunarBot(self.width // 2, self.height // 2)
        
        # Camera system
        self.camera_x = 0
        self.camera_y = 0
        
        # UI elements
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # Control state
        self.keys_pressed = {
            pygame.K_w: False,  # Forward
            pygame.K_s: False,  # Backward
            pygame.K_a: False,  # Left
            pygame.K_d: False,  # Right
            pygame.K_SPACE: False  # Stop
        }
        
        # Navigation mode
        self.navigation_mode = False
        self.target_x = 0
        self.target_y = 0
        
        print("LunarBot Navigation Simulator initialized!")
        print("Controls:")
        print("  WASD - Move bot")
        print("  SPACE - Stop")
        print("  N - Toggle navigation mode")
        print("  Click - Set navigation target")
        print("  ESC - Exit")
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_n:
                    self.navigation_mode = not self.navigation_mode
                    print(f"Navigation mode: {'ON' if self.navigation_mode else 'OFF'}")
                elif event.key in self.keys_pressed:
                    self.keys_pressed[event.key] = True
            
            elif event.type == pygame.KEYUP:
                if event.key in self.keys_pressed:
                    self.keys_pressed[event.key] = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    world_x = mouse_x + self.camera_x
                    world_y = mouse_y + self.camera_y
                    
                    if self.navigation_mode:
                        self.bot.navigate_to(world_x, world_y, self.terrain.safe_paths)
                        print(f"Navigation target set: ({world_x:.1f}, {world_y:.1f})")
                    else:
                        print(f"Clicked at world coordinates: ({world_x:.1f}, {world_y:.1f})")
    
    def update(self, dt: float):
        """Update simulation"""
        # Handle movement controls
        if self.keys_pressed[pygame.K_w]:
            self.bot.move_forward(dt)
        elif self.keys_pressed[pygame.K_s]:
            self.bot.move_backward(dt)
        
        if self.keys_pressed[pygame.K_a]:
            self.bot.turn_left(dt)
        elif self.keys_pressed[pygame.K_d]:
            self.bot.turn_right(dt)
        
        if self.keys_pressed[pygame.K_SPACE]:
            self.bot.stop()
        
        # Update bot
        self.bot.update(dt)
        
        # Update camera to follow bot
        self.camera_x = self.bot.position.x - self.width // 2
        self.camera_y = self.bot.position.y - self.height // 2
    
    def draw_ui(self):
        """Draw user interface"""
        # Status panel
        status_y = 10
        status_texts = [
            f"Battery: {self.bot.battery_level:.1f}%",
            f"Speed: {self.bot.speed:.2f} m/s",
            f"Position: ({self.bot.position.x:.1f}, {self.bot.position.y:.1f})",
            f"Status: {self.bot.status}",
            f"Navigation Mode: {'ON' if self.navigation_mode else 'OFF'}"
        ]
        
        for text in status_texts:
            surface = self.font.render(text, True, (255, 255, 255))
            self.screen.blit(surface, (10, status_y))
            status_y += 25
        
        # Control instructions
        instructions = [
            "Controls:",
            "W/S - Forward/Backward",
            "A/D - Turn Left/Right", 
            "SPACE - Stop",
            "N - Toggle Navigation Mode",
            "Click - Set Target (Navigation Mode)",
            "ESC - Exit"
        ]
        
        inst_y = self.height - len(instructions) * 20 - 10
        for instruction in instructions:
            surface = self.small_font.render(instruction, True, (200, 200, 200))
            self.screen.blit(surface, (10, inst_y))
            inst_y += 20
        
        # Safe paths info
        safe_paths_text = f"Safe Paths: {len(self.terrain.safe_paths)}"
        surface = self.font.render(safe_paths_text, True, (0, 255, 0))
        self.screen.blit(surface, (self.width - 200, 10))
        
        obstacles_text = f"Obstacles: {len(self.terrain.obstacles)}"
        surface = self.font.render(obstacles_text, True, (255, 0, 0))
        self.screen.blit(surface, (self.width - 200, 35))
    
    def draw(self):
        """Draw everything"""
        self.screen.fill((20, 20, 40))  # Dark blue space background
        
        # Draw terrain
        self.terrain.draw(self.screen, (self.camera_x, self.camera_y))
        
        # Draw bot
        self.bot.draw(self.screen, (self.camera_x, self.camera_y))
        
        # Draw UI
        self.draw_ui()
        
        pygame.display.flip()
    
    def run(self):
        """Main simulation loop"""
        print("Starting LunarBot Navigation Simulator...")
        
        while self.running:
            dt = self.clock.tick(60) / 1000.0  # Delta time in seconds
            
            self.handle_events()
            self.update(dt)
            self.draw()
        
        pygame.quit()
        print("Simulation ended.")

def main():
    """Main function"""
    simulator = LunarBotSimulator()
    simulator.run()

if __name__ == "__main__":
    main()
