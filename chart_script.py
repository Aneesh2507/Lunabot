import plotly.graph_objects as go
import numpy as np

# Define the components and their positions in a hierarchical layout
components = [
    {"name": "Simulation Env", "tech": "Gazebo/Isaac Sim<br>Lunar DEM<br>Physics Engine", "x": 0.5, "y": 0.9, "color": "#B3E5EC"},
    {"name": "ROS2 Nav Stack", "tech": "Nav2, SLAM<br>AMCL, Move Base", "x": 0.3, "y": 0.7, "color": "#A5D6A7"},
    {"name": "Perception Sys", "tech": "YOLO v8<br>DeepLabV3<br>PyTorch/OpenCV", "x": 0.7, "y": 0.7, "color": "#FFEB8A"},
    {"name": "Web Interface", "tech": "React Frontend<br>Flask Backend<br>WebSocket/rosbridge", "x": 0.5, "y": 0.5, "color": "#FFCDD2"},
    {"name": "Control System", "tech": "Motor Controllers<br>Safety Systems<br>PID Control", "x": 0.5, "y": 0.3, "color": "#9FA8B0"}
]

# Define connections between components
connections = [
    (0, 1),  # Simulation -> Navigation
    (0, 2),  # Simulation -> Perception
    (1, 3),  # Navigation -> Web Interface
    (2, 3),  # Perception -> Web Interface
    (1, 4),  # Navigation -> Control
    (2, 4),  # Perception -> Control
    (3, 4),  # Web Interface -> Control
]

# Create the figure
fig = go.Figure()

# Add connection lines first (so they appear behind nodes)
for conn in connections:
    start_comp = components[conn[0]]
    end_comp = components[conn[1]]
    
    fig.add_trace(go.Scatter(
        x=[start_comp["x"], end_comp["x"]],
        y=[start_comp["y"], end_comp["y"]],
        mode='lines',
        line=dict(color='#333333', width=2),
        showlegend=False,
        hoverinfo='skip'
    ))

# Add bidirectional arrows for Web Interface <-> Navigation and Perception
bidirectional = [(3, 1), (3, 2)]  # Web Interface with Navigation and Perception

for conn in bidirectional:
    start_comp = components[conn[0]]
    end_comp = components[conn[1]]
    
    # Add dashed line for bidirectional communication
    fig.add_trace(go.Scatter(
        x=[start_comp["x"], end_comp["x"]],
        y=[start_comp["y"], end_comp["y"]],
        mode='lines',
        line=dict(color='#1FB8CD', width=3, dash='dash'),
        showlegend=False,
        hoverinfo='skip'
    ))

# Add component boxes
for i, comp in enumerate(components):
    fig.add_trace(go.Scatter(
        x=[comp["x"]],
        y=[comp["y"]],
        mode='markers+text',
        marker=dict(
            size=120,
            color=comp["color"],
            line=dict(color='#333333', width=2),
            symbol='square'
        ),
        text=f"<b>{comp['name']}</b><br>{comp['tech']}",
        textposition="middle center",
        textfont=dict(size=11, color='#133343'),
        showlegend=False,
        hovertemplate=f"<b>{comp['name']}</b><br>{comp['tech'].replace('<br>', ', ')}<extra></extra>"
    ))

# Add layer labels on the left
layer_labels = [
    {"text": "Simulation Layer", "y": 0.9, "color": "#1FB8CD"},
    {"text": "Middleware Layer", "y": 0.7, "color": "#2E8B57"},
    {"text": "Interface Layer", "y": 0.5, "color": "#DB4545"},
    {"text": "Control Layer", "y": 0.3, "color": "#5D878F"}
]

for label in layer_labels:
    fig.add_trace(go.Scatter(
        x=[0.05],
        y=[label["y"]],
        mode='text',
        text=f"<b>{label['text']}</b>",
        textfont=dict(size=12, color=label["color"]),
        showlegend=False,
        hoverinfo='skip'
    ))

# Add title and layout
fig.update_layout(
    title="LunarBot System Architecture",
    xaxis=dict(
        range=[-0.1, 1.1],
        showgrid=False,
        showticklabels=False,
        zeroline=False
    ),
    yaxis=dict(
        range=[0.1, 1.0],
        showgrid=False,
        showticklabels=False,
        zeroline=False
    ),
    plot_bgcolor='white',
    showlegend=False
)

# Save as both PNG and SVG
fig.write_image("lunarbot_architecture.png")
fig.write_image("lunarbot_architecture.svg", format="svg")

print("LunarBot system architecture diagram created successfully!")
print("Components arranged in hierarchical layers with data flow connections.")
print("Bidirectional communication shown between Web Interface and middleware components.")