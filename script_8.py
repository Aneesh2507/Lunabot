# 8. Requirements and Setup Files

# Python requirements
requirements_content = '''# LunarBot Python Dependencies

# Deep Learning & Computer Vision
torch>=2.0.0
torchvision>=0.15.0
torchaudio>=2.0.0
ultralytics>=8.0.0
opencv-python>=4.8.0
opencv-contrib-python>=4.8.0
Pillow>=9.5.0

# Scientific Computing
numpy>=1.24.0
scipy>=1.10.0
matplotlib>=3.7.0
scikit-learn>=1.3.0
pandas>=2.0.0

# Web Framework
flask>=2.3.0
flask-socketio>=5.3.0
flask-cors>=4.0.0
websockets>=11.0
requests>=2.31.0

# ROS2 Python Libraries
rclpy
geometry-msgs
sensor-msgs
nav-msgs
std-msgs
tf2-ros
cv-bridge
image-transport

# Utilities
pyyaml>=6.0
jsonschema>=4.17.0
python-dotenv>=1.0.0
click>=8.1.0
tqdm>=4.65.0

# Development & Testing
pytest>=7.4.0
pytest-cov>=4.1.0
black>=23.7.0
flake8>=6.0.0
jupyter>=1.0.0

# Optional: Isaac Sim support
# omni-isaac-sim  # Uncomment if using Isaac Sim
'''

# ROS2 package.xml
package_xml_content = '''<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>lunarbot_bringup</name>
  <version>1.0.0</version>
  <description>LunarBot autonomous navigation system for lunar habitat exploration</description>
  
  <maintainer email="lunarbot@example.com">LunarBot Team</maintainer>
  <license>MIT</license>
  
  <url type="website">https://github.com/lunarbot/lunarbot</url>
  <url type="bugtracker">https://github.com/lunarbot/lunarbot/issues</url>
  <url type="repository">https://github.com/lunarbot/lunarbot</url>
  
  <author>LunarBot Development Team</author>
  
  <buildtool_depend>ament_cmake</buildtool_depend>
  <buildtool_depend>ament_cmake_python</buildtool_depend>
  
  <!-- Core ROS2 dependencies -->
  <depend>rclcpp</depend>
  <depend>rclpy</depend>
  <depend>std_msgs</depend>
  <depend>geometry_msgs</depend>
  <depend>sensor_msgs</depend>
  <depend>nav_msgs</depend>
  <depend>tf2</depend>
  <depend>tf2_ros</depend>
  <depend>tf2_geometry_msgs</depend>
  
  <!-- Navigation dependencies -->
  <depend>nav2_bringup</depend>
  <depend>nav2_msgs</depend>
  <depend>slam_toolbox</depend>
  <depend>robot_localization</depend>
  
  <!-- Simulation dependencies -->
  <depend>gazebo_ros_pkgs</depend>
  <depend>robot_state_publisher</depend>
  <depend>joint_state_publisher</depend>
  <depend>xacro</depend>
  
  <!-- Perception dependencies -->
  <depend>cv_bridge</depend>
  <depend>image_transport</depend>
  <depend>camera_info_manager</depend>
  
  <!-- Visualization -->
  <depend>rviz2</depend>
  <depend>rviz_common</depend>
  
  <test_depend>ament_lint_auto</test_depend>
  <test_depend>ament_lint_common</test_depend>
  <test_depend>ament_copyright</test_depend>
  <test_depend>ament_flake8</test_depend>
  <test_depend>ament_pep257</test_depend>
  
  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
'''

# CMakeLists.txt for ROS2 package
cmake_content = '''cmake_minimum_required(VERSION 3.8)
project(lunarbot_bringup)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)

# Include directories
include_directories(include)

# Install launch files
install(DIRECTORY
  launch
  config
  worlds
  urdf
  rviz
  DESTINATION share/${PROJECT_NAME}
)

# Install Python modules
ament_python_install_package(${PROJECT_NAME})

# Install Python executables
install(PROGRAMS
  src/perception/object_detection.py
  src/perception/semantic_segmentation.py
  src/navigation/slam_navigation.py
  src/web_interface/web_backend.py
  src/simulation/terrain_generator.py
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
'''

