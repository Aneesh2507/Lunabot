#!/usr/bin/env python3
"""
LunarBot Simulation Launcher
Choose between different simulation modes
"""

import sys
import os
import subprocess
import time

def print_banner():
    """Print welcome banner"""
    print("=" * 70)
    print("🚀 LunarBot Navigation Simulator Launcher")
    print("=" * 70)
    print("Choose your simulation mode:")
    print()

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = {
        'pygame': 'pygame',
        'flask': 'flask',
        'numpy': 'numpy'
    }
    
    missing_packages = []
    
    for package, pip_name in required_packages.items():
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(pip_name)
    
    if missing_packages:
        print("⚠️  Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print()
        print("Install them with:")
        print(f"   pip install {' '.join(missing_packages)}")
        print()
        return False
    
    return True

def run_pygame_simulator():
    """Run the pygame-based simulator"""
    print("🎮 Starting Pygame LunarBot Simulator...")
    print("Controls:")
    print("  WASD - Move bot")
    print("  SPACE - Stop")
    print("  N - Toggle navigation mode")
    print("  Click - Set navigation target")
    print("  ESC - Exit")
    print()
    
    try:
        import lunarbot_navigation_simulator
        lunarbot_navigation_simulator.main()
    except ImportError:
        print("❌ Pygame simulator not found. Make sure lunarbot_navigation_simulator.py exists.")
    except Exception as e:
        print(f"❌ Error running pygame simulator: {e}")

def run_web_simulator():
    """Run the web-based simulator"""
    print("🌐 Starting Web-based LunarBot Simulator...")
    print("The simulator will be available at: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print()
    
    try:
        import web_navigation_simulator
        # The web simulator will start automatically
    except ImportError:
        print("❌ Web simulator not found. Make sure web_navigation_simulator.py exists.")
    except Exception as e:
        print(f"❌ Error running web simulator: {e}")

def run_console_demo():
    """Run the console-based demo"""
    print("💻 Starting Console LunarBot Demo...")
    print("This is a text-based simulation with bot movement controls")
    print()
    
    try:
        import navigation_demo
        navigation_demo.main()
    except ImportError:
        print("❌ Console demo not found. Make sure navigation_demo.py exists.")
    except Exception as e:
        print(f"❌ Error running console demo: {e}")

def main():
    """Main launcher function"""
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        print("Please install missing dependencies and try again.")
        return
    
    while True:
        print("Available simulation modes:")
        print("1. 🎮 Pygame Visual Simulator (Real-time graphics)")
        print("2. 🌐 Web-based Simulator (Browser interface)")
        print("3. 💻 Console Demo (Text-based simulation)")
        print("4. ❓ Help & Information")
        print("5. 🚪 Exit")
        print()
        
        try:
            choice = input("Enter your choice (1-5): ").strip()
            
            if choice == '1':
                run_pygame_simulator()
            elif choice == '2':
                run_web_simulator()
            elif choice == '3':
                run_console_demo()
            elif choice == '4':
                show_help()
            elif choice == '5':
                print("👋 Goodbye! Thanks for using LunarBot Simulator!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-5.")
            
            print("\n" + "="*50 + "\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye! Thanks for using LunarBot Simulator!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

def show_help():
    """Show help information"""
    print("\n" + "="*60)
    print("📚 LunarBot Simulator Help")
    print("="*60)
    print()
    print("This simulator demonstrates autonomous navigation on lunar terrain")
    print("with a visual bot figure that can navigate through safe paths.")
    print()
    print("Features:")
    print("• Visual bot representation with direction indicator")
    print("• Safe path detection and navigation")
    print("• Obstacle avoidance")
    print("• Real-time movement controls (forward, backward, left, right)")
    print("• Battery simulation")
    print("• Multiple simulation modes")
    print()
    print("Simulation Modes:")
    print("1. Pygame Simulator: Real-time graphics with mouse controls")
    print("2. Web Simulator: Browser-based interface with WebSocket")
    print("3. Console Demo: Text-based simulation with keyboard controls")
    print()
    print("Bot Controls:")
    print("• W/S: Move forward/backward")
    print("• A/D: Turn left/right")
    print("• SPACE: Emergency stop")
    print("• Click: Set navigation target (visual modes)")
    print()
    print("Files:")
    print("• lunarbot_navigation_simulator.py - Pygame simulator")
    print("• web_navigation_simulator.py - Web-based simulator")
    print("• navigation_demo.py - Console demo")
    print("• templates/navigation_simulator.html - Web interface")
    print()
    print("Requirements:")
    print("• Python 3.7+")
    print("• pygame (for visual simulator)")
    print("• flask, flask-socketio (for web simulator)")
    print("• numpy (for calculations)")
    print("="*60)

if __name__ == "__main__":
    main()
