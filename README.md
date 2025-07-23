# Alterego Object Detection

**Alterego Object Detection** is a ROS-compatible object detection package that leverages **YOLOv8** (Ultralytics) to identify objects in real time. In addition to standard object detection, the package extracts the **3D relative position** of the detected objects with respect to an **Intel RealSense** camera.

## Features

- Real-time object detection using YOLOv8 (Ultralytics)
- Extraction of 3D coordinates (X, Y, Z) of detected objects relative to the camera
- Support for Intel RealSense RGB-D cameras
- ROS integration for easy use in robotic applications

## Requirements

- Python 3
- ROS Noetic
- [Ultralytics YOLOv8](https://docs.ultralytics.com/)
- Intel RealSense SDK (`pyrealsense2`)
- OpenCV
- NumPy

You can install the required Python packages directly with `create_env.sh`