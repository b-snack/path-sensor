"""
Sensor Controller
"""

import time

try:
    import RPi.GPIO as GPIO
    RASPBERRY_PI = True
except ImportError:
    RASPBERRY_PI = False
    print("⚠️  Warning: RPi.GPIO not available. Running in simulation mode.")

class SensorController:
    """Controller for managing multiple ultrasonic sensors"""
    
    def __init__(self, config):
        """Initialize sensor controller with configuration"""
        self.config = config
        self.sensors = config.SENSORS.copy()
        
        # Add ground sensor
        self.sensors['ground_sensor'] = config.GROUND_SENSOR
        
        if RASPBERRY_PI:
            # Set up GPIO pins
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            for sensor_name, pins in self.sensors.items():
                GPIO.setup(pins['trigger'], GPIO.OUT)
                GPIO.setup(pins['echo'], GPIO.IN)
                GPIO.output(pins['trigger'], False)
            
            # Let sensors settle
            time.sleep(0.1)
        
        print(f"✓ Initialized {len(self.sensors)} sensors")
        for sensor_name in self.sensors:
            print(f"  - {sensor_name}")
    
    def read_all_sensors(self):
        """
        Read distance from all sensors
        
        Returns:
            dict: Sensor name -> distance in meters
        """
        readings = {}
        
        for sensor_name in self.sensors:
            distance = self.read_sensor(sensor_name)
            readings[sensor_name] = distance
        
        return readings
    
    def read_sensor(self, sensor_name):
        """
        Read distance from a specific sensor
        
        Args:
            sensor_name (str): Name of sensor to read
            
        Returns:
            float: Distance in meters, or None if error
        """
        if sensor_name not in self.sensors:
            print(f"Error: Unknown sensor '{sensor_name}'")
            return None
        
        if RASPBERRY_PI:
            return self._read_ultrasonic_gpio(sensor_name)
        else:
            # Simulation mode - return realistic distances
            return self._simulate_reading(sensor_name)
    
    def _read_ultrasonic_gpio(self, sensor_name):
        """Read ultrasonic sensor using GPIO pins"""
        pins = self.sensors[sensor_name]
        trigger_pin = pins['trigger']
        echo_pin = pins['echo']
        
        try:
            # Send trigger pulse
            GPIO.output(trigger_pin, True)
            time.sleep(0.00001)  # 10 microsecond pulse
            GPIO.output(trigger_pin, False)
            
            # Wait for echo
            timeout = time.time() + 0.1  # 100ms timeout
            pulse_start = time.time()
            pulse_end = time.time()
            
            # Wait for echo to start
            while GPIO.input(echo_pin) == 0:
                pulse_start = time.time()
                if pulse_start > timeout:
                    return None  # Timeout
            
            # Wait for echo to end
            while GPIO.input(echo_pin) == 1:
                pulse_end = time.time()
                if pulse_end > timeout:
                    return None  # Timeout
            
            # Calculate distance
            pulse_duration = pulse_end - pulse_start
            distance = pulse_duration * 17150  # Speed of sound / 2 (in cm)
            distance = distance / 100  # Convert to meters
            
            # Validate reading
            if self.config.MIN_SENSOR_DISTANCE <= distance <= self.config.MAX_SENSOR_DISTANCE:
                return round(distance, 2)
            else:
                return None
                
        except Exception as e:
            print(f"Error reading sensor {sensor_name}: {e}")
            return None
    
    def _simulate_reading(self, sensor_name):
        """Simulate sensor reading for testing without hardware"""
        import random
        
        # Simulate different scenarios based on sensor position
        if sensor_name == 'ground_sensor':
            # Ground sensor - simulate flat ground with occasional hazards
            base_distance = 1.0  # 1 meter to ground
            variation = random.uniform(-0.05, 0.05)
            
            # Occasionally simulate a pothole or curb
            if random.random() < 0.05:  # 5% chance
                variation = random.uniform(0.2, 0.4)  # Pothole
            
            return round(base_distance + variation, 2)
        
        # Upper sensors - simulate various obstacle distances
        scenarios = {
            'front_high': random.uniform(1.5, 4.0),     # Overhead - usually clear
            'front_center': random.uniform(0.8, 3.5),   # Chest - occasional obstacles
            'front_low': random.uniform(1.0, 3.5),      # Knee - occasional obstacles
            'left_side': random.uniform(1.5, 4.0),      # Left - usually clear
            'right_side': random.uniform(1.5, 4.0)      # Right - usually clear
        }
        
        # Occasionally add close obstacles for testing
        distance = scenarios.get(sensor_name, 3.0)
        if random.random() < 0.1:  # 10% chance of close obstacle
            distance = random.uniform(0.3, 1.0)
        
        return round(distance, 2)
    
    def get_active_sensors(self):
        """Get list of active sensor names"""
        return list(self.sensors.keys())
    
    def cleanup(self):
        """Clean up GPIO resources"""
        if RASPBERRY_PI:
            GPIO.cleanup()
            print("GPIO cleaned up")