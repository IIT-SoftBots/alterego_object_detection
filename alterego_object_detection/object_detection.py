import os
import threading
import time
from pathlib import Path

import cv2
import numpy as np

try:
    import pyrealsense2 as rs  # Optional when using webcam
except ImportError:
    rs = None

from ultralytics import YOLO

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from ament_index_python.packages import get_package_share_directory


class YoloDetectorNode(Node):
    def __init__(self):
        super().__init__('yolo_detector_node')

        self.get_logger().info('=' * 50)
        self.get_logger().info('YOLO Object Detection Node Starting (ROS 2)')
        self.get_logger().info('=' * 50)

        self.robot_name = os.getenv('ROBOT_NAME', 'default_robot_name')
        self.get_logger().info(f'Robot name: {self.robot_name}')

        # Parameters
        self.declare_parameter('use_webcam', False)
        self.declare_parameter('webcam_device', 0)
        self.declare_parameter('webcam_width', 640)
        self.declare_parameter('webcam_height', 480)
        self.declare_parameter('weights_path', '')

        self.use_webcam = bool(self.get_parameter('use_webcam').get_parameter_value().bool_value)
        self.webcam_device = int(self.get_parameter('webcam_device').get_parameter_value().integer_value)
        self.webcam_width = int(self.get_parameter('webcam_width').get_parameter_value().integer_value)
        self.webcam_height = int(self.get_parameter('webcam_height').get_parameter_value().integer_value)
        self.user_weights_path = self.get_parameter('weights_path').get_parameter_value().string_value

        # State
        self.desired_object = None
        self.camera_available = False
        self.pipeline = None
        self.align = None
        self.model = None
        self.cap = None
        self.frame_count = 0

        # Subscribe to desired object topic
        topic = f'/{self.robot_name}/desired_object'
        self.subscription = self.create_subscription(
            String, topic, self.desired_object_callback, 10
        )
        self.get_logger().info(f'Subscribed to {topic}')

        # Load YOLO model (from installed share directory or user path)
        try:
            if self.user_weights_path:
                weights_path = self.user_weights_path
            else:
                share_dir = get_package_share_directory('alterego_object_detection')
                # Default packaged path
                default_packaged = os.path.join(share_dir, 'models', 'weights', 'yolov8n.pt')
                # Fallback legacy path if user moved weights
                legacy_path = os.path.join(share_dir, 'weights', 'yolov8n.pt')
                weights_path = default_packaged if os.path.exists(default_packaged) else legacy_path
            self.model = YOLO(weights_path)
            self.get_logger().info('✓ YOLO model loaded successfully')
        except Exception as e:
            self.get_logger().error(f'✗ Failed to load YOLO model: {e}')

        # Initialize camera source
        if self.use_webcam:
            self.get_logger().info(f'Initializing webcam device {self.webcam_device} at {self.webcam_width}x{self.webcam_height} ...')
            try:
                self.cap = cv2.VideoCapture(self.webcam_device)
                # Set resolution if supported
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.webcam_width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.webcam_height)
                if not self.cap.isOpened():
                    raise RuntimeError('Webcam could not be opened')
                self.camera_available = True
                self.get_logger().info('✓ Webcam initialized successfully')
            except Exception as e:
                self.get_logger().error(f'✗ Failed to initialize webcam: {e}')
                self.get_logger().warn('Node will continue running without camera (for debugging)')
                self.camera_available = False
        else:
            self.get_logger().info('Attempting to initialize RealSense camera...')
            if rs is None:
                self.get_logger().error('pyrealsense2 not available; cannot use RealSense. Set use_webcam:=true to use a standard camera.')
            
            def init_realsense():
                try:
                    if rs is None:
                        raise RuntimeError('pyrealsense2 module not found')
                    self.pipeline = rs.pipeline()
                    config = rs.config()
                    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
                    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
                    self.get_logger().info('Starting RealSense pipeline...')
                    profile = self.pipeline.start(config)
                    align_to = rs.stream.color
                    self.align = rs.align(align_to)
                    self.camera_available = True
                    self.get_logger().info('✓ RealSense camera initialized successfully')
                except Exception as e:
                    self.get_logger().error(f'✗ Failed to initialize RealSense: {e}')
                    self.get_logger().warn('Node will continue running without camera (for debugging)')
                    self.camera_available = False

            camera_thread = threading.Thread(target=init_realsense, daemon=True)
            camera_thread.start()
            camera_thread.join(timeout=5.0)

            if not self.camera_available:
                self.get_logger().warn('Camera initialization timed out or failed')
                self.get_logger().warn('Node is running in NO-CAMERA mode')

        # Main processing loop at 10 Hz
        self.timer = self.create_timer(0.1, self.process_frame)
        self.get_logger().info('=' * 50)
        self.get_logger().info('Node fully initialized - entering main loop')
        self.get_logger().info(f'Camera available: {self.camera_available}')
        self.get_logger().info(f'YOLO model loaded: {self.model is not None}')
        self.get_logger().info('=' * 50)

    def desired_object_callback(self, msg: String):
        data = msg.data.strip()
        if data == '':
            self.desired_object = None
            self.get_logger().info('✓ Detecting ALL objects (no filter)')
        else:
            self.desired_object = data
            self.get_logger().info(f"✓ Filtering for specific object: '{self.desired_object}'")

    def process_frame(self):
        self.frame_count += 1

        if not self.camera_available:
            if self.frame_count % 300 == 0:
                self.get_logger().info('Node running in NO-CAMERA mode. Waiting for camera...')
            return

        if self.model is None:
            if self.frame_count % 300 == 0:
                self.get_logger().warn('YOLO model not loaded. Cannot process frames.')
            return

        try:
            if self.use_webcam:
                ret, color_image = self.cap.read()
                if not ret or color_image is None:
                    if self.frame_count % 50 == 0:
                        self.get_logger().warn('No frames received from webcam')
                    return
                depth_frame = None
                depth_intrinsics = None
            else:
                frames = self.pipeline.wait_for_frames(timeout_ms=1000)
                aligned_frames = self.align.process(frames)
                depth_frame = aligned_frames.get_depth_frame()
                color_frame = aligned_frames.get_color_frame()

                if not depth_frame or not color_frame:
                    if self.frame_count % 50 == 0:
                        self.get_logger().warn('No frames received from camera')
                    return

                depth_intrinsics = depth_frame.profile.as_video_stream_profile().get_intrinsics()
                color_image = np.asanyarray(color_frame.get_data())

            results = self.model(color_image, verbose=False)

            detections_count = 0
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    class_name = self.model.names[int(box.cls)]

                    if self.desired_object is None or class_name == self.desired_object:
                        detections_count += 1
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cx = int((x1 + x2) / 2)
                        cy = int((y1 + y2) / 2)
                        label = f"{class_name}"

                        if not self.use_webcam and depth_frame is not None and depth_intrinsics is not None:
                            distance = depth_frame.get_distance(cx, cy)
                            if distance == 0:
                                continue
                            point_3d = rs.rs2_deproject_pixel_to_point(depth_intrinsics, [cx, cy], distance)
                            x_3d, y_3d, z_3d = point_3d[0], point_3d[1], point_3d[2]
                            position_text = f"X:{x_3d:.2f} Y:{y_3d:.2f} Z:{z_3d:.2f} m"
                        else:
                            position_text = None

                        cv2.rectangle(color_image, (x1, y1), (x2, y2), (255, 0, 255), 2)
                        cv2.putText(color_image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)
                        if position_text:
                            cv2.putText(color_image, position_text, (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                        cv2.circle(color_image, (cx, cy), 5, (0, 255, 0), -1)

            # Filter status overlay
            if self.desired_object is None:
                filter_text = 'Mode: ALL OBJECTS'
                filter_color = (0, 255, 0)
            else:
                filter_text = f"Mode: FILTER '{self.desired_object}'"
                filter_color = (0, 165, 255)

            cv2.rectangle(color_image, (5, 5), (400, 35), (0, 0, 0), -1)
            cv2.putText(color_image, filter_text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, filter_color, 2)

            if self.frame_count % 100 == 0:
                self.get_logger().info(f'Processing frame {self.frame_count}, detections: {detections_count}')

            title = 'YOLOv8 Detection (Webcam)' if self.use_webcam else 'YOLOv8 Detection (RealSense)'
            cv2.imshow(title, color_image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.get_logger().info('User requested shutdown (q pressed)')
                self.shutdown()

        except RuntimeError as e:
            if self.frame_count % 50 == 0:
                self.get_logger().warn(f'Runtime error in frame processing: {e}')

    def shutdown(self):
        try:
            if not self.use_webcam:
                if self.pipeline is not None and self.camera_available:
                    self.pipeline.stop()
                    self.get_logger().info('RealSense pipeline stopped')
            else:
                if self.cap is not None:
                    self.cap.release()
                    self.get_logger().info('Webcam released')
        except Exception:
            pass
        cv2.destroyAllWindows()
        self.get_logger().info('Object detection node shutting down')
        try:
            rclpy.shutdown()
        except Exception:
            pass


def main():
    rclpy.init()
    node = YoloDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Keyboard interrupt received')
    finally:
        node.shutdown()
