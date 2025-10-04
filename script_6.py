# 6. Docker Configuration Files
dockerfile_content = '''# LunarBot Docker Configuration
FROM ros:humble-desktop

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=humble

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    python3-pip \\
    python3-dev \\
    python3-opencv \\
    git \\
    wget \\
    curl \\
    vim \\
    tmux \\
    htop \\
    build-essential \\
    cmake \\
    libeigen3-dev \\
    libopencv-dev \\
    python3-colcon-common-extensions \\
    python3-rosdep \\
    ros-${ROS_DISTRO}-navigation2 \\
    ros-${ROS_DISTRO}-nav2-bringup \\
    ros-${ROS_DISTRO}-slam-toolbox \\
    ros-${ROS_DISTRO}-robot-localization \\
    ros-${ROS_DISTRO}-gazebo-* \\
    ros-${ROS_DISTRO}-rviz2 \\
    ros-${ROS_DISTRO}-cv-bridge \\
    ros-${ROS_DISTRO}-image-transport \\
    ros-${ROS_DISTRO}-camera-info-manager \\
    && rm -rf /var/lib/apt/lists/*

# Install Python ML/DL packages
RUN pip3 install \\
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu \\
    ultralytics \\
    opencv-python \\
    numpy \\
    matplotlib \\
    scipy \\
    flask \\
    flask-socketio \\
    flask-cors \\
    websockets \\
    requests \\
    Pillow \\
    scikit-learn \\
    pandas \\
    jupyter

# Set up workspace
WORKDIR /workspace
RUN mkdir -p /workspace/src

# Copy project files
COPY src/ /workspace/src/
COPY config/ /workspace/config/
COPY launch/ /workspace/launch/
COPY requirements/ /workspace/requirements/

# Install ROS dependencies
RUN cd /workspace && \\
    rosdep init || true && \\
    rosdep update && \\
    rosdep install --from-paths src --ignore-src -r -y

# Build ROS2 workspace
RUN cd /workspace && \\
    . /opt/ros/${ROS_DISTRO}/setup.sh && \\
    colcon build --symlink-install

# Set up entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Web interface setup
WORKDIR /workspace/web_frontend
COPY web_frontend/ /workspace/web_frontend/
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \\
    apt-get install -y nodejs && \\
    npm install

# Expose ports
EXPOSE 5000 3000 8080

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
'''

# Docker Compose configuration
docker_compose_content = '''version: '3.8'

services:
  lunarbot_simulation:
    build: .
    container_name: lunarbot_sim
    privileged: true
    network_mode: host
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
      - ./logs:/workspace/logs
      - ./data:/workspace/data
      - ./models:/workspace/models
    environment:
      - DISPLAY=${DISPLAY}
      - ROS_DOMAIN_ID=42
      - GAZEBO_MODEL_PATH=/workspace/models
      - TURTLEBOT3_MODEL=waffle_pi
    stdin_open: true
    tty: true
    command: >
      bash -c "
        source /workspace/install/setup.bash &&
        ros2 launch lunarbot_bringup simulation.launch.py
      "

  lunarbot_navigation:
    build: .
    container_name: lunarbot_nav
    network_mode: host
    depends_on:
      - lunarbot_simulation
    environment:
      - ROS_DOMAIN_ID=42
    volumes:
      - ./config:/workspace/config
      - ./maps:/workspace/maps
    command: >
      bash -c "
        source /workspace/install/setup.bash &&
        sleep 10 &&
        ros2 launch lunarbot_navigation navigation.launch.py
      "

  lunarbot_perception:
    build: .
    container_name: lunarbot_perception
    network_mode: host
    depends_on:
      - lunarbot_simulation
    environment:
      - ROS_DOMAIN_ID=42
    volumes:
      - ./models:/workspace/models
      - /dev:/dev
    privileged: true
    command: >
      bash -c "
        source /workspace/install/setup.bash &&
        sleep 15 &&
        ros2 launch lunarbot_perception perception.launch.py
      "

  lunarbot_web_backend:
    build: .
    container_name: lunarbot_web_backend
    network_mode: host
    depends_on:
      - lunarbot_simulation
      - lunarbot_navigation
    environment:
      - ROS_DOMAIN_ID=42
      - FLASK_ENV=production
    volumes:
      - ./web_interface:/workspace/web_interface
    ports:
      - "5000:5000"
    command: >
      bash -c "
        source /workspace/install/setup.bash &&
        sleep 20 &&
        cd /workspace/web_interface &&
        python3 backend.py
      "

  lunarbot_web_frontend:
    build: .
    container_name: lunarbot_web_frontend
    ports:
      - "3000:3000"
    volumes:
      - ./web_frontend:/workspace/web_frontend
    working_dir: /workspace/web_frontend
    command: >
      bash -c "
        npm install &&
        npm start
      "

  # Optional: Monitoring and logging
  lunarbot_monitor:
    image: grafana/grafana:latest
    container_name: lunarbot_monitor
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=lunarbot2024

volumes:
  grafana_data:

networks:
  default:
    driver: bridge
'''

# Entrypoint script
entrypoint_content = '''#!/bin/bash
set -e

# Setup ROS environment
source /opt/ros/$ROS_DISTRO/setup.bash

# Source workspace if built
if [ -f /workspace/install/setup.bash ]; then
    source /workspace/install/setup.bash
fi

# Initialize rosdep if not done
if [ ! -d /etc/ros/rosdep ]; then
    rosdep init
fi

# Update rosdep
rosdep update

# Set up display for GUI applications
export DISPLAY=${DISPLAY:-:0}

# Create necessary directories
mkdir -p /workspace/logs
mkdir -p /workspace/data
mkdir -p /workspace/models

# Set permissions
chown -R $(whoami):$(whoami) /workspace/logs
chown -R $(whoami):$(whoami) /workspace/data

echo "LunarBot environment initialized successfully!"

exec "$@"
'''

# Save Docker files
with open('Dockerfile', 'w') as f:
    f.write(dockerfile_content)

with open('docker-compose.yml', 'w') as f:
    f.write(docker_compose_content)

with open('entrypoint.sh', 'w') as f:
    f.write(entrypoint_content)

print("✅ Created Docker configuration files:")
print("   - Dockerfile")
print("   - docker-compose.yml") 
print("   - entrypoint.sh")