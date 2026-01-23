#!/usr/bin/env python3
import argparse
import os
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from devices import CameraDevice
import cv2
import supervision as sv
from ultralytics import YOLO


class Object_Detection_Node(Node):
    def __init__(self, device, robot_name='robot_alterego3'):
        super().__init__('object_detector')
        
        # # Initialize the object detector
        self.device = CameraDevice(device=device)

        # model
        self.model = YOLO('yolo26n.pt')
        # image annotators
        self.box_annotator = sv.BoxAnnotator()
        self.label_annotator = sv.LabelAnnotator()
    
        # Create a publisher and subscriber for the Q/A
        self.publisher_ = self.create_publisher(String, robot_name + '/object_detection', 10)

        # Create a timer to call call detect_objects at 20Hz
        self.timer_period = 0.05  # seconds equivalent to 20Hz
        self.timer = self.create_timer(self.timer_period, self.detect_objects)

        self.get_logger().info("Object detector node initialized and timer started")

    def detect_objects(self):
        # Capture frame from the camera device
        print("acquiring frame for detection")
        frame = self.device.get_frame()

        results = self.model(frame)[0]
        detections = sv.Detections.from_ultralytics(results)

        #annotate image with box + labels
        annotated_image = self.box_annotator.annotate(
            scene=frame, detections=detections)
        annotated_image = self.label_annotator.annotate(
            scene=annotated_image, detections=detections)

        #imshow the frame using cv2
        cv2.imshow("Frame", annotated_image)
        cv2.waitKey(1)
        
        # prepare output message
        out_msg = String()
        out_msg.data = ', '.join(detections.class_id.astype(str).tolist())

        # Publish the detected objects
        self.publisher_.publish(out_msg)
        self.get_logger().info(f'Published detected objects: "{out_msg.data}"')


def main(args=None):
    rclpy.init(args=args)
    parser = argparse.ArgumentParser(description="Alterego OBJECT DETECTION Node")
    parser.add_argument('--device', type=str, default='webcam', help='Camera device, e.g., zed, realsense or webcam')
    args, _ = parser.parse_known_args()

    node = Object_Detection_Node(device=args.device, robot_name=os.getenv('ROBOT_NAME', 'robot_alterego3'))

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()