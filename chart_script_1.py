# Create a detailed navigation and perception pipeline flowchart
diagram_code = """
flowchart TD
    %% Input Sources
    A[("Input Sources<br/>Camera, LiDAR<br/>IMU, GPS<br/>30Hz")] 
    
    %% Perception Processing
    B["YOLO Object<br/>Detection<br/>10Hz"]
    C["DeepLabV3<br/>Segmentation<br/>10Hz"]
    D["Point Cloud<br/>Processing<br/>10Hz"]
    
    %% SLAM Components
    E["Feature<br/>Extraction<br/>20Hz"]
    F{"Loop Closure<br/>Detection?<br/>20Hz"}
    G["Map Building &<br/>Localization<br/>20Hz"]
    
    %% Path Planning
    H["Global Planner<br/>(A*)<br/>10Hz"]
    I["Local Planner<br/>(DWA)<br/>10Hz"]
    J["Obstacle<br/>Avoidance &<br/>Cost Map<br/>10Hz"]
    
    %% Control Output
    K[("Control Output<br/>Velocity, Steering<br/>Motor Commands<br/>50Hz")]
    
    %% Main data flow
    A --> B
    A --> C
    A --> D
    
    B --> E
    C --> E
    D --> E
    
    E --> F
    F -->|Yes| G
    F -->|No| H
    G --> H
    
    H --> I
    I --> J
    J --> K
    
    %% Feedback loops
    G -.->|Map Update| H
    K -.->|Odometry| G
    J -.->|Obstacles| I
    
    %% Styling for different types
    classDef inputOutput fill:#B3E5EC,stroke:#1FB8CD,stroke-width:3px
    classDef algorithm fill:#A5D6A7,stroke:#2E8B57,stroke-width:2px
    classDef decision fill:#FFEB8A,stroke:#D2BA4C,stroke-width:2px
    
    class A,K inputOutput
    class B,C,D,E,G,H,I,J algorithm
    class F decision
"""

# Create the mermaid diagram
png_path, svg_path = create_mermaid_diagram(diagram_code, "navigation_pipeline.png", "navigation_pipeline.svg", width=1400, height=1000)

print(f"Navigation pipeline flowchart saved as {png_path} and {svg_path}")