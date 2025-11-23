"""
RFID Meshtastic Integration Package

This package provides integration between RFID timing systems and
Meshtastic LoRa mesh networks for river race safety and timing.
"""

__version__ = '1.0.0'
__author__ = 'RFID Timing System'

from .config import (
    DEPARTURE_WAIT_TIME,
    TRANSMISSION_DELAY_NORMAL,
    STATION_TYPE,
    STATION_ID
)

from .redis_queue import RedisQueue, RateLimitedQueueProcessor
from .meshtastic_interface import MeshtasticInterface, create_message
from .start_line_sender import StartLineSender, DepartureTracker
from .finish_line_receiver import FinishLineReceiver, OnWaterTracker
from .queue_monitor import QueueMonitor, SystemMonitor

__all__ = [
    'RedisQueue',
    'RateLimitedQueueProcessor',
    'MeshtasticInterface',
    'create_message',
    'StartLineSender',
    'DepartureTracker',
    'FinishLineReceiver',
    'OnWaterTracker',
    'QueueMonitor',
    'SystemMonitor',
]
