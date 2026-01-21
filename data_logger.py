"""
Data Logger
Logs sensor data and events for analysis
"""

import os
import json
import time
from datetime import datetime

class DataLogger:
    """Logger for sensor data and system events"""
    
    def __init__(self, config):
        """Initialize data logger"""
        self.config = config
        self.log_dir = config.LOG_DIRECTORY
        
        # Create log directory if it doesn't exist
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            print(f"✓ Created log directory: {self.log_dir}")
        
        # Create session log files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_file = os.path.join(self.log_dir, f"session_{timestamp}.jsonl")
        self.event_file = os.path.join(self.log_dir, f"events_{timestamp}.jsonl")
        
        # Statistics
        self.stats = {
            'session_start': time.time(),
            'total_readings': 0,
            'danger_events': 0,
            'warning_events': 0,
            'alert_events': 0,
            'ground_hazards': 0
        }
        
        print(f"✓ Logging to: {self.session_file}")
    
    def log_sensor_data(self, sensor_data):
        """
        Log sensor readings
        
        Args:
            sensor_data (dict): Dictionary of sensor name -> distance readings
        """
        if not self.config.LOG_SENSOR_DATA:
            return
        
        log_entry = {
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'type': 'sensor_data',
            'data': sensor_data
        }
        
        self._write_log(self.session_file, log_entry)
        self.stats['total_readings'] += 1
    
    def log_event(self, event_type, sensor_name, distance_or_hazard):
        """
        Log detection event
        
        Args:
            event_type (str): 'danger', 'warning', 'alert', or 'ground_*'
            sensor_name (str): Name of sensor that detected obstacle
            distance_or_hazard: Distance (float) or hazard dict
        """
        if not self.config.LOG_EVENTS:
            return
        
        log_entry = {
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'type': 'event',
            'event_type': event_type,
            'sensor': sensor_name,
        }
        
        # Handle different data types
        if isinstance(distance_or_hazard, dict):
            log_entry['hazard_info'] = distance_or_hazard
        else:
            log_entry['distance'] = distance_or_hazard
        
        self._write_log(self.event_file, log_entry)
        
        # Update statistics
        if 'danger' in event_type:
            self.stats['danger_events'] += 1
        elif 'warning' in event_type:
            self.stats['warning_events'] += 1
        elif 'alert' in event_type:
            self.stats['alert_events'] += 1
        
        if 'ground' in event_type:
            self.stats['ground_hazards'] += 1
    
    def _write_log(self, filename, data):
        """
        Write log entry to file
        
        Args:
            filename (str): Log file path
            data (dict): Data to log
        """
        try:
            with open(filename, 'a') as f:
                f.write(json.dumps(data) + '\n')
        except Exception as e:
            print(f"Error writing log: {e}")
    
    def get_session_summary(self):
        """
        Generate summary of current session
        
        Returns:
            dict: Session statistics
        """
        runtime = time.time() - self.stats['session_start']
        
        return {
            'runtime_seconds': runtime,
            'runtime_minutes': runtime / 60,
            'total_readings': self.stats['total_readings'],
            'danger_events': self.stats['danger_events'],
            'warning_events': self.stats['warning_events'],
            'alert_events': self.stats['alert_events'],
            'ground_hazards': self.stats['ground_hazards'],
            'readings_per_second': self.stats['total_readings'] / runtime if runtime > 0 else 0
        }
    
    def export_summary(self, filename=None):
        """
        Export session summary to JSON file
        
        Args:
            filename (str): Output filename (optional)
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.log_dir, f"summary_{timestamp}.json")
        
        summary = self.get_session_summary()
        
        try:
            with open(filename, 'w') as f:
                json.dump(summary, f, indent=2)
            print(f"✓ Summary exported to: {filename}")
        except Exception as e:
            print(f"Error exporting summary: {e}")