#!/home/alterego-base/miniconda3/envs/ros_yolo/bin/python

import cv2
import pyrealsense2 as rs
import numpy as np
from ultralytics import YOLO
import argparse
import rospy
from std_msgs.msg import String
import os
import time
import threading

print("[DEBUG] Script started - importing modules completed")
print(f"[DEBUG] Using Python from: {os.sys.executable}")

robot_name = os.getenv('ROBOT_NAME', 'default_robot_name')
print(f"[DEBUG] Robot name: {robot_name}")

# --- Inizializzazione ROS (PRIMA di tutto) --
print("[DEBUG] Initializing ROS node...")
rospy.init_node('yolo_detector_node', anonymous=True)
print("[DEBUG] ROS node initialized")
rospy.loginfo("=" * 50)
rospy.loginfo("YOLO Object Detection Node Starting")
rospy.loginfo("=" * 50)

# --- Variabili globali ---
oggetto_da_cercare = None
camera_available = False
pipeline = None
align = None
model = None

def desired_object_callback(msg):
    global oggetto_da_cercare
    # Tratta stringhe vuote come None (ricerca di tutti gli oggetti)
    if msg.data.strip() == "":
        oggetto_da_cercare = None
        rospy.loginfo("[YOLO] ✓ Detecting ALL objects (no filter)")
    else:
        oggetto_da_cercare = msg.data.strip()
        rospy.loginfo(f"[YOLO] ✓ Filtering for specific object: '{oggetto_da_cercare}'")

# Sottoscrizione al topic
rospy.Subscriber(f'/{robot_name}/desired_object', String, desired_object_callback)
rospy.loginfo(f"Subscribed to /{robot_name}/desired_object")

# Carica il modello YOLO
rospy.loginfo("Loading YOLO model...")
try:
    model = YOLO('yolov8n.pt')
    rospy.loginfo("✓ YOLO model loaded successfully")
except Exception as e:
    rospy.logerr(f"✗ Failed to load YOLO model: {e}")

# Configura e avvia la pipeline della RealSense con timeout
rospy.loginfo("Attempting to initialize RealSense camera...")

def init_realsense():
    global pipeline, align, camera_available
    try:
        pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        
        rospy.loginfo("Starting RealSense pipeline...")
        profile = pipeline.start(config)
        align_to = rs.stream.color
        align = rs.align(align_to)
        camera_available = True
        rospy.loginfo("✓ RealSense camera initialized successfully")
    except Exception as e:
        rospy.logerr(f"✗ Failed to initialize RealSense: {e}")
        rospy.logwarn("Node will continue running without camera (for debugging)")
        camera_available = False

# Prova ad inizializzare la camera in un thread separato con timeout
camera_thread = threading.Thread(target=init_realsense)
camera_thread.daemon = True
camera_thread.start()
camera_thread.join(timeout=5.0)  # Timeout di 5 secondi

if not camera_available:
    rospy.logwarn("Camera initialization timed out or failed")
    rospy.logwarn("Node is running in NO-CAMERA mode")

# --- Ciclo Principale ---
rate = rospy.Rate(10)  # 10 Hz
rospy.loginfo("=" * 50)
rospy.loginfo("Node fully initialized - entering main loop")
rospy.loginfo(f"Camera available: {camera_available}")
rospy.loginfo(f"YOLO model loaded: {model is not None}")
rospy.loginfo("=" * 50)

frame_count = 0

try:
    while not rospy.is_shutdown():
        frame_count += 1
        
        if not camera_available:
            # Modalità senza camera - il nodo rimane attivo
            rospy.loginfo_throttle(30, "Node running in NO-CAMERA mode. Waiting for camera...")
            rate.sleep()
            continue
        
        if model is None:
            rospy.logwarn_throttle(30, "YOLO model not loaded. Cannot process frames.")
            rate.sleep()
            continue
            
        try:
            frames = pipeline.wait_for_frames(timeout_ms=1000)
            aligned_frames = align.process(frames)
            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()
            
            if not depth_frame or not color_frame:
                rospy.logwarn_throttle(5, "No frames received from camera")
                rate.sleep()
                continue

            depth_intrinsics = depth_frame.profile.as_video_stream_profile().get_intrinsics()
            color_image = np.asanyarray(color_frame.get_data())
            results = model(color_image, verbose=False)

            detections_count = 0
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    class_name = model.names[int(box.cls)]

                    if oggetto_da_cercare is None or class_name == oggetto_da_cercare:
                        detections_count += 1
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cx = int((x1 + x2) / 2)
                        cy = int((y1 + y2) / 2)
                        distance = depth_frame.get_distance(cx, cy)

                        if distance == 0:
                            continue
                        
                        point_3d = rs.rs2_deproject_pixel_to_point(depth_intrinsics, [cx, cy], distance)
                        x_3d, y_3d, z_3d = point_3d[0], point_3d[1], point_3d[2]
                        
                        label = f"{class_name}"
                        position_text = f"X:{x_3d:.2f} Y:{y_3d:.2f} Z:{z_3d:.2f} m"

                        cv2.rectangle(color_image, (x1, y1), (x2, y2), (255, 0, 255), 2)
                        cv2.putText(color_image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,255), 2)
                        cv2.putText(color_image, position_text, (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
                        cv2.circle(color_image, (cx, cy), 5, (0, 255, 0), -1)

            # Mostra lo stato del filtro nell'angolo superiore sinistro
            if oggetto_da_cercare is None:
                filter_text = "Mode: ALL OBJECTS"
                filter_color = (0, 255, 0)  # Verde
            else:
                filter_text = f"Mode: FILTER '{oggetto_da_cercare}'"
                filter_color = (0, 165, 255)  # Arancione
            
            cv2.rectangle(color_image, (5, 5), (400, 35), (0, 0, 0), -1)  # Sfondo nero
            cv2.putText(color_image, filter_text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, filter_color, 2)

            if frame_count % 100 == 0:  # Log ogni 100 frame
                rospy.loginfo(f"Processing frame {frame_count}, detections: {detections_count}")
            
            cv2.imshow('RealSense YOLOv8 Detection', color_image)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                rospy.loginfo("User requested shutdown (q pressed)")
                break
            
        except RuntimeError as e:
            rospy.logwarn_throttle(5, f"Runtime error in frame processing: {e}")
        
        rate.sleep()

except KeyboardInterrupt:
    rospy.loginfo("Keyboard interrupt received")
except Exception as e:
    rospy.logerr(f"Error in object detection: {e}")
    import traceback
    rospy.logerr(traceback.format_exc())
finally:
    if pipeline is not None and camera_available:
        try:
            pipeline.stop()
            rospy.loginfo("RealSense pipeline stopped")
        except:
            pass
    cv2.destroyAllWindows()
    rospy.loginfo("Object detection node shutting down")