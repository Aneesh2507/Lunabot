# LunarBot Docker Configuration
FROM ros:humble-desktop

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=humble

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    python3-opencv \
    git \
    wget \
    curl \
    vim \
    tmux \
    htop \
    build-essential \
    cmake \
    libeigen3-dev \
    libopencv-dev \
    python3-colcon-common-extensions \
    python3-rosdep \
    ros-${ROS_DISTRO}-navigation2 \
    ros-${ROS_DISTRO}-nav2-bringup \
    ros-${ROS_DISTRO}-slam-toolbox \
    ros-${ROS_DISTRO}-robot-localization \
    ros-${ROS_DISTRO}-gazebo-* \
    ros-${ROS_DISTRO}-rviz2 \
    ros-${ROS_DISTRO}-cv-bridge \
    ros-${ROS_DISTRO}-image-transport \
    ros-${ROS_DISTRO}-camera-info-manager \
    && rm -rf /var/lib/apt/lists/*

# Install Python ML/DL packages
RUN pip3 install \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu \
    ultralytics \
    opencv-python \
    numpy \
    matplotlib \
    scipy \
    flask \
    flask-socketio \
    flask-cors \
    websockets \
    requests \
    Pillow \
    scikit-learn \
    pandas \
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
RUN cd /workspace && \
    rosdep init || true && \
    rosdep update && \
    rosdep install --from-paths src --ignore-src -r -y

# Build ROS2 workspace
RUN cd /workspace && \
    . /opt/ros/${ROS_DISTRO}/setup.sh && \
    colcon build --symlink-install

# Set up entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Web interface setup
WORKDIR /workspace/web_frontend
COPY web_frontend/ /workspace/web_frontend/
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install

# Expose ports
EXPOSE 5000 3000 8080

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
