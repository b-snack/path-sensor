"""
Ground Detector
"""

import time

class GroundDetector:
    """Detect ground-level hazards using downward-facing sensor"""
    
    def __init__(self, config):
        """Initialize ground detector"""
        self.config = config
        self.baseline_distance = None  # Calibrated ground distance
        self.calibration_readings = []
        self.calibrated = False
        
        print("✓ Ground hazard detector initialized")
    
    def calibrate(self, readings):
        """
        Calibrate baseline ground distance
        User should walk on flat ground for calibration
        
        Args:
            readings (dict): Sensor readings including 'ground_sensor'
        """
        if 'ground_sensor' not in readings or readings['ground_sensor'] is None:
            return
        
        self.calibration_readings.append(readings['ground_sensor'])
        
        if len(self.calibration_readings) >= self.config.GROUND_CALIBRATION_SAMPLES:
            # Average of middle 80% (remove outliers)
            sorted_readings = sorted(self.calibration_readings)
            # Remove top and bottom 10%
            trim_count = len(sorted_readings) // 10
            if trim_count > 0:
                middle_readings = sorted_readings[trim_count:-trim_count]
            else:
                middle_readings = sorted_readings
            
            self.baseline_distance = sum(middle_readings) / len(middle_readings)
            self.calibrated = True
            
            print(f"  Ground baseline: {self.baseline_distance:.2f}m")
    
    def detect_hazard(self, current_distance):
        """
        Detect ground-level hazards
        
        Args:
            current_distance (float): Current distance to ground
        
        Returns:
            dict: Hazard information, or None if no hazard
        """
        if not self.calibrated or current_distance is None:
            return None
        
        deviation = current_distance - self.baseline_distance
        
        # Sudden increase in distance = ground dropped away
        if deviation > self.config.POTHOLE_THRESHOLD:
            severity = 'critical' if deviation > self.config.MAJOR_DROP_THRESHOLD else 'warning'
            return {
                'type': 'drop_off',
                'depth': deviation,
                'severity': severity,
                'description': self._classify_drop(deviation)
            }
        
        # Sudden decrease in distance = raised obstacle
        elif deviation < -self.config.CURB_THRESHOLD:
            return {
                'type': 'raised_surface',
                'height': abs(deviation),
                'severity': 'warning',
                'description': self._classify_rise(abs(deviation))
            }
        
        # Gradual change = slope or ramp
        elif abs(deviation) > 0.05:
            return {
                'type': 'slope',
                'change': deviation,
                'severity': 'info',
                'description': 'Sloped surface detected'
            }
        
        return None  # Ground is normal
    
    def _classify_drop(self, depth):
        """
        Classify type of drop-off based on depth
        
        Args:
            depth (float): Depth of drop in meters
            
        Returns:
            str: Description of drop type
        """
        if depth < 0.15:
            return "Small depression"
        elif depth < 0.20:
            return "Pothole detected"
        elif depth < 0.30:
            return "Curb or step down"
        elif depth < 0.50:
            return "Large drop-off"
        else:
            return "Stairs or major drop - DANGER"
    
    def _classify_rise(self, height):
        """
        Classify type of raised surface based on height
        
        Args:
            height (float): Height of rise in meters
            
        Returns:
            str: Description of rise type
        """
        if height < 0.10:
            return "Small bump or crack"
        elif height < 0.15:
            return "Curb detected"
        elif height < 0.20:
            return "Step up ahead"
        else:
            return "Stairs or large obstacle"
    
    def detect_ice_surface(self, signal_strength, reflection_quality):
        """
        Detect potential ice patches based on ultrasonic reflection
        Ice creates very clean, strong reflections vs rough pavement
        
        Args:
            signal_strength (float): Strength of return signal (0-1)
            reflection_quality (float): Quality/clarity of reflection (0-1)
            
        Returns:
            dict: Ice detection result, or None
        """
        # Ice has very smooth surface = strong, clear reflection
        if signal_strength > 0.85 and reflection_quality > 0.85:
            return {
                'type': 'possible_ice',
                'confidence': 0.7,
                'description': 'Smooth surface - possible ice',
                'severity': 'warning'
            }
        
        return None
    
    def get_calibration_status(self):
        """Get calibration status information"""
        return {
            'calibrated': self.calibrated,
            'samples_collected': len(self.calibration_readings),
            'samples_needed': self.config.GROUND_CALIBRATION_SAMPLES,
            'baseline_distance': self.baseline_distance
        }