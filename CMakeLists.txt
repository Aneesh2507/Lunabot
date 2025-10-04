cmake_minimum_required(VERSION 3.8)
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
