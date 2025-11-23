"""
Configuration for RFID Meshtastic Integration System

This file contains all tunable parameters for the system.
Modify these values to adjust timing, thresholds, and behavior.
"""

import os

# ============================================================================
# TIMING PARAMETERS
# ============================================================================

# Wait time before sending RFID read to ensure paddler has departed (seconds)
DEPARTURE_WAIT_TIME = 300  # 5 minutes default (300 seconds)

# Redis queue processing rate limiting
TRANSMISSION_DELAY_NORMAL = 3.0      # Normal spacing between messages (seconds)
TRANSMISSION_DELAY_MEDIUM = 2.5      # Medium queue depth spacing (seconds)
TRANSMISSION_DELAY_FAST = 2.0        # High queue depth spacing (seconds)

# Queue depth thresholds for adaptive delay
QUEUE_DEPTH_HIGH = 50      # Switch to fast mode
QUEUE_DEPTH_MEDIUM = 20    # Switch to medium mode

# Retry configuration for failed transmissions
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5

# Queue monitoring interval (seconds)
QUEUE_MONITOR_INTERVAL = 10

# ============================================================================
# REDIS CONFIGURATION
# ============================================================================

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Redis queue names
REDIS_QUEUE_START = 'rfid:queue:start'
REDIS_QUEUE_FINISH = 'rfid:queue:finish'
REDIS_QUEUE_FAILED = 'rfid:queue:failed'

# Queue size thresholds for alerts
QUEUE_ALERT_WARNING = 50   # Warning threshold
QUEUE_ALERT_CRITICAL = 100  # Critical threshold

# ============================================================================
# MESHTASTIC CONFIGURATION
# ============================================================================

# Meshtastic device connection
# Options: 'serial', 'tcp', 'ble'
MESHTASTIC_CONNECTION_TYPE = os.getenv('MESHTASTIC_CONNECTION', 'serial')

# Serial port for Meshtastic device
MESHTASTIC_SERIAL_PORT = os.getenv('MESHTASTIC_PORT', '/dev/ttyUSB2')

# TCP connection (if using network interface)
MESHTASTIC_TCP_HOST = os.getenv('MESHTASTIC_TCP_HOST', 'localhost')
MESHTASTIC_TCP_PORT = int(os.getenv('MESHTASTIC_TCP_PORT', 4403))

# Meshtastic message channel (default is 0 for primary channel)
MESHTASTIC_CHANNEL = int(os.getenv('MESHTASTIC_CHANNEL', 0))

# Message acknowledgment timeout (seconds)
MESHTASTIC_ACK_TIMEOUT = 30

# ============================================================================
# STATION CONFIGURATION
# ============================================================================

# Station type: 'START' or 'FINISH'
STATION_TYPE = os.getenv('STATION_TYPE', 'START')

# Station identifier for messages
STATION_ID = os.getenv('STATION_ID', 'START_LINE_1')

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# PostgreSQL connection parameters
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'rfid_system')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

# Database query timeout (seconds)
DB_QUERY_TIMEOUT = 5

# ============================================================================
# RFID READER CONFIGURATION
# ============================================================================

# RFID dwell time (seconds) - prevent duplicate reads
RFID_DWELL_TIME = 2

# Directory to monitor for RFID reads (if using file-based integration)
RFID_OUTPUT_DIR = '/var/www/html/timer/uploads/'
RFID_OUTPUT_FILE = 'rfid_output.json'

# Polling interval for file-based monitoring (seconds)
FILE_MONITOR_INTERVAL = 0.5

# ============================================================================
# SAFETY DASHBOARD THRESHOLDS
# ============================================================================

# Time thresholds for safety alerts (seconds)
ALERT_YELLOW_THRESHOLD = 14400   # 4 hours
ALERT_RED_THRESHOLD = 21600      # 6 hours
ALERT_CRITICAL_THRESHOLD = 28800  # 8 hours

# ============================================================================
# MESSAGE PRIORITIES
# ============================================================================

MESSAGE_PRIORITY_NORMAL = 'normal'
MESSAGE_PRIORITY_HIGH = 'high'
MESSAGE_PRIORITY_CRITICAL = 'critical'

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', '/var/log/meshtastic_rfid.log')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# Enable console logging
LOG_TO_CONSOLE = True

# ============================================================================
# PERFORMANCE TUNING
# ============================================================================

# Maximum number of messages to process per batch
BATCH_SIZE = 10

# Worker thread count for processing
WORKER_THREADS = 2

# Maximum queue size before blocking new entries
MAX_QUEUE_SIZE = 1000

# Message expiration time in queue (seconds)
# Messages older than this are moved to failed queue
MESSAGE_EXPIRATION_TIME = 3600  # 1 hour

# ============================================================================
# DEVELOPMENT/DEBUG OPTIONS
# ============================================================================

# Enable debug mode (more verbose logging, validation checks)
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'

# Enable message simulation (for testing without hardware)
SIMULATE_MESSAGES = os.getenv('SIMULATE_MESSAGES', 'False').lower() == 'true'

# Dry run mode (don't actually transmit messages)
DRY_RUN = os.getenv('DRY_RUN', 'False').lower() == 'true'

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_transmission_delay(queue_depth):
    """
    Calculate transmission delay based on current queue depth.

    Args:
        queue_depth: Current number of messages in queue

    Returns:
        Delay in seconds between transmissions
    """
    if queue_depth > QUEUE_DEPTH_HIGH:
        return TRANSMISSION_DELAY_FAST
    elif queue_depth > QUEUE_DEPTH_MEDIUM:
        return TRANSMISSION_DELAY_MEDIUM
    else:
        return TRANSMISSION_DELAY_NORMAL


def get_alert_level(time_on_water):
    """
    Determine alert level based on time on water.

    Args:
        time_on_water: Time in seconds since departure

    Returns:
        Alert level string: 'normal', 'yellow', 'red', or 'critical'
    """
    if time_on_water >= ALERT_CRITICAL_THRESHOLD:
        return 'critical'
    elif time_on_water >= ALERT_RED_THRESHOLD:
        return 'red'
    elif time_on_water >= ALERT_YELLOW_THRESHOLD:
        return 'yellow'
    else:
        return 'normal'


def validate_config():
    """
    Validate configuration parameters.
    Raises ValueError if configuration is invalid.
    """
    if DEPARTURE_WAIT_TIME < 0:
        raise ValueError("DEPARTURE_WAIT_TIME must be positive")

    if TRANSMISSION_DELAY_FAST >= TRANSMISSION_DELAY_MEDIUM >= TRANSMISSION_DELAY_NORMAL:
        raise ValueError("Transmission delays must be: FAST < MEDIUM < NORMAL")

    if QUEUE_DEPTH_MEDIUM >= QUEUE_DEPTH_HIGH:
        raise ValueError("Queue depth thresholds must be: MEDIUM < HIGH")

    if STATION_TYPE not in ['START', 'FINISH']:
        raise ValueError("STATION_TYPE must be 'START' or 'FINISH'")

    if MESHTASTIC_CONNECTION_TYPE not in ['serial', 'tcp', 'ble']:
        raise ValueError("MESHTASTIC_CONNECTION_TYPE must be 'serial', 'tcp', or 'ble'")

    return True


# Validate configuration on import
if not DEBUG_MODE:
    validate_config()
