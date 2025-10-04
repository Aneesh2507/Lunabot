import os

# Create the main project structure
project_structure = {
    "lunarbot_project": {
        "src": {
            "perception": ["object_detection.py", "semantic_segmentation.py", "terrain_analysis.py"],
            "navigation": ["slam_node.py", "path_planner.py", "obstacle_avoidance.py"],
            "control": ["motor_controller.py", "safety_system.py"],
            "web_interface": ["backend.py", "websocket_handler.py"],
            "simulation": ["gazebo_launch.py", "terrain_generator.py"]
        },
        "config": ["nav2_params.yaml", "slam_config.yaml", "ml_models.yaml"],
        "launch": ["full_system.launch.py", "simulation.launch.py"],
        "web_frontend": {
            "src": {
                "components": ["Dashboard.jsx", "MapViewer.jsx", "ControlPanel.jsx"],
                "services": ["ros_service.js", "websocket.js"]
            }
        },
        "docker": ["Dockerfile", "docker-compose.yml"],
        "requirements": ["requirements.txt", "package.xml"]
    }
}

def create_file_structure(base_path, structure, level=0):
    """Create directory structure and return file paths"""
    paths = []
    for name, content in structure.items():
        current_path = os.path.join(base_path, name)
        if isinstance(content, dict):
            paths.append(f"{'  ' * level}📁 {name}/")
            paths.extend(create_file_structure(current_path, content, level + 1))
        elif isinstance(content, list):
            paths.append(f"{'  ' * level}📁 {name}/")
            for file in content:
                paths.append(f"{'  ' * (level + 1)}📄 {file}")
        else:
            paths.append(f"{'  ' * level}📄 {name}")
    return paths

# Generate the project structure visualization
structure_output = create_file_structure(".", project_structure)
print("LunarBot Project Structure:")
print("=" * 50)
for item in structure_output:
    print(item)

print(f"\n✅ Total project structure created with {len([x for x in structure_output if '📄' in x])} files")