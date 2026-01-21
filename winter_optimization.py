"""
Optimization Module for Winter
"""

import time
import math

class WinterOptimizer:
    """Optimize obstacle detection for winter conditions"""
    
    def __init__(self, config):
        """Initialize winter optimizer"""
        self.config = config
        self.temperature = config.DEFAULT_TEMPERATURE  # Celsius
        self.snow_filter_enabled = config.SNOW_FILTER_ENABLED
        
        print(f"✓ Winter optimization initialized (temp: {self.temperature}°C)")
    
    def set_temperature(self, temperature):
        """
        Set current temperature for calculations
        
        Args:
            temperature (float): Current temperature in Celsius
        """
        self.temperature = temperature
    
    def adjust_for_temperature(self, distance_reading, temperature=None):
        """
        Adjust ultrasonic reading for cold temperature effects
        
        Speed of sound changes with temperature:
        v = 331.3 + (0.606 * temp_celsius) m/s
        
        At -20°C, sound travels ~4% slower than at 20°C
        
        Args:
            distance_reading (float): Raw distance measurement
            temperature (float): Current temperature in Celsius (optional)
            
        Returns:
            float: Temperature-compensated distance
        """
        if not self.config.COLD_TEMP_COMPENSATION:
            return distance_reading
        
        if distance_reading is None:
            return None
        
        if temperature is None:
            temperature = self.temperature
        
        # Standard speed of sound at 20°C
        standard_speed = 343.0  # m/s
        
        # Actual speed at current temperature
        actual_speed = 331.3 + (0.606 * temperature)
        
        # Compensation factor
        factor = actual_speed / standard_speed
        
        # Adjust distance
        compensated_distance = distance_reading * factor
        
        return round(compensated_distance, 2)
    
    def filter_snow_particles(self, sensor_readings, history_buffer):
        """
        Distinguish between solid obstacles and airborne snow particles
        
        Snow particles characteristics:
        - Small, moving rapidly
        - Inconsistent readings (high variance)
        - Brief detections
        
        Solid obstacles characteristics:
        - Large, stationary or slowly moving
        - Consistent readings (low variance)
        - Persistent detections
        
        Args:
            sensor_readings (dict): Current sensor readings
            history_buffer (dict): Last N readings for each sensor
            
        Returns:
            dict: Filtered readings with snow particles removed
        """
        if not self.snow_filter_enabled:
            return sensor_readings
        
        filtered = {}
        
        for sensor_name, current_distance in sensor_readings.items():
            if current_distance is None:
                filtered[sensor_name] = None
                continue
            
            # Get history for this sensor
            sensor_history = history_buffer.get(sensor_name, [])
            
            if len(sensor_history) < 3:
                # Not enough history, accept reading
                filtered[sensor_name] = current_distance
                continue
            
            # Calculate variance in recent readings
            variance = self._calculate_variance(sensor_history)
            
            # Calculate rate of change
            if len(sensor_history) >= 2:
                rate_of_change = abs(sensor_history[-1] - sensor_history[-2])
            else:
                rate_of_change = 0
            
            # High variance + rapid change = likely snow particles
            # Low variance + slow change = likely solid obstacle
            if variance > 0.4 or rate_of_change > 0.5:
                # Erratic readings, likely snow particles or moving objects
                # Require multiple consistent readings before alerting
                if self._is_consistent_obstacle(sensor_history, current_distance):
                    filtered[sensor_name] = current_distance
                else:
                    filtered[sensor_name] = None
            else:
                # Consistent readings, likely solid obstacle
                filtered[sensor_name] = current_distance
        
        return filtered
    
    def _is_consistent_obstacle(self, history, current):
        """
        Check if readings indicate a consistent obstacle
        
        Args:
            history (list): Historical readings
            current (float): Current reading
            
        Returns:
            bool: True if obstacle is consistent
        """
        if len(history) < 3:
            return False
        
        # Check if last 3 readings are all within 20cm of each other
        recent = history[-3:] + [current]
        max_val = max(recent)
        min_val = min(recent)
        
        return (max_val - min_val) < 0.2  # Within 20cm = consistent
    
    def _calculate_variance(self, readings):
        """
        Calculate variance in a list of readings
        
        Args:
            readings (list): List of distance readings
            
        Returns:
            float: Variance value
        """
        if not readings or len(readings) < 2:
            return 0.0
        
        # Remove None values
        valid_readings = [r for r in readings if r is not None]
        if len(valid_readings) < 2:
            return 0.0
        
        mean = sum(valid_readings) / len(valid_readings)
        variance = sum((x - mean) ** 2 for x in valid_readings) / len(valid_readings)
        
        return variance
    
    def detect_snow_bank(self, side_sensors, ground_sensor):
        """
        Detect snow banks pushed to sides of paths
        
        Args:
            side_sensors (dict): Left and right sensor readings
            ground_sensor (float): Ground sensor reading
            
        Returns:
            dict: Snow bank detection info, or None
        """
        # Snow banks appear as:
        # - Close readings on side sensors
        # - Elevated ground level
        # - Gradual slope
        
        left_close = side_sensors.get('left_side', 999) < 1.0
        right_close = side_sensors.get('right_side', 999) < 1.0
        
        if left_close or right_close:
            return {
                'detected': True,
                'side': 'left' if left_close else 'right',
                'description': 'Snow bank detected on path edge'
            }
        
        return None
    
    def get_winter_advisory(self):
        """
        Generate advisory message based on current conditions
        
        Returns:
            str: Advisory message for user
        """
        temp = self.temperature
        
        if temp < -30:
            return "⚠️  Extreme cold: Battery life significantly reduced"
        elif temp < -20:
            return "❄️  Very cold: Reduced battery life, caution advised"
        elif temp < -10:
            return "❄️  Cold conditions: Winter optimization active"
        elif temp < 0:
            return "🧊 Freezing: Watch for ice patches"
        elif temp < 5:
            return "🌡️  Cool: Normal operation"
        else:
            return "✓ Normal temperature: All systems optimal"
    
    def estimate_battery_impact(self, temperature):
        """
        Estimate battery life impact from cold
        
        Lithium batteries lose capacity in cold:
        -20°C = ~50% capacity
        -10°C = ~75% capacity
        
        Args:
            temperature (float): Temperature in Celsius
            
        Returns:
            float: Capacity multiplier (0-1)
        """
        if temperature >= 20:
            return 1.0  # Full capacity
        elif temperature >= 0:
            return 0.95  # Minimal impact
        elif temperature >= -10:
            return 0.75  # Moderate impact
        elif temperature >= -20:
            return 0.50  # Significant impact
        else:
            return 0.30  # Severe impact