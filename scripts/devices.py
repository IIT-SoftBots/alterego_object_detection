# create the CameraDevice class that has the methos frame = self.device.get_frame()
import cv2 as cv



class CameraDevice:
    def __init__(self, device='webcam'):
        #use cap read for get frame
        self.cap = None
        if device == 'webcam':
            self.cap = cv.VideoCapture(0)  # Default webcam
        elif device == 'zed':
            self.cap = 'zed_camera_stream_url'  # Replace with actual ZED camera stream URL
        elif device == 'realsense':
            self.cap = 'realsense_camera_stream_url'  # Replace with actual RealSense camera stream URL
        print(f"CameraDevice initialized with device: {device}")

    def get_frame(self):
        # read from webcam usinf cap read
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to capture frame")
            return None
        
        return frame

    def detect_objects(self, frame):
        # Dummy implementation for object detection
        print(f"Detecting objects in frame: {frame}")
        return ["object1", "object2"]