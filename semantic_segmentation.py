#!/usr/bin/env python3
"""
LunarBot Semantic Segmentation Module
Uses DeepLabV3 for pixel-level terrain classification
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Header
from cv_bridge import CvBridge
import cv2
import torch
import torchvision.transforms as transforms
from torchvision.models.segmentation import deeplabv3_resnet50
import numpy as np

class SemanticSegmentationNode(Node):
    def __init__(self):
        super().__init__('semantic_segmentation_node')

        # Initialize DeepLabV3 model
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = deeplabv3_resnet50(pretrained=True)

        # Modify for lunar terrain classes
        self.num_classes = 6  # background, rock, sand, crater, safe_path, obstacle
        self.model.classifier[4] = torch.nn.Conv2d(256, self.num_classes, 1)
        self.model.aux_classifier[4] = torch.nn.Conv2d(256, self.num_classes, 1)

        self.model.to(self.device)
        self.model.eval()

        # Image preprocessing
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((512, 512)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])

        # ROS2 setup
        self.bridge = CvBridge()
        self.image_subscription = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10)
        self.segmentation_publisher = self.create_publisher(
            Image, '/segmentation_map', 10)
        self.drivability_publisher = self.create_publisher(
            Image, '/drivability_map', 10)

        # Class colors for visualization
        self.class_colors = np.array([
            [0, 0, 0],       # background - black
            [128, 64, 128],  # rock - purple
            [244, 164, 96],  # sand - sandy brown
            [70, 70, 70],    # crater - dark gray
            [0, 255, 0],     # safe_path - green
            [255, 0, 0]      # obstacle - red
        ], dtype=np.uint8)

        self.get_logger().info("Semantic Segmentation Node initialized")

    def image_callback(self, msg):
        """Process camera images for semantic segmentation"""
        try:
            # Convert ROS image to OpenCV
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            original_size = cv_image.shape[:2]

            # Preprocess image
            input_tensor = self.transform(cv_image).unsqueeze(0).to(self.device)

            # Run segmentation
            with torch.no_grad():
                output = self.model(input_tensor)['out']
                predictions = torch.softmax(output, dim=1)
                segmentation = torch.argmax(predictions, dim=1).squeeze().cpu().numpy()

            # Resize back to original dimensions
            segmentation = cv2.resize(segmentation.astype(np.uint8), 
                                    (original_size[1], original_size[0]), 
                                    interpolation=cv2.INTER_NEAREST)

            # Create colored segmentation map
            colored_seg = self.colorize_segmentation(segmentation)

            # Create drivability map
            drivability_map = self.create_drivability_map(segmentation)

            # Publish segmentation map
            seg_msg = self.bridge.cv2_to_imgmsg(colored_seg, "bgr8")
            seg_msg.header = msg.header
            self.segmentation_publisher.publish(seg_msg)

            # Publish drivability map
            driv_msg = self.bridge.cv2_to_imgmsg(drivability_map, "mono8")
            driv_msg.header = msg.header
            self.drivability_publisher.publish(driv_msg)

            # Log terrain analysis
            self.analyze_terrain(segmentation)

        except Exception as e:
            self.get_logger().error(f"Segmentation error: {str(e)}")

    def colorize_segmentation(self, segmentation):
        """Convert segmentation map to colored visualization"""
        colored = np.zeros((segmentation.shape[0], segmentation.shape[1], 3), dtype=np.uint8)
        for class_id in range(self.num_classes):
            mask = segmentation == class_id
            colored[mask] = self.class_colors[class_id]
        return colored

    def create_drivability_map(self, segmentation):
        """Create binary drivability map for path planning"""
        # Safe classes: background, sand, safe_path
        safe_classes = [0, 2, 4]
        drivability = np.zeros_like(segmentation, dtype=np.uint8)

        for class_id in safe_classes:
            drivability[segmentation == class_id] = 255

        # Apply morphological operations to clean up
        kernel = np.ones((5, 5), np.uint8)
        drivability = cv2.morphologyEx(drivability, cv2.MORPH_CLOSE, kernel)
        drivability = cv2.morphologyEx(drivability, cv2.MORPH_OPEN, kernel)

        return drivability

    def analyze_terrain(self, segmentation):
        """Analyze terrain composition for navigation decisions"""
        total_pixels = segmentation.size
        class_names = ['background', 'rock', 'sand', 'crater', 'safe_path', 'obstacle']

        terrain_stats = {}
        for i, class_name in enumerate(class_names):
            pixel_count = np.sum(segmentation == i)
            percentage = (pixel_count / total_pixels) * 100
            terrain_stats[class_name] = percentage

        # Log significant terrain features
        if terrain_stats['obstacle'] > 10:
            self.get_logger().warn(f"High obstacle density: {terrain_stats['obstacle']:.1f}%")
        if terrain_stats['safe_path'] > 30:
            self.get_logger().info(f"Good traversable terrain: {terrain_stats['safe_path']:.1f}%")

def main(args=None):
    rclpy.init(args=args)
    node = SemanticSegmentationNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
