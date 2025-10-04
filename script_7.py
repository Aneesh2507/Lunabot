# 7. ROS2 Launch Files and Configuration

# Main system launch file
main_launch_content = '''#!/usr/bin/env python3
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
'''

# Simulation-only launch file
simulation_launch_content = '''#!/usr/bin/env python3
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
'''

# Navigation configuration
nav2_config_content = '''# Nav2 Configuration for LunarBot
# Optimized for lunar terrain navigation

amcl:
  ros__parameters:
    use_sim_time: True
    alpha1: 0.2
    alpha2: 0.2
    alpha3: 0.2
    alpha4: 0.2
    alpha5: 0.2
    base_frame_id: "base_footprint"
    beam_skip_distance: 0.5
    beam_skip_error_threshold: 0.9
    beam_skip_threshold: 0.3
    do_beamskip: false
    global_frame_id: "map"
    lambda_short: 0.1
    laser_likelihood_max_dist: 2.0
    laser_max_range: 100.0
    laser_min_range: -1.0
    laser_model_type: "likelihood_field"
    max_beams: 60
    max_particles: 2000
    min_particles: 500
    odom_frame_id: "odom"
    pf_err: 0.05
    pf_z: 0.99
    recovery_alpha_fast: 0.0
    recovery_alpha_slow: 0.0
    resample_interval: 1
    robot_model_type: "nav2_amcl::DifferentialMotionModel"
    save_pose_rate: 0.5
    sigma_hit: 0.2
    tf_broadcast: true
    transform_tolerance: 1.0
    update_min_a: 0.2
    update_min_d: 0.25
    z_hit: 0.5
    z_max: 0.05
    z_rand: 0.5
    z_short: 0.05
    scan_topic: scan

bt_navigator:
  ros__parameters:
    use_sim_time: True
    global_frame: map
    robot_base_frame: base_link
    odom_topic: /odom
    bt_loop_duration: 10
    default_server_timeout: 20
    wait_for_service_timeout: 1000
    action_server_result_timeout: 900.0
    navigators: ["navigate_to_pose", "navigate_through_poses"]
    navigate_to_pose:
      plugin: "nav2_bt_navigator::NavigateToPoseNavigator"
    navigate_through_poses:
      plugin: "nav2_bt_navigator::NavigateThroughPosesNavigator"
    # Custom behavior tree for lunar navigation
    default_nav_to_pose_bt_xml: "/workspace/config/navigate_to_pose_bt.xml"
    default_nav_through_poses_bt_xml: "/workspace/config/navigate_through_poses_bt.xml"

controller_server:
  ros__parameters:
    use_sim_time: True
    controller_frequency: 20.0
    min_x_velocity_threshold: 0.001
    min_y_velocity_threshold: 0.5
    min_theta_velocity_threshold: 0.001
    failure_tolerance: 0.3
    progress_checker_plugin: "progress_checker"
    goal_checker_plugins: ["general_goal_checker"]
    controller_plugins: ["FollowPath"]

    # Progress checker parameters
    progress_checker:
      plugin: "nav2_controller::SimpleProgressChecker"
      required_movement_radius: 0.5
      movement_time_allowance: 10.0
    
    # Goal checker parameters
    general_goal_checker:
      stateful: True
      plugin: "nav2_controller::SimpleGoalChecker"
      xy_goal_tolerance: 0.25
      yaw_goal_tolerance: 0.25
    
    # DWB controller parameters (optimized for lunar terrain)
    FollowPath:
      plugin: "dwb_core::DWBLocalPlanner"
      debug_trajectory_details: True
      min_vel_x: 0.0
      min_vel_y: 0.0
      max_vel_x: 0.8
      max_vel_y: 0.0
      max_vel_theta: 1.0
      min_speed_xy: 0.0
      max_speed_xy: 0.8
      min_speed_theta: 0.0
      acc_lim_x: 2.5
      acc_lim_y: 0.0
      acc_lim_theta: 3.2
      decel_lim_x: -2.5
      decel_lim_y: 0.0
      decel_lim_theta: -3.2
      vx_samples: 20
      vy_samples: 5
      vtheta_samples: 20
      sim_time: 1.7
      linear_granularity: 0.05
      angular_granularity: 0.025
      transform_tolerance: 0.2
      xy_goal_tolerance: 0.25
      trans_stopped_velocity: 0.25
      short_circuit_trajectory_evaluation: True
      stateful: True
      critics: ["RotateToGoal", "Oscillation", "BaseObstacle", "GoalAlign", "PathAlign", "PathDist", "GoalDist"]
      BaseObstacle.scale: 0.02
      PathAlign.scale: 32.0
      PathAlign.forward_point_distance: 0.1
      GoalAlign.scale: 24.0
      GoalAlign.forward_point_distance: 0.1
      PathDist.scale: 32.0
      GoalDist.scale: 24.0
      RotateToGoal.scale: 32.0
      RotateToGoal.slowing_factor: 5.0
      RotateToGoal.lookahead_time: -1.0

local_costmap:
  local_costmap:
    ros__parameters:
      update_frequency: 5.0
      publish_frequency: 2.0
      global_frame: odom
      robot_base_frame: base_link
      use_sim_time: True
      rolling_window: true
      width: 3
      height: 3
      resolution: 0.05
      robot_radius: 0.22
      plugins: ["voxel_layer", "inflation_layer"]
      inflation_layer:
        plugin: "nav2_costmap_2d::InflationLayer"
        cost_scaling_factor: 3.0
        inflation_radius: 0.55
      voxel_layer:
        plugin: "nav2_costmap_2d::VoxelLayer"
        enabled: True
        publish_voxel_map: True
        origin_z: 0.0
        z_resolution: 0.05
        z_voxels: 16
        max_obstacle_height: 2.0
        mark_threshold: 0
        observation_sources: scan
        scan:
          topic: /scan
          max_obstacle_height: 2.0
          clearing: True
          marking: True
          data_type: "LaserScan"
          raytrace_max_range: 3.0
          raytrace_min_range: 0.0
          obstacle_max_range: 2.5
          obstacle_min_range: 0.0
      static_layer:
        plugin: "nav2_costmap_2d::StaticLayer"
        map_subscribe_transient_local: True
      always_send_full_costmap: True

global_costmap:
  global_costmap:
    ros__parameters:
      update_frequency: 1.0
      publish_frequency: 1.0
      global_frame: map
      robot_base_frame: base_link
      use_sim_time: True
      robot_radius: 0.22
      resolution: 0.05
      track_unknown_space: true
      plugins: ["static_layer", "obstacle_layer", "inflation_layer"]
      obstacle_layer:
        plugin: "nav2_costmap_2d::ObstacleLayer"
        enabled: True
        observation_sources: scan
        scan:
          topic: /scan
          max_obstacle_height: 2.0
          clearing: True
          marking: True
          data_type: "LaserScan"
          raytrace_max_range: 3.0
          raytrace_min_range: 0.0
          obstacle_max_range: 2.5
          obstacle_min_range: 0.0
      static_layer:
        plugin: "nav2_costmap_2d::StaticLayer"
        map_subscribe_transient_local: True
      inflation_layer:
        plugin: "nav2_costmap_2d::InflationLayer"
        cost_scaling_factor: 3.0
        inflation_radius: 0.55
      always_send_full_costmap: True

planner_server:
  ros__parameters:
    expected_planner_frequency: 20.0
    use_sim_time: True
    planner_plugins: ["GridBased"]
    GridBased:
      plugin: "nav2_navfn_planner/NavfnPlanner"
      tolerance: 0.5
      use_astar: false
      allow_unknown: true

smoother_server:
  ros__parameters:
    use_sim_time: True
    smoother_plugins: ["simple_smoother"]
    simple_smoother:
      plugin: "nav2_smoother::SimpleSmoother"
      tolerance: 1.0e-10
      max_its: 1000
      do_refinement: True

behavior_server:
  ros__parameters:
    costmap_topic: local_costmap/costmap_raw
    footprint_topic: local_costmap/published_footprint
    cycle_frequency: 10.0
    behavior_plugins: ["spin", "backup", "drive_on_heading", "wait"]
    spin:
      plugin: "nav2_behaviors/Spin"
    backup:
      plugin: "nav2_behaviors/BackUp"
    drive_on_heading:
      plugin: "nav2_behaviors/DriveOnHeading"
    wait:
      plugin: "nav2_behaviors/Wait"
    global_frame: odom
    robot_base_frame: base_link
    transform_tolerance: 0.1
    use_sim_time: true
    simulate_ahead_time: 2.0
    max_rotational_vel: 1.0
    min_rotational_vel: 0.4
    rotational_acc_lim: 3.2
'''

# Save configuration files
with open('full_system.launch.py', 'w') as f:
    f.write(main_launch_content)

with open('simulation.launch.py', 'w') as f:
    f.write(simulation_launch_content)
    
with open('nav2_params.yaml', 'w') as f:
    f.write(nav2_config_content)

print("✅ Created ROS2 launch files and configuration:")
print("   - full_system.launch.py")
print("   - simulation.launch.py")
print("   - nav2_params.yaml")