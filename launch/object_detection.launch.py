from launch import LaunchDescription
from launch.substitutions import EnvironmentVariable, LaunchConfiguration
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node


def generate_launch_description():
    robot_name_env = EnvironmentVariable(name='ROBOT_NAME', default_value='default_robot_name')
    robot_name = LaunchConfiguration('robot_name', default=robot_name_env)

    object_detection_node = Node(
        package='alterego_object_detection',
        executable='object_detection',
        name='object_detection',
        namespace=robot_name,
        output='screen',
    )

    return LaunchDescription([
        object_detection_node
    ])
