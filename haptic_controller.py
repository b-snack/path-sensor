"""
Haptic Controller - Manages vibration motors for directional feedback
"""

import time
import threading

try:
    import RPi.GPIO as GPIO
    RASPBERRY_PI = True
except ImportError:
    RASPBERRY_PI = False

class HapticController:
    """Controller for managing haptic feedback motors"""
    
    def __init__(self, config):
        """Initialize haptic controller"""
        self.config = config
        self.motors = config.HAPTIC_MOTORS
        self.active_alerts = {}  # Track active vibration threads
        self.motor_states = {name: False for name in self.motors}
        
        if RASPBERRY_PI:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            for motor_name, pin in self.motors.items():
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, False)
        
        print(f"✓ Initialized {len(self.motors)} haptic motors")
    
    def alert(self, sensor_name, intensity='medium', pattern='pulse'):
        """
        Trigger haptic alert for detected obstacle
        
        Args:
            sensor_name (str): Sensor that detected obstacle
            intensity (str): 'low', 'medium', or 'high'
            pattern (str): 'rapid', 'pulse', or 'intermittent'
        """
        # Map sensor to corresponding motor
        motor_name = self._sensor_to_motor(sensor_name)
        
        if motor_name not in self.motors:
            return
        
        # Stop existing alert for this motor if any
        if motor_name in self.active_alerts:
            self.active_alerts[motor_name]['stop'] = True
            time.sleep(0.05)  # Brief pause for cleanup
        
        # Start new alert thread
        alert_control = {'stop': False}
        alert_thread = threading.Thread(
            target=self._vibrate_pattern,
            args=(motor_name, intensity, pattern, alert_control)
        )
        alert_thread.daemon = True
        alert_thread.start()
        
        self.active_alerts[motor_name] = alert_control
    
    def stop(self, sensor_name):
        """Stop haptic alert for a specific sensor"""
        motor_name = self._sensor_to_motor(sensor_name)
        
        if motor_name in self.active_alerts:
            self.active_alerts[motor_name]['stop'] = True
            self._motor_off(motor_name)
    
    def stop_all(self):
        """Stop all haptic feedback"""
        for motor_name in list(self.active_alerts.keys()):
            self.active_alerts[motor_name]['stop'] = True
        
        time.sleep(0.1)  # Allow threads to stop
        
        # Turn off all motors
        for motor_name in self.motors:
            self._motor_off(motor_name)
        
        self.active_alerts.clear()
    
    def _sensor_to_motor(self, sensor_name):
        """Map sensor name to corresponding motor"""
        mapping = {
            'front_high': 'front_upper',
            'front_center': 'front_center',
            'front_low': 'front_lower',
            'left_side': 'left',
            'right_side': 'right',
            'ground_sensor': 'front_lower'  # Ground hazards use lower motor
        }
        return mapping.get(sensor_name, 'front_center')
    
    def _vibrate_pattern(self, motor_name, intensity, pattern, control):
        """
        Execute vibration pattern in separate thread
        
        Args:
            motor_name (str): Name of motor to vibrate
            intensity (str): Vibration strength
            pattern (str): Vibration pattern type
            control (dict): Control dictionary with 'stop' flag
        """
        # Define patterns (on_time, off_time in seconds)
        patterns = {
            'rapid': (0.1, 0.1),          # Fast pulsing - danger
            'pulse': (0.3, 0.3),          # Medium pulsing - warning
            'intermittent': (0.2, 0.8)    # Slow pulsing - alert
        }
        
        # Define intensity (duty cycle if using PWM, or just on/off)
        intensities = {
            'low': 0.3,
            'medium': 0.6,
            'high': 1.0
        }
        
        on_time, off_time = patterns.get(pattern, (0.3, 0.3))
        strength = intensities.get(intensity, 0.6)
        
        # Continue pattern until stopped
        while not control['stop']:
            self._motor_on(motor_name, strength)
            time.sleep(on_time)
            
            if control['stop']:
                break
                
            self._motor_off(motor_name)
            time.sleep(off_time)
        
        # Ensure motor is off when done
        self._motor_off(motor_name)
    
    def _motor_on(self, motor_name, strength=1.0):
        """Turn motor on with specified strength"""
        if motor_name not in self.motors:
            return
        
        pin = self.motors[motor_name]
        
        if RASPBERRY_PI:
            # For full implementation, use PWM for variable strength
            # For now, simple on/off
            GPIO.output(pin, True)
        else:
            if not self.motor_states.get(motor_name, False):
                print(f"[HAPTIC] {motor_name:15} ████ ON  (strength: {strength:.1f})")
        
        self.motor_states[motor_name] = True
    
    def _motor_off(self, motor_name):
        """Turn motor off"""
        if motor_name not in self.motors:
            return
        
        pin = self.motors[motor_name]
        
        if RASPBERRY_PI:
            GPIO.output(pin, False)
        else:
            if self.motor_states.get(motor_name, False):
                print(f"[HAPTIC] {motor_name:15} ──── OFF")
        
        self.motor_states[motor_name] = False