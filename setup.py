from setuptools import setup

package_name = 'alterego_object_detection'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/object_detection.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sam',
    maintainer_email='sam@todo.todo',
    description='YOLO object detection node for ROS 2 using RealSense',
    license='TODO',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'object_detection = alterego_object_detection.object_detection:main',
        ],
    },
)
