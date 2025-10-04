#!/usr/bin/env python3
"""
LunarBot Object Detection Module
Uses YOLOv8 for real-time detection of lunar surface features
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseArray, Pose
from cv_bridge import CvBridge
import cv2
import torch
from ultralytics import YOLO
import numpy as np

class ObjectDetectionNode(Node):
    def __init__(self):
        super().__init__('object_detection_node')

        # Initialize YOLO model
        self.model = YOLO('yolov8n.pt')  # Can be fine-tuned for lunar terrain
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model.to(self.device)

        # ROS2 setup
        self.bridge = CvBridge()
        self.image_subscription = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10)
        self.detection_publisher = self.create_publisher(
            PoseArray, '/detections', 10)

        # Lunar object classes
        self.lunar_classes = {
            'rock': 0,
            'crater': 1,
            'boulder': 2,
            'pothole': 3,
            'hill': 4
        }

        self.get_logger().info("Object Detection Node initialized")

    def image_callback(self, msg):
        """Process camera images for object detection"""
        try:
            # Convert ROS image to OpenCV
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")

            # Run YOLO detection
            results = self.model(cv_image, conf=0.5, verbose=False)

            # Process detections
            detections = PoseArray()
            detections.header.stamp = self.get_clock().now().to_msg()
            detections.header.frame_id = "camera_frame"

            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Extract detection data
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = box.conf[0].cpu().numpy()
                        class_id = int(box.cls[0].cpu().numpy())

                        # Convert to robot pose (simplified)
                        pose = Pose()
                        pose.position.x = float((x1 + x2) / 2 / cv_image.shape[1])
                        pose.position.y = float((y1 + y2) / 2 / cv_image.shape[0])
                        pose.position.z = float(confidence)

                        detections.poses.append(pose)

                        # Draw bounding box for visualization
                        cv2.rectangle(cv_image, (int(x1), int(y1)), (int(x2), int(y2)), 
                                    (0, 255, 0), 2)
                        cv2.putText(cv_image, f'Class: {class_id}, Conf: {confidence:.2f}',
                                  (int(x1), int(y1-10)), cv2.FONT_HERSHEY_SIMPLEX, 
                                  0.5, (0, 255, 0), 2)

            # Publish detections
            self.detection_publisher.publish(detections)

            # Optional: publish annotated image
            # self.publish_annotated_image(cv_image)

        except Exception as e:
            self.get_logger().error(f"Detection error: {str(e)}")

def main(args=None):
    rclpy.init(args=args)
    node = ObjectDetectionNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
