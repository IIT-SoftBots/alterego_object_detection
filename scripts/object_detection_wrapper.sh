#!/bin/bash

# Optional: activate a Python environment if needed
if command -v conda >/dev/null 2>&1; then
	source "$(conda info --base)/etc/profile.d/conda.sh"
	conda activate object_detection_test 2>/dev/null || true
fi

# Source ROS 2 environment (assumes ROS_DISTRO exported or default to humble)
ROS_DISTRO=${ROS_DISTRO:-humble}
source "/opt/ros/${ROS_DISTRO}/setup.bash" || exit 1

# Source workspace if already built
if [ -f "install/setup.bash" ]; then
	source install/setup.bash
fi

# Run the ROS 2 node via entry point
exec ros2 run alterego_object_detection object_detection "$@"
