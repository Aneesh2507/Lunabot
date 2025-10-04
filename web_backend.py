#!/usr/bin/env python3
"""
LunarBot Web Interface Backend
Flask application with WebSocket support for real-time robot control
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from geometry_msgs.msg import Twist, PoseStamped
from sensor_msgs.msg import Image, LaserScan
from nav_msgs.msg import OccupancyGrid
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import base64
import json
import threading
import time
import numpy as np

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lunarbot_secret_2024'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

class WebInterfaceNode(Node):
    def __init__(self):
        super().__init__('web_interface_node')

        # ROS2 Publishers
        self.cmd_vel_publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        self.goal_publisher = self.create_publisher(PoseStamped, '/goal_pose', 10)
        self.emergency_publisher = self.create_publisher(String, '/emergency_stop', 10)

        # ROS2 Subscribers
        self.image_subscription = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10)
        self.lidar_subscription = self.create_subscription(
            LaserScan, '/scan', self.lidar_callback, 10)
        self.map_subscription = self.create_subscription(
            OccupancyGrid, '/map', self.map_callback, 10)
        self.segmentation_subscription = self.create_subscription(
            Image, '/segmentation_map', self.segmentation_callback, 10)

        # OpenCV bridge
        self.bridge = CvBridge()

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

        self.get_logger().info("Web Interface Node initialized")

    def image_callback(self, msg):
        """Process camera images for web streaming"""
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            # Resize for web streaming
            cv_image = cv2.resize(cv_image, (640, 480))

            # Encode to base64 for web transmission
            _, buffer = cv2.imencode('.jpg', cv_image, 
                                   [cv2.IMWRITE_JPEG_QUALITY, 70])
            img_base64 = base64.b64encode(buffer).decode('utf-8')

            self.telemetry['camera_stream'] = img_base64

            # Emit to web clients
            socketio.emit('camera_frame', {
                'image': img_base64,
                'timestamp': time.time()
            })

        except Exception as e:
            self.get_logger().error(f"Camera streaming error: {str(e)}")

    def segmentation_callback(self, msg):
        """Process segmentation maps for web visualization"""
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            cv_image = cv2.resize(cv_image, (640, 480))

            _, buffer = cv2.imencode('.jpg', cv_image,
                                   [cv2.IMWRITE_JPEG_QUALITY, 70])
            img_base64 = base64.b64encode(buffer).decode('utf-8')

            self.telemetry['segmentation_stream'] = img_base64

            socketio.emit('segmentation_frame', {
                'image': img_base64,
                'timestamp': time.time()
            })

        except Exception as e:
            self.get_logger().error(f"Segmentation streaming error: {str(e)}")

    def lidar_callback(self, msg):
        """Process LiDAR data for web visualization"""
        try:
            ranges = np.array(msg.ranges)
            angles = np.linspace(msg.angle_min, msg.angle_max, len(ranges))

            # Filter valid readings
            valid_mask = np.isfinite(ranges) & (ranges > msg.range_min) & (ranges < msg.range_max)
            valid_ranges = ranges[valid_mask]
            valid_angles = angles[valid_mask]

            # Convert to cartesian for web display
            lidar_points = []
            for r, a in zip(valid_ranges, valid_angles):
                x = float(r * np.cos(a))
                y = float(r * np.sin(a))
                lidar_points.append({'x': x, 'y': y, 'range': float(r)})

            self.telemetry['lidar_data'] = lidar_points

            # Emit to web clients
            socketio.emit('lidar_data', {
                'points': lidar_points[:360],  # Limit points for performance
                'timestamp': time.time()
            })

        except Exception as e:
            self.get_logger().error(f"LiDAR processing error: {str(e)}")

    def map_callback(self, msg):
        """Process occupancy grid map for web display"""
        try:
            # Convert occupancy grid to image
            map_array = np.array(msg.data).reshape(msg.info.height, msg.info.width)

            # Convert to 0-255 scale
            map_img = np.zeros_like(map_array, dtype=np.uint8)
            map_img[map_array == 0] = 255    # Free space - white
            map_img[map_array == 100] = 0    # Occupied - black
            map_img[map_array == -1] = 128   # Unknown - gray

            # Encode for web
            _, buffer = cv2.imencode('.png', map_img)
            map_base64 = base64.b64encode(buffer).decode('utf-8')

            self.telemetry['map_data'] = {
                'image': map_base64,
                'resolution': msg.info.resolution,
                'width': msg.info.width,
                'height': msg.info.height,
                'origin': {
                    'x': msg.info.origin.position.x,
                    'y': msg.info.origin.position.y
                }
            }

            socketio.emit('map_update', self.telemetry['map_data'])

        except Exception as e:
            self.get_logger().error(f"Map processing error: {str(e)}")

    def send_velocity_command(self, linear_x, angular_z):
        """Send velocity command to robot"""
        cmd = Twist()
        cmd.linear.x = float(linear_x)
        cmd.angular.z = float(angular_z)
        self.cmd_vel_publisher.publish(cmd)

        self.robot_status['current_speed'] = abs(linear_x)
        self.get_logger().info(f"Velocity command: linear={linear_x}, angular={angular_z}")

    def send_navigation_goal(self, x, y, theta=0.0):
        """Send navigation goal to robot"""
        goal = PoseStamped()
        goal.header.stamp = self.get_clock().now().to_msg()
        goal.header.frame_id = "map"
        goal.pose.position.x = float(x)
        goal.pose.position.y = float(y)
        goal.pose.position.z = 0.0

        # Convert theta to quaternion
        goal.pose.orientation.z = np.sin(theta / 2.0)
        goal.pose.orientation.w = np.cos(theta / 2.0)

        self.goal_publisher.publish(goal)
        self.robot_status['navigation_status'] = 'navigating'
        self.get_logger().info(f"Navigation goal sent: ({x}, {y}, {theta})")

    def emergency_stop(self):
        """Emergency stop the robot"""
        self.send_velocity_command(0.0, 0.0)
        emergency_msg = String()
        emergency_msg.data = "EMERGENCY_STOP"
        self.emergency_publisher.publish(emergency_msg)

        self.robot_status['navigation_status'] = 'stopped'
        self.get_logger().warn("Emergency stop activated!")

# Global node instance
ros_node = None
ros_executor = None

def start_ros_node():
    """Start ROS2 node in separate thread"""
    global ros_node, ros_executor

    rclpy.init()
    ros_node = WebInterfaceNode()
    ros_executor = MultiThreadedExecutor()
    ros_executor.add_node(ros_node)

    # Spin in background
    ros_executor.spin()

# Flask Routes
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/robot/status')
def get_robot_status():
    """Get current robot status"""
    if ros_node:
        ros_node.robot_status['last_update'] = time.time()
        return jsonify(ros_node.robot_status)
    return jsonify({'connected': False})

@app.route('/api/robot/move', methods=['POST'])
def move_robot():
    """Send movement command to robot"""
    data = request.json
    linear_x = data.get('linear_x', 0.0)
    angular_z = data.get('angular_z', 0.0)

    if ros_node:
        ros_node.send_velocity_command(linear_x, angular_z)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Robot not connected'})

@app.route('/api/robot/navigate', methods=['POST'])
def navigate_robot():
    """Send navigation goal to robot"""
    data = request.json
    x = data.get('x', 0.0)
    y = data.get('y', 0.0)
    theta = data.get('theta', 0.0)

    if ros_node:
        ros_node.send_navigation_goal(x, y, theta)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Robot not connected'})

@app.route('/api/robot/stop', methods=['POST'])
def stop_robot():
    """Emergency stop the robot"""
    if ros_node:
        ros_node.emergency_stop()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Robot not connected'})

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
    if ros_node:
        linear = data.get('linear', 0.0)
        angular = data.get('angular', 0.0)
        ros_node.send_velocity_command(linear, angular)
        emit('control_ack', {'status': 'received'})

@socketio.on('request_telemetry')
def handle_telemetry_request():
    """Send current telemetry data"""
    if ros_node and ros_node.telemetry:
        emit('telemetry_update', ros_node.telemetry)

if __name__ == '__main__':
    # Start ROS2 node in background thread
    ros_thread = threading.Thread(target=start_ros_node, daemon=True)
    ros_thread.start()

    # Wait for ROS node to initialize
    time.sleep(2)

    # Start Flask-SocketIO server
    print("Starting LunarBot Web Interface...")
    print("Access dashboard at: http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
