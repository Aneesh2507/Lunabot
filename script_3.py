# 3. SLAM and Navigation Module
slam_navigation_code = '''#!/usr/bin/env python3
"""
LunarBot SLAM and Navigation Module
Integrates SLAM with Nav2 for autonomous navigation
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from sensor_msgs.msg import LaserScan, PointCloud2
from geometry_msgs.msg import PoseStamped, Twist, PoseWithCovarianceStamped
from nav_msgs.msg import OccupancyGrid, Path
from nav2_msgs.action import NavigateToPose
from tf2_ros import Buffer, TransformListener
import numpy as np
import math

class SLAMNavigationNode(Node):
    def __init__(self):
        super().__init__('slam_navigation_node')
        
        # TF2 setup
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        # Navigation action client
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        # Subscribers
        self.lidar_subscription = self.create_subscription(
            LaserScan, '/scan', self.lidar_callback, 10)
        self.map_subscription = self.create_subscription(
            OccupancyGrid, '/map', self.map_callback, 10)
        self.pose_subscription = self.create_subscription(
            PoseWithCovarianceStamped, '/amcl_pose', self.pose_callback, 10)
        
        # Publishers
        self.goal_publisher = self.create_publisher(
            PoseStamped, '/goal_pose', 10)
        self.cmd_vel_publisher = self.create_publisher(
            Twist, '/cmd_vel', 10)
        
        # Navigation state
        self.current_pose = None
        self.current_map = None
        self.navigation_goals = []
        self.current_goal_index = 0
        
        # Safety parameters
        self.min_obstacle_distance = 0.5  # meters
        self.emergency_stop_distance = 0.3  # meters
        
        # Timer for navigation monitoring
        self.navigation_timer = self.create_timer(0.1, self.navigation_monitor)
        
        self.get_logger().info("SLAM Navigation Node initialized")
    
    def lidar_callback(self, msg):
        """Process LiDAR data for obstacle detection"""
        try:
            # Convert laser scan to cartesian coordinates
            ranges = np.array(msg.ranges)
            angles = np.linspace(msg.angle_min, msg.angle_max, len(ranges))
            
            # Filter invalid readings
            valid_indices = np.isfinite(ranges) & (ranges > msg.range_min) & (ranges < msg.range_max)
            valid_ranges = ranges[valid_indices]
            valid_angles = angles[valid_indices]
            
            # Check for emergency stop conditions
            if len(valid_ranges) > 0:
                min_distance = np.min(valid_ranges)
                if min_distance < self.emergency_stop_distance:
                    self.emergency_stop()
                    self.get_logger().warn(f"Emergency stop! Obstacle at {min_distance:.2f}m")
            
            # Update local costmap with recent obstacles
            self.update_local_obstacles(valid_ranges, valid_angles)
            
        except Exception as e:
            self.get_logger().error(f"LiDAR processing error: {str(e)}")
    
    def map_callback(self, msg):
        """Update current map for path planning"""
        self.current_map = msg
        self.get_logger().debug("Map updated")
    
    def pose_callback(self, msg):
        """Update current robot pose"""
        self.current_pose = msg.pose.pose
    
    def set_navigation_goals(self, waypoints):
        """Set sequence of navigation goals"""
        self.navigation_goals = waypoints
        self.current_goal_index = 0
        self.get_logger().info(f"Set {len(waypoints)} navigation goals")
    
    def navigate_to_next_goal(self):
        """Navigate to the next goal in the sequence"""
        if self.current_goal_index >= len(self.navigation_goals):
            self.get_logger().info("All navigation goals completed!")
            return
        
        goal_pose = self.navigation_goals[self.current_goal_index]
        
        # Create navigation goal
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = goal_pose
        
        # Send goal to Nav2
        if not self.nav_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error("Nav2 server not available")
            return
        
        self.get_logger().info(f"Navigating to goal {self.current_goal_index + 1}")
        future = self.nav_client.send_goal_async(goal_msg)
        future.add_done_callback(self.goal_response_callback)
    
    def goal_response_callback(self, future):
        """Handle navigation goal response"""
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Navigation goal rejected")
            return
        
        self.get_logger().info("Navigation goal accepted")
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.navigation_result_callback)
    
    def navigation_result_callback(self, future):
        """Handle navigation result"""
        result = future.result().result
        if result:
            self.get_logger().info(f"Goal {self.current_goal_index + 1} completed")
            self.current_goal_index += 1
            
            # Navigate to next goal after a short delay
            self.create_timer(2.0, self.navigate_to_next_goal, count=1)
        else:
            self.get_logger().error("Navigation failed")
    
    def emergency_stop(self):
        """Emergency stop the robot"""
        stop_msg = Twist()
        stop_msg.linear.x = 0.0
        stop_msg.angular.z = 0.0
        self.cmd_vel_publisher.publish(stop_msg)
    
    def update_local_obstacles(self, ranges, angles):
        """Update local obstacle information"""
        # Convert to cartesian coordinates
        x_coords = ranges * np.cos(angles)
        y_coords = ranges * np.sin(angles)
        
        # Filter close obstacles
        close_obstacles = ranges < self.min_obstacle_distance
        if np.any(close_obstacles):
            self.get_logger().warn(f"Close obstacles detected: {np.sum(close_obstacles)} points")
    
    def navigation_monitor(self):
        """Monitor navigation progress and safety"""
        if self.current_pose is None:
            return
        
        # Check if robot is stuck (velocity too low for too long)
        # This would require velocity monitoring implementation
        
        # Check battery level (if available)
        # This would require battery status integration
        
        # Update navigation statistics
        pass
    
    def calculate_path_safety_score(self, path):
        """Calculate safety score for a given path"""
        if self.current_map is None:
            return 0.0
        
        # Analyze path through occupancy grid
        # This would implement path safety analysis
        safety_score = 1.0  # Placeholder
        return safety_score

def main(args=None):
    rclpy.init(args=args)
    node = SLAMNavigationNode()
    
    # Example usage: set navigation goals
    waypoints = [
        # Create example waypoints for lunar exploration
        create_pose_stamped(5.0, 0.0, 0.0),
        create_pose_stamped(10.0, 5.0, 1.57),
        create_pose_stamped(0.0, 10.0, 3.14),
    ]
    node.set_navigation_goals(waypoints)
    node.navigate_to_next_goal()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

def create_pose_stamped(x, y, theta):
    """Helper function to create PoseStamped message"""
    pose = PoseStamped()
    pose.header.frame_id = "map"
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.position.z = 0.0
    
    # Convert theta to quaternion
    pose.pose.orientation.z = math.sin(theta / 2.0)
    pose.pose.orientation.w = math.cos(theta / 2.0)
    
    return pose

if __name__ == '__main__':
    main()
'''

with open('slam_navigation.py', 'w') as f:
    f.write(slam_navigation_code)

print("✅ Created slam_navigation.py")