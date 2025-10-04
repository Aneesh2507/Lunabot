import React, { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';
import './AdvancedDashboard.css';

const AdvancedLunarBotDashboard = () => {
  // State management
  const [robotStatus, setRobotStatus] = useState({
    connected: false,
    battery_level: 95,
    current_speed: 0.0,
    position: { x: 0.0, y: 0.0, theta: 0.0 },
    navigation_status: 'idle',
    temperature: -180,
    radiation_level: 0.1,
    mission_time: 0
  });

  const [terrainAnalysis, setTerrainAnalysis] = useState({
    safe_paths: [],
    obstacles: [],
    craters: [],
    rocks: [],
    navigability_score: 100,
    recommended_direction: 0
  });

  const [missionData, setMissionData] = useState({
    waypoints: [],
    current_waypoint: 0,
    distance_traveled: 0.0,
    samples_collected: 0,
    photos_taken: 0
  });

  const [uploadedImage, setUploadedImage] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Refs
  const socketRef = useRef(null);
  const fileInputRef = useRef(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    // Initialize WebSocket connection
    socketRef.current = io('http://localhost:5000');

    // Socket event listeners
    socketRef.current.on('connect', () => {
      console.log('Connected to Advanced LunarBot server');
      setRobotStatus(prev => ({ ...prev, connected: true }));
    });

    socketRef.current.on('disconnect', () => {
      console.log('Disconnected from Advanced LunarBot server');
      setRobotStatus(prev => ({ ...prev, connected: false }));
    });

    socketRef.current.on('robot_status_update', (data) => {
      setRobotStatus(data);
    });

    socketRef.current.on('terrain_analysis_update', (data) => {
      setTerrainAnalysis(data);
    });

    socketRef.current.on('mission_data_update', (data) => {
      setMissionData(data);
    });

    // Cleanup on unmount
    return () => {
      socketRef.current.disconnect();
    };
  }, []);

  // Robot control functions
  const moveRobot = async (direction) => {
    const commands = {
      'forward': { linear_x: 0.5, angular_z: 0 },
      'backward': { linear_x: -0.5, angular_z: 0 },
      'left': { linear_x: 0, angular_z: 0.5 },
      'right': { linear_x: 0, angular_z: -0.5 }
    };

    try {
      const response = await fetch('http://localhost:5000/api/robot/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(commands[direction])
      });
      const result = await response.json();
      console.log('Movement command result:', result);
    } catch (error) {
      console.error('Movement command failed:', error);
    }
  };

  const emergencyStop = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/robot/stop', {
        method: 'POST'
      });
      const result = await response.json();
      console.log('Emergency stop result:', result);
    } catch (error) {
      console.error('Emergency stop failed:', error);
    }
  };

  const navigateToCoordinates = async (x, y) => {
    try {
      const response = await fetch('http://localhost:5000/api/robot/navigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x: x, y: y })
      });
      const result = await response.json();
      console.log('Navigation result:', result);
    } catch (error) {
      console.error('Navigation failed:', error);
    }
  };

  // Image upload and analysis
  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      setUploadedImage(e.target.result);
      analyzeImage(e.target.result);
    };
    reader.readAsDataURL(file);
  };

  const analyzeImage = async (imageData) => {
    setIsAnalyzing(true);
    try {
      const response = await fetch('http://localhost:5000/api/analyze-terrain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: imageData })
      });
      const result = await response.json();
      setAnalysisResult(result);
    } catch (error) {
      console.error('Image analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
          setUploadedImage(e.target.result);
          analyzeImage(e.target.result);
        };
        reader.readAsDataURL(file);
      }
    }
  };

  // Render terrain visualization
  useEffect(() => {
    if (canvasRef.current && terrainAnalysis.safe_paths.length > 0) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const scale = 20;

      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw grid
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
      ctx.lineWidth = 1;
      for (let i = -10; i <= 10; i++) {
        ctx.beginPath();
        ctx.moveTo(centerX + i * scale, 0);
        ctx.lineTo(centerX + i * scale, canvas.height);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(0, centerY + i * scale);
        ctx.lineTo(canvas.width, centerY + i * scale);
        ctx.stroke();
      }

      // Draw robot position
      ctx.fillStyle = '#64b5f6';
      ctx.fillRect(centerX - 5, centerY - 5, 10, 10);

      // Draw safe paths
      ctx.strokeStyle = '#4caf50';
      ctx.lineWidth = 3;
      terrainAnalysis.safe_paths.forEach(path => {
        const angle = (path.angle * Math.PI) / 180;
        const endX = centerX + Math.cos(angle) * path.distance * scale;
        const endY = centerY - Math.sin(angle) * path.distance * scale;
        
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(endX, endY);
        ctx.stroke();
      });

      // Draw obstacles
      ctx.fillStyle = '#f44336';
      terrainAnalysis.obstacles.forEach(obstacle => {
        const angle = (obstacle.angle * Math.PI) / 180;
        const x = centerX + Math.cos(angle) * obstacle.distance * scale;
        const y = centerY - Math.sin(angle) * obstacle.distance * scale;
        
        ctx.fillRect(x - 3, y - 3, 6, 6);
      });
    }
  }, [terrainAnalysis]);

  return (
    <div className="advanced-dashboard">
      <header className="dashboard-header">
        <h1>🚀 LunarBot Advanced Mission Control</h1>
        <div className="connection-status">
          <span className={`status-indicator ${robotStatus.connected ? 'connected' : 'disconnected'}`}>
            {robotStatus.connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </header>

      <div className="dashboard-grid">
        {/* Control Panel */}
        <div className="panel control-panel">
          <h3>🎮 Robot Control</h3>
          
          <div className="control-grid">
            <button className="control-btn forward" onClick={() => moveRobot('forward')}>
              ↑ Forward
            </button>
            <button className="control-btn backward" onClick={() => moveRobot('backward')}>
              ↓ Backward
            </button>
            <button className="control-btn left" onClick={() => moveRobot('left')}>
              ← Turn Left
            </button>
            <button className="control-btn right" onClick={() => moveRobot('right')}>
              → Turn Right
            </button>
          </div>

          <button className="control-btn emergency" onClick={emergencyStop}>
            🚨 Emergency Stop
          </button>

          <div className="coordinate-input">
            <div className="input-group">
              <label>X Coordinate</label>
              <input type="number" id="x-coord" placeholder="0.0" step="0.1" />
            </div>
            <div className="input-group">
              <label>Y Coordinate</label>
              <input type="number" id="y-coord" placeholder="0.0" step="0.1" />
            </div>
          </div>

          <button 
            className="navigate-btn" 
            onClick={() => {
              const x = parseFloat(document.getElementById('x-coord').value) || 0;
              const y = parseFloat(document.getElementById('y-coord').value) || 0;
              navigateToCoordinates(x, y);
            }}
          >
            🎯 Navigate to Coordinates
          </button>
        </div>

        {/* Status Panel */}
        <div className="panel status-panel">
          <h3>📊 Robot Status</h3>
          
          <div className="status-grid">
            <div className="status-item">
              <div className="status-label">Battery Level</div>
              <div className="status-value">{robotStatus.battery_level.toFixed(1)}%</div>
              <div className="battery-bar">
                <div 
                  className="battery-fill"
                  style={{ width: `${robotStatus.battery_level}%` }}
                />
              </div>
            </div>

            <div className="status-item">
              <div className="status-label">Temperature</div>
              <div className="status-value">{robotStatus.temperature.toFixed(1)}°C</div>
            </div>

            <div className="status-item">
              <div className="status-label">Position</div>
              <div className="status-value">
                ({robotStatus.position.x.toFixed(1)}, {robotStatus.position.y.toFixed(1)})
              </div>
            </div>

            <div className="status-item">
              <div className="status-label">Navigation Status</div>
              <div className="status-value">{robotStatus.navigation_status}</div>
            </div>
          </div>

          <div className="mission-stats">
            <div className="stat-item">
              <div className="stat-value">{missionData.distance_traveled.toFixed(1)}</div>
              <div className="stat-label">Distance (m)</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{missionData.samples_collected}</div>
              <div className="stat-label">Samples</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{Math.floor(robotStatus.mission_time / 60)}</div>
              <div className="stat-label">Time (min)</div>
            </div>
          </div>
        </div>

        {/* Terrain Analysis Panel */}
        <div className="panel terrain-panel">
          <h3>🌙 Terrain Analysis</h3>
          
          <div 
            className="upload-area"
            onClick={() => fileInputRef.current.click()}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="upload-icon">📷</div>
            <div className="upload-text">Upload Terrain Image</div>
            <div className="upload-subtext">Click to upload or drag & drop</div>
            <div className="upload-formats">Supports: JPG, PNG, WebP</div>
          </div>

          <input 
            ref={fileInputRef}
            type="file" 
            accept="image/*" 
            style={{ display: 'none' }} 
            onChange={handleImageUpload}
          />

          {uploadedImage && (
            <div className="uploaded-image">
              <img src={uploadedImage} alt="Uploaded terrain" />
            </div>
          )}

          {isAnalyzing && (
            <div className="analysis-loading">
              <div className="loading-spinner"></div>
              <div>Analyzing terrain...</div>
            </div>
          )}

          {analysisResult && (
            <div className="analysis-result">
              <div className={`recommendation ${analysisResult.recommendation.toLowerCase().replace(/_/g, '-')}`}>
                {analysisResult.recommendation.replace(/_/g, ' ')}
              </div>
              <div className="analysis-details">
                <div><strong>Navigability Score:</strong> {analysisResult.navigability_score}/100</div>
                <div><strong>Craters Detected:</strong> {analysisResult.craters_detected}</div>
                <div><strong>Obstacles Detected:</strong> {analysisResult.obstacles_detected}</div>
                <div><strong>Confidence:</strong> {analysisResult.confidence}</div>
              </div>
            </div>
          )}

          <div className="terrain-visualization">
            <canvas ref={canvasRef} width="400" height="300" />
          </div>
        </div>

        {/* Mission Data Panel */}
        <div className="panel mission-panel">
          <h3>🛰️ Mission Data</h3>
          
          <div className="status-grid">
            <div className="status-item">
              <div className="status-label">Radiation Level</div>
              <div className="status-value">{robotStatus.radiation_level.toFixed(2)}</div>
            </div>

            <div className="status-item">
              <div className="status-label">Navigability Score</div>
              <div className="status-value">{terrainAnalysis.navigability_score.toFixed(0)}</div>
            </div>

            <div className="status-item">
              <div className="status-label">Safe Paths</div>
              <div className="status-value">{terrainAnalysis.safe_paths.length}</div>
            </div>

            <div className="status-item">
              <div className="status-label">Obstacles</div>
              <div className="status-value">{terrainAnalysis.obstacles.length}</div>
            </div>
          </div>

          <div className="mission-log">
            <h4>Mission Log</h4>
            <div className="log-content">
              <div>[00:00:00] LunarBot initialized and ready for mission...</div>
              {analysisResult && (
                <div>[{new Date().toLocaleTimeString()}] Terrain analysis complete: {analysisResult.recommendation}</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdvancedLunarBotDashboard;
