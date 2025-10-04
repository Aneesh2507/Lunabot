#!/usr/bin/env python3
"""
LunarBot Object Detection Demo
Simplified version without ROS2 dependencies
"""

import cv2
import numpy as np
import time
import random

class ObjectDetectionDemo:
    def __init__(self):
        print("Initializing LunarBot Object Detection Demo...")
        
        # Simulate lunar object classes
        self.lunar_classes = {
            'rock': 0,
            'crater': 1,
            'boulder': 2,
            'pothole': 3,
            'hill': 4
        }
        
        self.detection_count = 0
        
    def generate_simulated_image(self):
        """Generate a simulated lunar terrain image"""
        # Create base lunar surface
        img = np.random.randint(80, 120, (480, 640, 3), dtype=np.uint8)
        
        # Add lunar features
        features = []
        
        # Add rocks
        for _ in range(random.randint(3, 8)):
            x, y = random.randint(50, 590), random.randint(50, 430)
            size = random.randint(15, 40)
            cv2.circle(img, (x, y), size, (40, 40, 40), -1)
            features.append(('rock', x, y, size))
        
        # Add craters
        for _ in range(random.randint(1, 3)):
            x, y = random.randint(100, 540), random.randint(100, 380)
            size = random.randint(30, 80)
            cv2.circle(img, (x, y), size, (20, 20, 20), -1)
            cv2.circle(img, (x, y), size//2, (60, 60, 60), -1)
            features.append(('crater', x, y, size))
        
        # Add safe paths
        for _ in range(random.randint(2, 5)):
            x, y = random.randint(50, 590), random.randint(50, 430)
            size = random.randint(20, 50)
            cv2.circle(img, (x, y), size, (160, 160, 160), -1)
            features.append(('safe_path', x, y, size))
        
        return img, features
    
    def simulate_detection(self, img, features):
        """Simulate object detection on the image"""
        detections = []
        
        for feature_type, x, y, size in features:
            # Simulate detection confidence
            confidence = random.uniform(0.6, 0.95)
            
            # Create bounding box
            x1 = max(0, x - size)
            y1 = max(0, y - size)
            x2 = min(img.shape[1], x + size)
            y2 = min(img.shape[0], y + size)
            
            detections.append({
                'class': feature_type,
                'confidence': confidence,
                'bbox': (x1, y1, x2, y2),
                'center': (x, y)
            })
        
        return detections
    
    def draw_detections(self, img, detections):
        """Draw detection results on image"""
        annotated_img = img.copy()
        
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            class_name = detection['class']
            confidence = detection['confidence']
            
            # Choose color based on class
            if class_name == 'rock':
                color = (0, 255, 0)  # Green
            elif class_name == 'crater':
                color = (0, 0, 255)  # Red
            elif class_name == 'safe_path':
                color = (255, 0, 0)  # Blue
            else:
                color = (255, 255, 0)  # Yellow
            
            # Draw bounding box
            cv2.rectangle(annotated_img, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            
            # Draw label
            label = f'{class_name}: {confidence:.2f}'
            cv2.putText(annotated_img, label, (int(x1), int(y1-10)), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return annotated_img
    
    def run_detection_demo(self, num_frames=10):
        """Run object detection demo"""
        print(f"Running detection demo for {num_frames} frames...")
        print("Press 'q' to quit, 's' to save current frame")
        
        for frame_num in range(num_frames):
            # Generate simulated image
            img, features = self.generate_simulated_image()
            
            # Run detection
            detections = self.simulate_detection(img, features)
            
            # Draw results
            annotated_img = self.draw_detections(img, detections)
            
            # Display results
            cv2.imshow('LunarBot Object Detection Demo', annotated_img)
            
            # Print detection results
            print(f"\nFrame {frame_num + 1}:")
            print(f"Detected {len(detections)} objects:")
            for det in detections:
                print(f"  - {det['class']}: {det['confidence']:.2f} at {det['center']}")
            
            self.detection_count += len(detections)
            
            # Handle key presses
            key = cv2.waitKey(1000) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                filename = f'lunarbot_detection_frame_{frame_num}.jpg'
                cv2.imwrite(filename, annotated_img)
                print(f"Saved frame as {filename}")
            
            time.sleep(0.5)  # Simulate processing time
        
        cv2.destroyAllWindows()
        print(f"\nDetection demo completed!")
        print(f"Total detections: {self.detection_count}")
        print(f"Average detections per frame: {self.detection_count/num_frames:.1f}")

def main():
    """Main function"""
    print("=" * 60)
    print("🚀 LunarBot Object Detection Demo")
    print("=" * 60)
    print("This demo simulates object detection on lunar terrain")
    print("Features detected: rocks, craters, safe paths")
    print("=" * 60)
    
    # Initialize detection system
    detector = ObjectDetectionDemo()
    
    # Run demo
    detector.run_detection_demo(num_frames=15)
    
    print("\nDemo completed successfully!")
    print("To run the full system with ROS2, install ROS2 Humble and run:")
    print("  ros2 launch lunarbot_bringup full_system.launch.py")

if __name__ == '__main__':
    main()
