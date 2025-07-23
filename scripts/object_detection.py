import cv2
import pyrealsense2 as rs
import numpy as np
from ultralytics import YOLO

# --- Inizializzazione ---
# Carica il modello YOLO
model = YOLO('yolov8n.pt')

# Configura e avvia la pipeline della RealSense
pipeline = rs.pipeline()
config = rs.config()

# Abilita lo streaming di profondità e colore
# Assicurati che le risoluzioni corrispondano a quelle supportate dalla tua camera
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# Avvia lo streaming
profile = pipeline.start(config)

# Crea un oggetto 'align' per allineare il frame di profondità a quello a colori
align_to = rs.stream.color
align = rs.align(align_to)


# --- Ciclo Principale ---
try:
    while True:
        # Attendi una coppia di frame coerenti: profondità e colore
        frames = pipeline.wait_for_frames()
        aligned_frames = align.process(frames)
        
        depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()
        
        if not depth_frame or not color_frame:
            continue

        # Ottieni i parametri intrinseci della camera (necessari per la deproiezione)
        depth_intrinsics = depth_frame.profile.as_video_stream_profile().get_intrinsics()

        # Converti i frame in array numpy
        color_image = np.asanyarray(color_frame.get_data())

        # Esegui il rilevamento YOLO
        results = model(color_image, verbose=False) # verbose=False per pulire l'output

        # Itera sui risultati
        for r in results:
            boxes = r.boxes
            for box in boxes:
                # Estrai le coordinate del bounding box
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                # Calcola il centro del bounding box
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)

                # Ottieni la distanza (profondità) del pixel centrale
                distance = depth_frame.get_distance(cx, cy)

                # Se il punto è troppo lontano o troppo vicino, ignoralo
                if distance == 0:
                    continue
                
                # Calcola le coordinate 3D reali usando la deproiezione
                point_3d = rs.rs2_deproject_pixel_to_point(depth_intrinsics, [cx, cy], distance)
                
                # Estrai le coordinate X, Y, Z
                x_3d, y_3d, z_3d = point_3d[0], point_3d[1], point_3d[2]
                
                # Prepara il testo da visualizzare
                label = f"{model.names[int(box.cls)]}"
                position_text = f"X:{x_3d:.2f} Y:{y_3d:.2f} Z:{z_3d:.2f} m"

                # Disegna il bounding box e il testo sull'immagine a colori
                cv2.rectangle(color_image, (x1, y1), (x2, y2), (255, 0, 255), 2)
                cv2.putText(color_image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,255), 2)
                cv2.putText(color_image, position_text, (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
                # Disegna un cerchio al centro per verifica
                cv2.circle(color_image, (cx, cy), 5, (0, 255, 0), -1)

        # Mostra l'immagine
        cv2.imshow('RealSense YOLOv8 Detection', color_image)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Cleanup
    pipeline.stop()
    cv2.destroyAllWindows()