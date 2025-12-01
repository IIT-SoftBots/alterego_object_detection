#!/bin/bash

# Attiva l'ambiente conda ros_yolo
source /home/alterego-base/miniconda3/bin/activate ros_yolo

# Source ROS environment
source /opt/ros/noetic/setup.bash
source /home/alterego-base/catkin_ws/devel/setup.bash

# Esegui lo script Python con l'interprete dell'ambiente ros_yolo
exec /home/alterego-base/miniconda3/envs/ros_yolo/bin/python /home/alterego-base/catkin_ws/src/AlterEGO_v2/utils/alterego_object_detection/scripts/object_detection.py "$@"
