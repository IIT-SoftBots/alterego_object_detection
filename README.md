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

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)
## Create conda env
These four commands download the latest 64-bit version of the Linux installer, rename it to a shorter file name, silently install, and then delete the installer:
```
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm ~/miniconda3/miniconda.sh
```
After installing, close and reopen your terminal application or refresh it by running the following command:
```
source ~/miniconda3/bin/activate
```
To initialize conda on the current shell
, run the following command:
```
conda init
```
Then deactivate the autostart activation of the base env
```
conda config --set auto_activate_base false
```

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

## Object Detection
If you want to use the face tracking and recognition, lets create the virtual env from the bash file ```create_env.sh``` inside .

(optional) Be sure to accept Conda's ToS on first Conda use:
```
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
```

Create Conda env and build packages:
```
cd ~/(your_catkin_path)/src/AlterEgo_v2/utils/alterego_object_dection
chmod +x create_env.sh # To make executable the script
./create_env.sh
cd ~/(your_catkin_path)
catkin build alterego_object_detection
```


![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

## Build the entire solution
Move to source dir `cd ~/(your_catkin_path)/`. Then
```
catkin build
conda deactivate
```
