# LunarBot Navigation Simulator with Visual Bot Figure

This enhanced LunarBot simulation includes a visual bot figure that can navigate through safe paths detected by the program. The bot can be controlled using forward, backward, left, and right movement controls.

## Features

### 🤖 Visual Bot Figure
- **Blue circular bot** with yellow direction indicator
- **Real-time position tracking** with coordinates
- **Battery simulation** that drains during movement
- **Status indicators** (idle, moving, navigating, stopped)
- **Collision detection** with obstacles

### 🎮 Movement Controls
- **Forward/Backward**: Move the bot in the direction it's facing
- **Left/Right**: Turn the bot left or right
- **Emergency Stop**: Immediately stop all movement
- **Navigation Mode**: Click to set target destinations

### 🛤️ Safe Path Navigation
- **Automatic pathfinding** using detected safe paths
- **Obstacle avoidance** with safety margins
- **Path visualization** showing planned routes
- **Terrain analysis** with safety scores

### 🌙 Lunar Terrain
- **Dynamic obstacle generation** (rocks, craters, boulders, potholes)
- **Safe path detection** with varying safety scores
- **Realistic lunar surface simulation**
- **Collision detection** and avoidance

## Simulation Modes

### 1. 🎮 Pygame Visual Simulator
**File**: `lunarbot_navigation_simulator.py`

Real-time graphics simulation with mouse and keyboard controls.

**Controls**:
- `W/S` - Move forward/backward
- `A/D` - Turn left/right
- `SPACE` - Emergency stop
- `N` - Toggle navigation mode
- `Click` - Set navigation target
- `ESC` - Exit

**Features**:
- Real-time graphics rendering
- Camera follows the bot
- Visual terrain with obstacles and safe paths
- Bot trail showing movement history
- Interactive controls

### 2. 🌐 Web-based Simulator
**File**: `web_navigation_simulator.py`
**Template**: `templates/navigation_simulator.html`

Browser-based interface with WebSocket communication.

**Features**:
- Modern web interface
- Real-time bot control buttons
- Canvas-based visualization
- WebSocket communication
- Responsive design
- Battery and status monitoring

**Access**: http://localhost:5000

### 3. 💻 Console Demo
**File**: `navigation_demo.py`

Text-based simulation with detailed status display.

**Controls**:
- `W/S` - Move forward/backward
- `A/D` - Turn left/right
- `G` - Go to next goal
- `R` - Run autonomous mission
- `V` - View detailed bot status
- `Q` - Quit

**Features**:
- Detailed text output
- Visual ASCII representation
- Terrain information display
- Mission planning
- Status monitoring

## Quick Start

### Option 1: Use the Launcher
```bash
python lunarbot_launcher.py
```

The launcher will check dependencies and let you choose your preferred simulation mode.

### Option 2: Run Individual Simulators

#### Pygame Simulator
```bash
pip install pygame numpy
python lunarbot_navigation_simulator.py
```

#### Web Simulator
```bash
pip install flask flask-socketio flask-cors numpy
python web_navigation_simulator.py
```
Then open http://localhost:5000 in your browser.

#### Console Demo
```bash
pip install numpy
python navigation_demo.py
```

## Requirements

### Core Dependencies
- **Python 3.7+**
- **numpy** - Mathematical calculations
- **pygame** - Graphics rendering (for visual simulator)
- **flask** - Web framework (for web simulator)
- **flask-socketio** - WebSocket support (for web simulator)
- **flask-cors** - Cross-origin requests (for web simulator)

### Installation
```bash
# For all simulators
pip install pygame flask flask-socketio flask-cors numpy

# Or install from requirements file
pip install -r simulator_requirements.txt
```

## Bot Navigation System

### Bot Figure Properties
- **Position**: (x, y) coordinates in meters
- **Orientation**: Theta angle in radians
- **Speed**: Linear velocity in m/s
- **Angular Speed**: Rotational velocity in rad/s
- **Battery**: Percentage remaining (drains during movement)
- **Status**: Current operation mode

### Movement System
- **Acceleration**: Gradual speed changes for realistic movement
- **Constraints**: Maximum speed and angular speed limits
- **Collision Detection**: Automatic stopping when hitting obstacles
- **Battery Drain**: Energy consumption based on movement

### Pathfinding Algorithm
1. **Safe Path Detection**: Analyze terrain for navigable routes
2. **Path Selection**: Choose safest available path to target
3. **Waypoint Planning**: Create intermediate navigation points
4. **Dynamic Replanning**: Adjust path based on obstacles

### Terrain Generation
- **Obstacles**: Randomly placed rocks, craters, boulders, potholes
- **Safe Paths**: Generated routes with safety scores
- **Collision Boundaries**: Safety margins around obstacles
- **Dynamic Updates**: Terrain can be regenerated

## Usage Examples

### Basic Movement
```python
# Move forward
bot.move_forward(dt)

# Turn left
bot.turn_left(dt)

# Stop
bot.stop()
```

### Navigation
```python
# Navigate to coordinates using safe paths
bot.navigate_to(target_x, target_y, safe_paths)

# Check if target reached
if bot.target_position is None:
    print("Target reached!")
```

### Status Monitoring
```python
# Get current position
position = bot.position

# Check battery level
if bot.battery_level < 20:
    print("Low battery warning!")

# Get current status
status = bot.status  # 'idle', 'moving', 'navigating', 'stopped'
```

## File Structure

```
├── lunarbot_navigation_simulator.py    # Pygame visual simulator
├── web_navigation_simulator.py         # Web-based simulator
├── navigation_demo.py                   # Enhanced console demo
├── lunarbot_launcher.py                 # Simulation launcher
├── simulator_requirements.txt           # Python dependencies
├── templates/
│   └── navigation_simulator.html        # Web interface template
└── README.md                           # This file
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   pip install pygame flask flask-socketio flask-cors numpy
   ```

2. **Pygame Display Issues**
   - Ensure you have a display (not running headless)
   - Try running with `DISPLAY=:0 python lunarbot_navigation_simulator.py`

3. **Web Simulator Port Issues**
   - Change port in `web_navigation_simulator.py` if 5000 is occupied
   - Check firewall settings

4. **Performance Issues**
   - Reduce simulation speed in the code
   - Lower graphics quality settings

### Performance Tips

- **Pygame**: Reduce frame rate or simplify graphics
- **Web**: Limit WebSocket update frequency
- **Console**: Reduce output verbosity

## Contributing

To extend the bot navigation system:

1. **Add New Movement Modes**: Extend the `LunarBotFigure` class
2. **Improve Pathfinding**: Enhance the `find_safe_path` method
3. **Add Sensors**: Implement LiDAR or camera simulation
4. **Create New Terrains**: Extend the `TerrainGenerator` class

## License

This project is part of the LunarBot simulation system for educational and research purposes.

---

**Enjoy exploring lunar terrain with your LunarBot! 🚀🌙**
