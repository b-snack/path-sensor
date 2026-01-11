"""
Configuration
All system settings and constants
"""

class Config:
    """Configuration settings for PathSense system"""
    
    # ========== DETECTION ZONES (in meters) ==========
    DANGER_ZONE = 0.5   # Critical alert - immediate danger
    WARNING_ZONE = 1.5  # Warning alert - prepare to stop/turn
    ALERT_ZONE = 3.0    # Information alert - obstacle detected
    
    # ========== SCAN SETTINGS ==========
    SCAN_INTERVAL = 0.1  # 10 Hz update rate (seconds between sensor reads)
    
    # ========== SENSOR GPIO PIN MAPPINGS (BCM numbering) ==========
    SENSORS = {
        'front_high': {'trigger': 17, 'echo': 27},      # Overhead obstacles
        'front_center': {'trigger': 22, 'echo': 23},    # Chest height
        'front_low': {'trigger': 24, 'echo': 25},       # Knee height
        'left_side': {'trigger': 5, 'echo': 6},         # Left peripheral
        'right_side': {'trigger': 13, 'echo': 19}       # Right peripheral
    }
    
    # Ground sensor (downward-facing for potholes/curbs/stairs)
    GROUND_SENSOR = {'trigger': 10, 'echo': 9}
    
    # ========== HAPTIC MOTOR GPIO PINS (BCM numbering) ==========
    HAPTIC_MOTORS = {
        'front_upper': 12,    # Upper chest motor (overhead obstacles)
        'front_center': 16,   # Center chest motor (chest-height obstacles)
        'front_lower': 20,    # Lower chest motor (knee/ground obstacles)
        'left': 21,           # Left shoulder motor (left-side obstacles)
        'right': 26           # Right shoulder motor (right-side obstacles)
    }
    
    # ========== DATA LOGGING SETTINGS ==========
    LOG_ENABLED = True
    LOG_DIRECTORY = './logs'
    LOG_SENSOR_DATA = True
    LOG_EVENTS = True
    
    # ========== SENSOR LIMITS ==========
    MAX_SENSOR_DISTANCE = 4.0  # Maximum reliable sensor range (meters)
    MIN_SENSOR_DISTANCE = 0.02  # Minimum sensor range (meters)
    
    # ========== WINTER OPTIMIZATION SETTINGS ==========
    COLD_TEMP_COMPENSATION = True  # Adjust for temperature effects on ultrasonic
    SNOW_FILTER_ENABLED = True     # Filter out snow particles vs solid obstacles
    DEFAULT_TEMPERATURE = 0.0      # Default temperature (Celsius) for winter mode
    
    # ========== GROUND DETECTION SETTINGS ==========
    GROUND_CALIBRATION_SAMPLES = 50     # Number of samples for ground calibration
    POTHOLE_THRESHOLD = 0.15            # Minimum depth to classify as pothole (meters)
    CURB_THRESHOLD = 0.10               # Minimum height to classify as curb (meters)
    MAJOR_DROP_THRESHOLD = 0.30         # Threshold for critical drop-off alert (meters)
    
    # ========== SYSTEM INFORMATION ==========
    VERSION = "1.0.0"
    SYSTEM_NAME = "PathSense"
    DESCRIPTION = "Wearable 3D Obstacle Detection for Blind Navigation"