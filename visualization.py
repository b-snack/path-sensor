"""
Visualization - real time data
"""

import time
import os
import sys

class PathSenseVisualizer:
    """Simple console visualization of sensor data"""
    
    def __init__(self):
        """Initialize visualizer"""
        self.last_data = {}
        self.alerts = []
        self.update_count = 0
    
    def update(self, sensor_data, ground_hazard=None):
        """
        Update display with new sensor data
        
        Args:
            sensor_data (dict): Sensor readings
            ground_hazard (dict): Ground hazard info if any
        """
        self.last_data = sensor_data
        self.update_count += 1
        
        if ground_hazard:
            self.alerts.append(ground_hazard)
            # Keep only last 5 alerts
            self.alerts = self.alerts[-5:]
        
        self._render()
    
    def _render(self):
        """Render current state to console"""
        # Clear screen
        self._clear_screen()
        
        print("=" * 70)
        print("  PathSense - Real-Time Obstacle Detection System")
        print("=" * 70)
        print()
        
        # Upper sensors
        print("┌─ UPPER BODY SENSORS ────────────────────────────────────────┐")
        print("│                                                              │")
        
        for sensor_name in ['front_high', 'front_center', 'front_low', 'left_side', 'right_side']:
            if sensor_name in self.last_data:
                distance = self.last_data[sensor_name]
                self._render_sensor(sensor_name, distance)
        
        print("│                                                              │")
        print("└──────────────────────────────────────────────────────────────┘")
        print()
        
        # Ground sensor
        print("┌─ GROUND HAZARD DETECTION ───────────────────────────────────┐")
        print("│                                                              │")
        
        if 'ground_sensor' in self.last_data:
            distance = self.last_data['ground_sensor']
            self._render_sensor('ground_sensor', distance, is_ground=True)
        
        print("│                                                              │")
        print("└──────────────────────────────────────────────────────────────┘")
        
        # Recent alerts
        if self.alerts:
            print()
            print("┌─ RECENT GROUND HAZARDS ─────────────────────────────────────┐")
            for alert in self.alerts[-3:]:
                severity_icon = "⚠️ " if alert['severity'] == 'critical' else "⚡" if alert['severity'] == 'warning' else "ℹ️ "
                print(f"│ {severity_icon} {alert['description']:55} │")
            print("└──────────────────────────────────────────────────────────────┘")
        
        print()
        print(f"Updates: {self.update_count}  |  Press Ctrl+C to stop")
    
    def _render_sensor(self, sensor_name, distance, is_ground=False):
        """Render individual sensor reading"""
        # Format sensor name
        display_name = sensor_name.replace('_', ' ').title()
        
        if distance is None:
            status = "NO READING"
            bar = "─" * 20
            color_code = ""
        elif distance < 0.5:
            status = "⚠️  DANGER  "
            bar = self._create_bar(distance, 4.0, '█')
            color_code = ""
        elif distance < 1.5:
            status = "⚡ WARNING "
            bar = self._create_bar(distance, 4.0, '▓')
            color_code = ""
        elif distance < 3.0:
            status = "ℹ️  ALERT   "
            bar = self._create_bar(distance, 4.0, '▒')
            color_code = ""
        else:
            status = "✓  CLEAR   "
            bar = self._create_bar(distance, 4.0, '░')
            color_code = ""
        
        # Format distance
        dist_str = f"{distance:5.2f}m" if distance else "  N/A  "
        
        print(f"│ {display_name:16} {dist_str}  [{bar}] {status:12} │")
    
    def _create_bar(self, value, max_value, char):
        """Create visual bar for distance"""
        bar_length = 20
        if value is None:
            return "─" * bar_length
        
        filled = int((value / max_value) * bar_length)
        filled = min(filled, bar_length)
        empty = bar_length - filled
        
        return f"{char * filled}{'·' * empty}"
    
    def _clear_screen(self):
        """Clear console screen"""
        # Works on Unix/Linux/Mac and Windows
        os.system('clear' if os.name == 'posix' else 'cls')


def demo():
    """Demo visualization with PathSense"""
    print("Starting PathSense Visualization Demo...")
    print("This will show real-time sensor data.")
    print()
    
    # Import main PathSense
    try:
        from main import PathSense
        
        visualizer = PathSenseVisualizer()
        pathsense = PathSense()
        pathsense.start()
        
        print("\nVisualization will start in 3 seconds...")
        time.sleep(3)
        
        try:
            while True:
                # Get sensor data
                sensor_data = pathsense.sensor_controller.read_all_sensors()
                
                # Check for ground hazards
                ground_hazard = None
                if pathsense.ground_detector.calibrated:
                    if 'ground_sensor' in sensor_data and sensor_data['ground_sensor']:
                        ground_hazard = pathsense.ground_detector.detect_hazard(
                            sensor_data['ground_sensor']
                        )
                
                # Update visualization
                visualizer.update(sensor_data, ground_hazard)
                
                time.sleep(0.5)  # Update every 0.5 seconds for smooth display
                
        except KeyboardInterrupt:
            print("\n\nStopping visualization...")
            pathsense.stop()
            
    except ImportError as e:
        print(f"Error: Could not import PathSense: {e}")
        print("Make sure all PathSense files are in the same directory.")


if __name__ == "__main__":
    demo()