# Setup instructions README
setup_readme_content = '''# LunarBot Setup Instructions

## System Requirements

- Ubuntu 22.04 LTS (recommended)
- ROS2 Humble Hawksbill
- Python 3.10+
- Docker and Docker Compose
- NVIDIA GPU (recommended for ML/DL models)
- 8GB+ RAM
- 50GB+ free disk space

## Installation

### 1. Install ROS2 Humble

```bash
# Install ROS2 Humble
sudo apt update && sudo apt install curl gnupg lsb-release
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(source /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update
sudo apt install ros-humble-desktop
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup ros-humble-slam-toolbox
```

### 2. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin
```

### 3. Clone and Setup Project

```bash
# Clone repository
git clone https://github.com/lunarbot/lunarbot.git
cd lunarbot

# Create ROS2 workspace
mkdir -p ~/lunarbot_ws/src
cd ~/lunarbot_ws/src
ln -s $(pwd) lunarbot

# Install dependencies
cd ~/lunarbot_ws
rosdep init
rosdep update
rosdep install --from-paths src --ignore-src -r -y

# Build workspace
colcon build --symlink-install
source install/setup.bash
```

### 4. Download ML Models

```bash
# Create models directory
mkdir -p ~/lunarbot_ws/models

# Download pre-trained models (replace with actual URLs)
cd ~/lunarbot_ws/models
wget -O yolo_lunar.pt "https://example.com/models/yolo_lunar.pt"
wget -O deeplabv3_lunar.pth "https://example.com/models/deeplabv3_lunar.pth"
```

### 5. Download Lunar Terrain Data

```bash
# Create data directory
mkdir -p ~/lunarbot_ws/data

# Download NASA DEM data
cd ~/lunarbot_ws/data
wget -O lunar_south_pole_dem.tif "https://pgda.gsfc.nasa.gov/data/lunar_south_pole_dem.tif"
wget -O lunar_regolith_texture.jpg "https://example.com/textures/lunar_regolith.jpg"
```

## Usage

### Option 1: Docker Deployment (Recommended)

```bash
# Build and run with Docker Compose
cd ~/lunarbot_ws/src/lunarbot
docker-compose up --build

# Access web interface at http://localhost:3000
```

### Option 2: Native ROS2 Launch

```bash
# Terminal 1: Launch simulation
cd ~/lunarbot_ws
source install/setup.bash
ros2 launch lunarbot_bringup simulation.launch.py

# Terminal 2: Launch navigation
ros2 launch lunarbot_bringup full_system.launch.py

# Terminal 3: Launch web interface
cd src/lunarbot/web_interface
python3 web_backend.py

# Terminal 4: Launch React frontend
cd web_frontend
npm install
npm start
```

### Option 3: Isaac Sim Integration

```bash
# Install Isaac Sim (requires NVIDIA Omniverse)
# Download from: https://developer.nvidia.com/isaac-sim

# Set environment variables
export ISAAC_SIM_PATH="/path/to/isaac_sim"
export PYTHONPATH="$ISAAC_SIM_PATH/kit/python/lib/python3.7/site-packages:$PYTHONPATH"

# Launch with Isaac Sim
ros2 launch lunarbot_bringup isaac_simulation.launch.py
```

## Configuration

### Navigation Tuning

Edit `config/nav2_params.yaml` to adjust navigation behavior:

```yaml
# Key parameters to tune
controller_server:
  FollowPath:
    max_vel_x: 0.8  # Maximum linear velocity
    max_vel_theta: 1.0  # Maximum angular velocity
    sim_time: 1.7  # Trajectory simulation time

local_costmap:
  robot_radius: 0.22  # Robot footprint radius
  inflation_radius: 0.55  # Safety inflation
```

### ML Model Configuration

Edit `config/ml_models.yaml`:

```yaml
object_detection:
  model_path: "/workspace/models/yolo_lunar.pt"
  confidence_threshold: 0.5
  classes: ["rock", "crater", "boulder", "pothole", "hill"]

semantic_segmentation:
  model_path: "/workspace/models/deeplabv3_lunar.pth"
  input_size: [512, 512]
  classes: ["background", "rock", "sand", "crater", "safe_path", "obstacle"]
```

## Testing

```bash
# Run unit tests
cd ~/lunarbot_ws
colcon test --packages-select lunarbot_bringup

# Run integration tests
python3 -m pytest src/lunarbot/tests/

# Test web interface
curl -X POST http://localhost:5000/api/robot/move \\
  -H "Content-Type: application/json" \\
  -d '{"linear_x": 0.1, "angular_z": 0.0}'
```

## Monitoring

### System Monitoring

```bash
# Check ROS2 nodes
ros2 node list

# Monitor topics
ros2 topic list
ros2 topic echo /cmd_vel

# Check transforms
ros2 run tf2_tools view_frames
```

### Performance Monitoring

```bash
# Docker stats
docker stats

# Resource usage
htop
nvidia-smi  # GPU usage

# Network monitoring
netstat -tlnp | grep :5000
```

## Troubleshooting

### Common Issues

1. **Camera not working**: Check USB permissions and camera index
2. **Navigation fails**: Verify map quality and robot localization
3. **Web interface not accessible**: Check firewall and port forwarding
4. **Docker permission denied**: Add user to docker group and restart

### Debug Commands

```bash
# Check ROS2 environment
printenv | grep ROS

# Verify package installation
ros2 pkg list | grep lunarbot

# Test ML models
python3 -c "import torch; print(torch.cuda.is_available())"

# Check network connectivity
ping localhost
telnet localhost 5000
```

## Development

### Code Structure

```
lunarbot/
├── src/
│   ├── perception/          # ML/DL modules
│   ├── navigation/          # SLAM and path planning
│   ├── control/            # Motor control and safety
│   ├── web_interface/      # Flask backend
│   └── simulation/         # Gazebo/Isaac Sim
├── config/                 # Configuration files
├── launch/                 # ROS2 launch files
├── web_frontend/           # React dashboard
├── docker/                 # Container configuration
└── tests/                  # Unit and integration tests
```

### Adding New Features

1. Create new ROS2 node in appropriate src/ subdirectory
2. Add dependencies to package.xml
3. Update CMakeLists.txt
4. Add launch file configuration
5. Update web interface if needed
6. Write unit tests
7. Update documentation

### Contributing

1. Fork the repository
2. Create feature branch
3. Follow coding standards (black, flake8)
4. Add comprehensive tests
5. Update documentation
6. Submit pull request

## Support

- Documentation: https://lunarbot.readthedocs.io
- Issues: https://github.com/lunarbot/lunarbot/issues
- Discord: https://discord.gg/lunarbot
- Email: support@lunarbot.com
'''

# Save all files
with open('requirements.txt', 'w') as f:
    f.write(requirements_content)

with open('package.xml', 'w') as f:
    f.write(package_xml_content)

with open('CMakeLists.txt', 'w') as f:
    f.write(cmake_content)

with open('SETUP.md', 'w') as f:
    f.write(setup_readme_content)

print("✅ Created setup and configuration files:")
print("   - requirements.txt")
print("   - package.xml") 
print("   - CMakeLists.txt")
print("   - SETUP.md")

# Summary of all created files
print("\n🚀 LunarBot Project Complete!")
print("=" * 60)
print("Created files:")

all_files = [
    "object_detection.py", "semantic_segmentation.py", "slam_navigation.py",
    "web_backend.py", "Dashboard.jsx", "Dockerfile", "docker-compose.yml", 
    "entrypoint.sh", "full_system.launch.py", "simulation.launch.py", 
    "nav2_params.yaml", "requirements.txt", "package.xml", "CMakeLists.txt", "SETUP.md"
]

for i, filename in enumerate(all_files, 1):
    print(f"{i:2d}. {filename}")

print(f"\n📊 Total: {len(all_files)} files created")
print("✨ Ready for deployment and development!")