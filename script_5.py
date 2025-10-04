# 5. React Frontend Dashboard
react_dashboard_code = '''// React Dashboard Component for LunarBot Control
import React, { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';
import './Dashboard.css';

const LunarBotDashboard = () => {
  // State management
  const [robotStatus, setRobotStatus] = useState({
    connected: false,
    battery_level: 0,
    current_speed: 0.0,
    position: { x: 0, y: 0, theta: 0 },
    navigation_status: 'idle'
  });
  
  const [telemetry, setTelemetry] = useState({
    lidar_data: [],
    camera_stream: null,
    segmentation_stream: null,
    map_data: null
  });
  
  const [controlMode, setControlMode] = useState('manual'); // manual, autonomous
  const [isEmergencyStop, setIsEmergencyStop] = useState(false);
  const [navigationGoal, setNavigationGoal] = useState({ x: 0, y: 0, theta: 0 });
  const [manualControl, setManualControl] = useState({ linear: 0, angular: 0 });
  
  // WebSocket connection
  const socketRef = useRef(null);
  const cameraCanvasRef = useRef(null);
  const lidarCanvasRef = useRef(null);
  
  useEffect(() => {
    // Initialize WebSocket connection
    socketRef.current = io('http://localhost:5000');
    
    // Socket event listeners
    socketRef.current.on('connect', () => {
      console.log('Connected to LunarBot server');
      setRobotStatus(prev => ({ ...prev, connected: true }));
    });
    
    socketRef.current.on('disconnect', () => {
      console.log('Disconnected from LunarBot server');
      setRobotStatus(prev => ({ ...prev, connected: false }));
    });
    
    socketRef.current.on('camera_frame', (data) => {
      if (cameraCanvasRef.current) {
        const canvas = cameraCanvasRef.current;
        const ctx = canvas.getContext('2d');
        const img = new Image();
        img.onload = () => {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        };
        img.src = `data:image/jpeg;base64,${data.image}`;
      }
    });
    
    socketRef.current.on('lidar_data', (data) => {
      setTelemetry(prev => ({ ...prev, lidar_data: data.points }));
      renderLidarData(data.points);
    });
    
    socketRef.current.on('segmentation_frame', (data) => {
      setTelemetry(prev => ({ ...prev, segmentation_stream: data.image }));
    });
    
    socketRef.current.on('map_update', (data) => {
      setTelemetry(prev => ({ ...prev, map_data: data }));
    });
    
    // Request initial telemetry
    const telemetryInterval = setInterval(() => {
      socketRef.current.emit('request_telemetry');
    }, 1000);
    
    // Cleanup on unmount
    return () => {
      clearInterval(telemetryInterval);
      socketRef.current.disconnect();
    };
  }, []);
  
  const renderLidarData = (points) => {
    if (!lidarCanvasRef.current || !points.length) return;
    
    const canvas = lidarCanvasRef.current;
    const ctx = canvas.getContext('2d');
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const scale = 50; // pixels per meter
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw grid
    ctx.strokeStyle = '#ddd';
    ctx.lineWidth = 1;
    for (let i = -10; i <= 10; i++) {
      // Vertical lines
      ctx.beginPath();
      ctx.moveTo(centerX + i * scale, 0);
      ctx.lineTo(centerX + i * scale, canvas.height);
      ctx.stroke();
      
      // Horizontal lines
      ctx.beginPath();
      ctx.moveTo(0, centerY + i * scale);
      ctx.lineTo(canvas.width, centerY + i * scale);
      ctx.stroke();
    }
    
    // Draw robot position
    ctx.fillStyle = '#00ff00';
    ctx.fillRect(centerX - 5, centerY - 5, 10, 10);
    
    // Draw LiDAR points
    ctx.fillStyle = '#ff0000';
    points.forEach(point => {
      const x = centerX + point.x * scale;
      const y = centerY - point.y * scale; // Flip Y axis
      ctx.fillRect(x - 2, y - 2, 4, 4);
    });
  };
  
  const sendMovementCommand = async (linear, angular) => {
    try {
      const response = await fetch('http://localhost:5000/api/robot/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ linear_x: linear, angular_z: angular })
      });
      const result = await response.json();
      console.log('Movement command result:', result);
    } catch (error) {
      console.error('Movement command failed:', error);
    }
  };
  
  const sendNavigationGoal = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/robot/navigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(navigationGoal)
      });
      const result = await response.json();
      console.log('Navigation command result:', result);
      setRobotStatus(prev => ({ ...prev, navigation_status: 'navigating' }));
    } catch (error) {
      console.error('Navigation command failed:', error);
    }
  };
  
  const emergencyStop = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/robot/stop', {
        method: 'POST'
      });
      const result = await response.json();
      console.log('Emergency stop result:', result);
      setIsEmergencyStop(true);
      setRobotStatus(prev => ({ ...prev, navigation_status: 'stopped' }));
    } catch (error) {
      console.error('Emergency stop failed:', error);
    }
  };
  
  const resetEmergencyStop = () => {
    setIsEmergencyStop(false);
    setRobotStatus(prev => ({ ...prev, navigation_status: 'idle' }));
  };
  
  // Keyboard control handlers
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (controlMode !== 'manual' || isEmergencyStop) return;
      
      let linear = 0, angular = 0;
      
      switch(e.key.toLowerCase()) {
        case 'w': linear = 0.5; break;
        case 's': linear = -0.5; break;
        case 'a': angular = 0.5; break;
        case 'd': angular = -0.5; break;
        case ' ': emergencyStop(); return;
        default: return;
      }
      
      sendMovementCommand(linear, angular);
      setManualControl({ linear, angular });
    };
    
    const handleKeyUp = () => {
      if (controlMode === 'manual' && !isEmergencyStop) {
        sendMovementCommand(0, 0);
        setManualControl({ linear: 0, angular: 0 });
      }
    };
    
    window.addEventListener('keydown', handleKeyPress);
    window.addEventListener('keyup', handleKeyUp);
    
    return () => {
      window.removeEventListener('keydown', handleKeyPress);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [controlMode, isEmergencyStop]);
  
  return (
    <div className="lunarbot-dashboard">
      <header className="dashboard-header">
        <h1>LunarBot Mission Control</h1>
        <div className="connection-status">
          <span className={`status-indicator ${robotStatus.connected ? 'connected' : 'disconnected'}`}>
            {robotStatus.connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </header>
      
      <div className="dashboard-grid">
        {/* Camera Feed */}
        <div className="panel camera-panel">
          <h3>Camera Feed</h3>
          <canvas ref={cameraCanvasRef} width="640" height="480" />
        </div>
        
        {/* Segmentation View */}
        <div className="panel segmentation-panel">
          <h3>Terrain Segmentation</h3>
          {telemetry.segmentation_stream && (
            <img 
              src={`data:image/jpeg;base64,${telemetry.segmentation_stream}`}
              alt="Segmentation"
              style={{ width: '100%', height: 'auto' }}
            />
          )}
        </div>
        
        {/* LiDAR Visualization */}
        <div className="panel lidar-panel">
          <h3>LiDAR Scanner</h3>
          <canvas ref={lidarCanvasRef} width="400" height="400" />
          <div className="lidar-stats">
            Points: {telemetry.lidar_data.length}
          </div>
        </div>
        
        {/* Control Panel */}
        <div className="panel control-panel">
          <h3>Robot Control</h3>
          
          {/* Emergency Stop */}
          <div className="emergency-section">
            {!isEmergencyStop ? (
              <button className="emergency-stop" onClick={emergencyStop}>
                EMERGENCY STOP
              </button>
            ) : (
              <button className="reset-stop" onClick={resetEmergencyStop}>
                Reset Emergency Stop
              </button>
            )}
          </div>
          
          {/* Control Mode */}
          <div className="control-mode">
            <label>
              <input 
                type="radio" 
                value="manual" 
                checked={controlMode === 'manual'}
                onChange={(e) => setControlMode(e.target.value)}
              />
              Manual Control
            </label>
            <label>
              <input 
                type="radio" 
                value="autonomous" 
                checked={controlMode === 'autonomous'}
                onChange={(e) => setControlMode(e.target.value)}
              />
              Autonomous Navigation
            </label>
          </div>
          
          {/* Manual Control */}
          {controlMode === 'manual' && (
            <div className="manual-controls">
              <div className="control-instructions">
                Use WASD keys to control:
                <br />W/S: Forward/Backward
                <br />A/D: Left/Right
                <br />Space: Emergency Stop
              </div>
              <div className="current-command">
                Linear: {manualControl.linear.toFixed(2)} m/s
                <br />
                Angular: {manualControl.angular.toFixed(2)} rad/s
              </div>
            </div>
          )}
          
          {/* Navigation Goal */}
          {controlMode === 'autonomous' && (
            <div className="navigation-controls">
              <h4>Navigation Goal</h4>
              <div className="goal-inputs">
                <label>
                  X: <input 
                    type="number" 
                    step="0.1" 
                    value={navigationGoal.x}
                    onChange={(e) => setNavigationGoal(prev => ({...prev, x: parseFloat(e.target.value)}))}
                  />
                </label>
                <label>
                  Y: <input 
                    type="number" 
                    step="0.1" 
                    value={navigationGoal.y}
                    onChange={(e) => setNavigationGoal(prev => ({...prev, y: parseFloat(e.target.value)}))}
                  />
                </label>
                <label>
                  Theta: <input 
                    type="number" 
                    step="0.1" 
                    value={navigationGoal.theta}
                    onChange={(e) => setNavigationGoal(prev => ({...prev, theta: parseFloat(e.target.value)}))}
                  />
                </label>
              </div>
              <button onClick={sendNavigationGoal} disabled={isEmergencyStop}>
                Send Navigation Goal
              </button>
            </div>
          )}
        </div>
        
        {/* Status Panel */}
        <div className="panel status-panel">
          <h3>Robot Status</h3>
          <div className="status-grid">
            <div className="status-item">
              <span className="label">Battery:</span>
              <div className="battery-bar">
                <div 
                  className="battery-fill"
                  style={{ width: `${robotStatus.battery_level}%` }}
                />
              </div>
              <span>{robotStatus.battery_level}%</span>
            </div>
            
            <div className="status-item">
              <span className="label">Speed:</span>
              <span>{robotStatus.current_speed.toFixed(2)} m/s</span>
            </div>
            
            <div className="status-item">
              <span className="label">Position:</span>
              <span>
                ({robotStatus.position.x.toFixed(2)}, {robotStatus.position.y.toFixed(2)})
              </span>
            </div>
            
            <div className="status-item">
              <span className="label">Navigation:</span>
              <span className={`nav-status ${robotStatus.navigation_status}`}>
                {robotStatus.navigation_status}
              </span>
            </div>
          </div>
        </div>
        
        {/* Map View */}
        <div className="panel map-panel">
          <h3>Mission Map</h3>
          {telemetry.map_data && (
            <img 
              src={`data:image/png;base64,${telemetry.map_data.image}`}
              alt="Mission Map"
              style={{ width: '100%', height: 'auto', border: '1px solid #ccc' }}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default LunarBotDashboard;
'''

with open('Dashboard.jsx', 'w') as f:
    f.write(react_dashboard_code)

print("✅ Created Dashboard.jsx")