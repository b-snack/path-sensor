"""
PathSense - Wearable Obstacle Detection System
Main application file for sensor processing and haptic feedback control
Author: PathSense Team
Date: January 2026
"""

import time
import threading
from sensor_controller import SensorController
from haptic_controller import HapticController
from data_logger import DataLogger
from ground_detector import GroundDetector
from winter_optimizer import WinterOptimizer
from config import Config

class PathSense:
    """Main application class for PathSense obstacle detection system"""
    
    def __init__(self):
        """Initialize PathSense system components"""
        print("Initializing PathSense...")
        print("=" * 60)
        
        # Load configuration
        self.config = Config()
        
        # Initialize controllers
        self.sensor_controller = SensorController(self.config)
        self.haptic_controller = HapticController(self.config)
        self.data_logger = DataLogger(self.config)
        self.ground_detector = GroundDetector(self.config)
        self.winter_optimizer = WinterOptimizer(self.config)
        
        # System state
        self.running = False
        self.detection_thread = None
        self.start_time = None
        self.total_detections = 0
        
        print("PathSense initialized successfully!")
        print("=" * 60)
    
    def start(self):
        """Start the obstacle detection system"""
        if self.running:
            print("PathSense is already running")
            return
        
        print("\nStarting PathSense obstacle detection...")
        print("Calibrating ground sensor...")
        
        self.running = True
        self.start_time = time.time()
        
        # Start detection in separate thread
        self.detection_thread = threading.Thread(target=self._detection_loop)
        self.detection_thread.daemon = True
        self.detection_thread.start()
        
        print("✓ PathSense is now active!")
        print(f"✓ Winter optimization: {self.config.SNOW_FILTER_ENABLED}")
        print(f"✓ Ground hazard detection: ENABLED")
        print(f"✓ Sensors active: {len(self.config.SENSORS) + 1}")  # +1 for ground sensor
        print()
    
    def stop(self):
        """Stop the obstacle detection system"""
        print("\nStopping PathSense...")
        self.running = False
        
        if self.detection_thread:
            self.detection_thread.join(timeout=2.0)
        
        # Stop all haptic feedback
        self.haptic_controller.stop_all()
        
        # Print session summary
        self._print_summary()
        
        print("PathSense stopped")
    
    def _detection_loop(self):
        """Main detection loop - runs continuously"""
        calibration_count = 0
        sensor_history = {name: [] for name in self.config.SENSORS}
        
        while self.running:
            try:
                # Read all sensors
                sensor_data = self.sensor_controller.read_all_sensors()
                
                # Ground sensor calibration (first 5 seconds)
                if not self.ground_detector.calibrated and calibration_count < 50:
                    if 'ground_sensor' in sensor_data and sensor_data['ground_sensor']:
                        self.ground_detector.calibrate(sensor_data)
                        calibration_count += 1
                        if self.ground_detector.calibrated:
                            print("✓ Ground sensor calibrated!")
                
                # Apply winter optimizations
                if self.config.SNOW_FILTER_ENABLED:
                    sensor_data = self.winter_optimizer.filter_snow_particles(
                        sensor_data, sensor_history
                    )
                
                # Update sensor history
                for sensor_name, distance in sensor_data.items():
                    if distance is not None:
                        if sensor_name not in sensor_history:
                            sensor_history[sensor_name] = []
                        sensor_history[sensor_name].append(distance)
                        # Keep only last 5 readings
                        sensor_history[sensor_name] = sensor_history[sensor_name][-5:]
                
                # Process upper-body obstacles
                for sensor_name, distance in sensor_data.items():
                    if sensor_name != 'ground_sensor' and distance is not None:
                        self._process_obstacle(sensor_name, distance)
                
                # Process ground hazards
                if 'ground_sensor' in sensor_data and sensor_data['ground_sensor']:
                    hazard = self.ground_detector.detect_hazard(sensor_data['ground_sensor'])
                    if hazard:
                        self._process_ground_hazard(hazard)
                
                # Log data for analysis
                self.data_logger.log_sensor_data(sensor_data)
                
                # Small delay to prevent CPU overload
                time.sleep(self.config.SCAN_INTERVAL)
                
            except Exception as e:
                print(f"Error in detection loop: {e}")
                time.sleep(0.5)
    
    def _process_obstacle(self, sensor_name, distance):
        """
        Process obstacle detection and trigger appropriate haptic feedback
        
        Args:
            sensor_name (str): Name of the sensor (e.g., 'front_center', 'left_side')
            distance (float): Distance to obstacle in meters
        """
        # Apply temperature compensation
        distance = self.winter_optimizer.adjust_for_temperature(distance)
        
        # Determine danger level based on distance
        if distance < self.config.DANGER_ZONE:
            # Critical - strong rapid vibration
            self.haptic_controller.alert(sensor_name, intensity='high', pattern='rapid')
            self.data_logger.log_event('danger', sensor_name, distance)
            self.total_detections += 1
            
        elif distance < self.config.WARNING_ZONE:
            # Warning - moderate pulsing vibration
            self.haptic_controller.alert(sensor_name, intensity='medium', pattern='pulse')
            self.data_logger.log_event('warning', sensor_name, distance)
            
        elif distance < self.config.ALERT_ZONE:
            # Alert - gentle intermittent vibration
            self.haptic_controller.alert(sensor_name, intensity='low', pattern='intermittent')
            self.data_logger.log_event('alert', sensor_name, distance)
            
        else:
            # No obstacle in range - stop vibration for this sensor
            self.haptic_controller.stop(sensor_name)
    
    def _process_ground_hazard(self, hazard):
        """
        Process ground hazard and trigger appropriate alerts
        
        Args:
            hazard (dict): Hazard information from ground detector
        """
        sensor_name = 'ground_sensor'
        
        if hazard['severity'] == 'critical':
            # Major drop - strong alert
            self.haptic_controller.alert('front_lower', intensity='high', pattern='rapid')
            print(f"⚠️  CRITICAL: {hazard['description']} - {hazard.get('depth', 0):.2f}m")
            self.data_logger.log_event('ground_critical', sensor_name, hazard)
            
        elif hazard['severity'] == 'warning':
            # Moderate hazard - warning alert
            self.haptic_controller.alert('front_lower', intensity='medium', pattern='pulse')
            print(f"⚡ WARNING: {hazard['description']}")
            self.data_logger.log_event('ground_warning', sensor_name, hazard)
            
        else:
            # Info only - gentle alert
            self.haptic_controller.alert('front_lower', intensity='low', pattern='intermittent')
    
    def get_status(self):
        """Get current system status"""
        return {
            'running': self.running,
            'sensors_active': len(self.config.SENSORS) + 1,
            'battery_level': self._get_battery_level(),
            'uptime': time.time() - self.start_time if self.start_time else 0,
            'total_detections': self.total_detections,
            'ground_calibrated': self.ground_detector.calibrated,
            'winter_mode': self.config.SNOW_FILTER_ENABLED
        }
    
    def _get_battery_level(self):
        """Get battery level (placeholder - would read from actual battery monitor)"""
        # This would interface with actual battery monitoring hardware
        return 85.0  # Percentage
    
    def _print_summary(self):
        """Print session summary"""
        if self.start_time:
            runtime = time.time() - self.start_time
            print("\n" + "=" * 60)
            print("SESSION SUMMARY")
            print("=" * 60)
            print(f"Runtime: {runtime:.1f} seconds ({runtime/60:.1f} minutes)")
            print(f"Total obstacle detections: {self.total_detections}")
            print(f"Winter optimization: {'Active' if self.config.SNOW_FILTER_ENABLED else 'Inactive'}")
            print("=" * 60)

def main():
    """Main entry point for PathSense application"""
    print("\n" + "=" * 60)
    print("  PathSense - Wearable Obstacle Detection System")
    print("  Comprehensive 3D Navigation for Blind Mobility")
    print("=" * 60)
    print("\nFeatures:")
    print("  ✓ 360° obstacle detection (head, chest, knee, sides)")
    print("  ✓ Ground hazard detection (potholes, curbs, stairs)")
    print("  ✓ Winter-optimized (snow filtering, temp compensation)")
    print("  ✓ Directional haptic feedback")
    print("  ✓ Data logging for analysis")
    print()
    
    # Create PathSense instance
    pathsense = PathSense()
    
    try:
        # Start detection
        pathsense.start()
        
        # Keep running until interrupted
        print("PathSense is running. Press Ctrl+C to stop.\n")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nShutdown requested...")
        
    finally:
        pathsense.stop()
        print("\nThank you for using PathSense!")
        print("Stay safe! 🦯\n")

if __name__ == "__main__":
    main()