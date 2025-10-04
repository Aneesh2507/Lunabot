#!/bin/bash
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
