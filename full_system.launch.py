#!/usr/bin/env python3
"""
LunarBot Full System Launch File
Launches all components for complete autonomous operation
"""

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Package directories
    pkg_lunarbot = get_package_share_directory('lunarbot_bringup')
    pkg_gazebo = get_package_share_directory('gazebo_ros')
    pkg_nav2 = get_package_share_directory('nav2_bringup')

    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    world_file = LaunchConfiguration('world', 
                                   default=os.path.join(pkg_lunarbot, 'worlds', 'lunar_environment.world'))
    robot_model = LaunchConfiguration('robot_model', default='lunarbot')

    # Declare launch arguments
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )

    declare_world = DeclareLaunchArgument(
        'world',
        default_value=world_file,
        description='Full path to world file to load'
    )

    # Gazebo simulation
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('gazebo_ros'),
                'launch',
                'gazebo.launch.py'
            ])
        ]),
        launch_arguments={
            'world': world_file,
            'verbose': 'true'
        }.items()
    )

    # Robot state publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': open(os.path.join(pkg_lunarbot, 'urdf', 'lunarbot.urdf')).read()
        }],
        output='screen'
    )

    # Spawn robot in Gazebo
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_lunarbot',
        arguments=['-entity', 'lunarbot',
                  '-topic', 'robot_description',
                  '-x', '0.0', '-y', '0.0', '-z', '0.1'],
        output='screen'
    )

    # SLAM Toolbox
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('slam_toolbox'),
                'launch',
                'online_async_launch.py'
            ])
        ]),
        launch_arguments={
            'slam_params_file': os.path.join(pkg_lunarbot, 'config', 'slam_config.yaml'),
            'use_sim_time': use_sim_time
        }.items()
    )

    # Navigation2
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('nav2_bringup'),
                'launch',
                'navigation_launch.py'
            ])
        ]),
        launch_arguments={
            'params_file': os.path.join(pkg_lunarbot, 'config', 'nav2_params.yaml'),
            'use_sim_time': use_sim_time
        }.items()
    )

    # Perception nodes
    object_detection_node = Node(
        package='lunarbot_perception',
        executable='object_detection_node',
        name='object_detection_node',
        parameters=[{
            'use_sim_time': use_sim_time,
            'model_path': os.path.join(pkg_lunarbot, 'models', 'yolo_lunar.pt'),
            'confidence_threshold': 0.5
        }],
        output='screen'
    )

    semantic_segmentation_node = Node(
        package='lunarbot_perception',
        executable='semantic_segmentation_node',
        name='semantic_segmentation_node',
        parameters=[{
            'use_sim_time': use_sim_time,
            'model_path': os.path.join(pkg_lunarbot, 'models', 'deeplabv3_lunar.pth'),
            'input_topic': '/camera/image_raw',
            'output_topic': '/segmentation_map'
        }],
        output='screen'
    )

    # Web interface node
    web_interface_node = Node(
        package='lunarbot_web_interface',
        executable='web_backend.py',
        name='web_interface_node',
        parameters=[{
            'use_sim_time': use_sim_time,
            'server_port': 5000
        }],
        output='screen'
    )

    # RViz2 for visualization
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', os.path.join(pkg_lunarbot, 'rviz', 'lunarbot.rviz')],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    return LaunchDescription([
        # Declare arguments
        declare_use_sim_time,
        declare_world,

        # Launch components
        gazebo_launch,
        robot_state_publisher,
        spawn_robot,
        slam_launch,
        nav2_launch,
        object_detection_node,
        semantic_segmentation_node,
        web_interface_node,
        rviz_node,
    ])
