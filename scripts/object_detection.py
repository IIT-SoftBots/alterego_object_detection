import cv2
import pyrealsense2 as rs
import numpy as np
from ultralytics import YOLO
import argparse # 1. Importa la libreria
import rospy
from std_msgs.msg import String
import os



robot_name = os.getenv('ROBOT_NAME', 'default_robot_name')  


# --- Inizializzazione ---

oggetto_da_cercare = None

def desired_object_callback(msg):
    global oggetto_da_cercare
    oggetto_da_cercare = msg.data
    rospy.loginfo(f"[YOLO] Oggetto da cercare aggiornato: {oggetto_da_cercare}")

# Inizializza il nodo ROS
rospy.init_node('yolo_detector_node', anonymous=True)

# Sottoscrizione al topic (es. '/oggetto_desiderato')
rospy.Subscriber(f'/{robot_name}/desired_object', String, desired_object_callback)


# Carica il modello YOLO
model = YOLO('yolov8n.pt')

# Configura e avvia la pipeline della RealSense
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
profile = pipeline.start(config)
align_to = rs.stream.color
align = rs.align(align_to)


# --- Ciclo Principale ---
try:
    while True:
        frames = pipeline.wait_for_frames()
        aligned_frames = align.process(frames)
        depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()
        
        if not depth_frame or not color_frame:
            continue

        depth_intrinsics = depth_frame.profile.as_video_stream_profile().get_intrinsics()
        color_image = np.asanyarray(color_frame.get_data())
        results = model(color_image, verbose=False)

        for r in results:
            boxes = r.boxes
            for box in boxes:
                class_name = model.names[int(box.cls)]

                # 3. Logica di controllo flessibile
                # Se 'oggetto_da_cercare' è None (default) OPPURE se il nome della classe corrisponde, allora procedi.
                if oggetto_da_cercare is None or class_name == oggetto_da_cercare:
                    
                    # Tutto il codice che avevi prima rimane qui dentro, invariato
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    distance = depth_frame.get_distance(cx, cy)

                    if distance == 0:
                        continue
                    
                    point_3d = rs.rs2_deproject_pixel_to_point(depth_intrinsics, [cx, cy], distance)
                    x_3d, y_3d, z_3d = point_3d[0], point_3d[1], point_3d[2]
                    
                    label = f"{class_name}" # Usiamo la variabile per mostrare il nome corretto
                    position_text = f"X:{x_3d:.2f} Y:{y_3d:.2f} Z:{z_3d:.2f} m"

                    cv2.rectangle(color_image, (x1, y1), (x2, y2), (255, 0, 255), 2)
                    cv2.putText(color_image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,255), 2)
                    cv2.putText(color_image, position_text, (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
                    cv2.circle(color_image, (cx, cy), 5, (0, 255, 0), -1)

        cv2.imshow('RealSense YOLOv8 Detection', color_image)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    pipeline.stop()
    cv2.destroyAllWindows()