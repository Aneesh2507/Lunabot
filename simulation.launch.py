#!/usr/bin/env python3
"""
LunarBot Simulation Launch File
Launches Gazebo simulation with lunar terrain
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Package directory
    pkg_lunarbot = get_package_share_directory('lunarbot_bringup')

    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    world_file = LaunchConfiguration('world', 
                                   default=os.path.join(pkg_lunarbot, 'worlds', 'lunar_south_pole.world'))

    # Gazebo server
    gazebo_server = ExecuteProcess(
        cmd=['gzserver', world_file, '--verbose'],
        output='screen'
    )

    # Gazebo client
    gazebo_client = ExecuteProcess(
        cmd=['gzclient'],
        output='screen'
    )

    # Robot description
    robot_description = open(os.path.join(pkg_lunarbot, 'urdf', 'lunarbot.urdf')).read()

    # Robot state publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': use_sim_time
        }]
    )

    # Spawn robot
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'lunarbot',
            '-topic', 'robot_description',
            '-x', '0.0', '-y', '0.0', '-z', '0.5',
            '-R', '0.0', '-P', '0.0', '-Y', '0.0'
        ],
        output='screen'
    )

    # Terrain generator (loads DEM data)
    terrain_generator = Node(
        package='lunarbot_simulation',
        executable='terrain_generator.py',
        parameters=[{
            'dem_file': os.path.join(pkg_lunarbot, 'data', 'lunar_south_pole_dem.tif'),
            'texture_file': os.path.join(pkg_lunarbot, 'data', 'lunar_regolith_texture.jpg'),
            'scale_factor': 1.0,
            'use_sim_time': use_sim_time
        }],
        output='screen'
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('world', default_value=world_file),

        gazebo_server,
        gazebo_client,
        robot_state_publisher,
        spawn_robot,
        terrain_generator,
    ])
