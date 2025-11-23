"""
Meshtastic Interface for RFID Message Transmission

Handles communication with Meshtastic devices for sending/receiving RFID data.
"""

import json
import logging
import time
from typing import Dict, Optional, Callable
from datetime import datetime

try:
    import meshtastic
    import meshtastic.serial_interface
    import meshtastic.tcp_interface
    MESHTASTIC_AVAILABLE = True
except ImportError:
    MESHTASTIC_AVAILABLE = False
    logging.warning("Meshtastic library not available. Running in simulation mode.")

from config import (
    MESHTASTIC_CONNECTION_TYPE,
    MESHTASTIC_SERIAL_PORT,
    MESHTASTIC_TCP_HOST,
    MESHTASTIC_TCP_PORT,
    MESHTASTIC_CHANNEL,
    MESHTASTIC_ACK_TIMEOUT,
    STATION_ID,
    DRY_RUN,
    SIMULATE_MESSAGES
)

logger = logging.getLogger(__name__)


class MeshtasticInterface:
    """
    Interface for communicating with Meshtastic LoRa devices.
    """

    def __init__(self, on_receive_callback: Optional[Callable] = None):
        """
        Initialize Meshtastic interface.

        Args:
            on_receive_callback: Function to call when message is received
        """
        self.interface = None
        self.on_receive_callback = on_receive_callback
        self.connected = False
        self.messages_sent = 0
        self.messages_received = 0
        self.last_message_time = None

        if not SIMULATE_MESSAGES:
            self.connect()

    def connect(self):
        """Establish connection to Meshtastic device."""
        if not MESHTASTIC_AVAILABLE:
            logger.warning("Meshtastic library not installed. Running in simulation mode.")
            logger.warning("Install with: pip install meshtastic")
            return

        try:
            if MESHTASTIC_CONNECTION_TYPE == 'serial':
                logger.info(f"Connecting to Meshtastic via serial: {MESHTASTIC_SERIAL_PORT}")
                self.interface = meshtastic.serial_interface.SerialInterface(
                    devPath=MESHTASTIC_SERIAL_PORT
                )

            elif MESHTASTIC_CONNECTION_TYPE == 'tcp':
                logger.info(f"Connecting to Meshtastic via TCP: {MESHTASTIC_TCP_HOST}:{MESHTASTIC_TCP_PORT}")
                self.interface = meshtastic.tcp_interface.TCPInterface(
                    hostname=MESHTASTIC_TCP_HOST,
                    portNumber=MESHTASTIC_TCP_PORT
                )

            else:
                raise ValueError(f"Unsupported connection type: {MESHTASTIC_CONNECTION_TYPE}")

            # Set up receive callback
            if self.on_receive_callback:
                self.interface.onReceive = self._on_receive_wrapper

            self.connected = True
            logger.info("Successfully connected to Meshtastic device")

        except Exception as e:
            logger.error(f"Failed to connect to Meshtastic: {e}")
            self.connected = False
            raise

    def _on_receive_wrapper(self, packet, interface):
        """
        Wrapper for receive callback to handle Meshtastic packets.

        Args:
            packet: Meshtastic packet
            interface: Meshtastic interface
        """
        try:
            # Extract message from packet
            if 'decoded' in packet and 'text' in packet['decoded']:
                text = packet['decoded']['text']

                # Try to parse as JSON
                try:
                    message = json.loads(text)

                    # Add receive metadata
                    message['received_at'] = datetime.utcnow().isoformat()
                    message['rssi'] = packet.get('rxRssi', None)
                    message['snr'] = packet.get('rxSnr', None)
                    message['from_node'] = packet.get('fromId', None)

                    self.messages_received += 1
                    self.last_message_time = time.time()

                    logger.info(f"Received message from {message.get('from_node')}: "
                              f"RFID {message.get('rfid')}")

                    # Call user callback
                    if self.on_receive_callback:
                        self.on_receive_callback(message)

                except json.JSONDecodeError:
                    logger.debug(f"Received non-JSON text message: {text}")

        except Exception as e:
            logger.error(f"Error processing received message: {e}")

    def send_message(self, message: Dict, retries: int = 3) -> bool:
        """
        Send a message via Meshtastic.

        Args:
            message: Dictionary containing message data
            retries: Number of retry attempts

        Returns:
            True if successful, False otherwise
        """
        if DRY_RUN:
            logger.info(f"[DRY RUN] Would send message: {message.get('rfid')}")
            return True

        if SIMULATE_MESSAGES or not MESHTASTIC_AVAILABLE:
            logger.info(f"[SIMULATION] Sending message: {message.get('rfid')}")
            self.messages_sent += 1
            time.sleep(0.1)  # Simulate transmission time
            return True

        if not self.connected:
            logger.error("Cannot send message: Not connected to Meshtastic")
            return False

        # Add transmission metadata
        message['sent_at'] = datetime.utcnow().isoformat()
        message['sent_by'] = STATION_ID

        # Convert message to JSON
        try:
            message_json = json.dumps(message)

            # Check message size (Meshtastic has size limits)
            if len(message_json) > 200:  # Conservative limit
                logger.error(f"Message too large: {len(message_json)} bytes")
                return False

            # Attempt to send with retries
            for attempt in range(retries):
                try:
                    self.interface.sendText(
                        text=message_json,
                        channelIndex=MESHTASTIC_CHANNEL
                    )

                    self.messages_sent += 1
                    self.last_message_time = time.time()

                    logger.info(f"Sent message (attempt {attempt + 1}/{retries}): "
                              f"RFID {message.get('rfid')}")
                    return True

                except Exception as e:
                    logger.warning(f"Send attempt {attempt + 1} failed: {e}")
                    if attempt < retries - 1:
                        time.sleep(1)  # Wait before retry
                    else:
                        logger.error(f"Failed to send message after {retries} attempts")
                        return False

        except Exception as e:
            logger.error(f"Error preparing message for transmission: {e}")
            return False

    def send_rfid_start(self, rfid: str, timestamp: float, tag_data: Dict = None) -> bool:
        """
        Send a START message for an RFID.

        Args:
            rfid: RFID tag ID
            timestamp: Unix timestamp of detection
            tag_data: Optional additional tag data

        Returns:
            True if successful, False otherwise
        """
        message = {
            'rfid': rfid,
            'timestamp': timestamp,
            'timestamp_h': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'message_type': 'START',
            'station_id': STATION_ID,
            'priority': 'normal'
        }

        # Add optional tag data
        if tag_data:
            message.update({
                'tag_type': tag_data.get('tag_type'),
                'tag_position': tag_data.get('tag_position')
            })

        return self.send_message(message)

    def send_rfid_finish(self, rfid: str, timestamp: float, tag_data: Dict = None) -> bool:
        """
        Send a FINISH message for an RFID.

        Args:
            rfid: RFID tag ID
            timestamp: Unix timestamp of detection
            tag_data: Optional additional tag data

        Returns:
            True if successful, False otherwise
        """
        message = {
            'rfid': rfid,
            'timestamp': timestamp,
            'timestamp_h': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'message_type': 'FINISH',
            'station_id': STATION_ID,
            'priority': 'normal'
        }

        # Add optional tag data
        if tag_data:
            message.update({
                'tag_type': tag_data.get('tag_type'),
                'tag_position': tag_data.get('tag_position')
            })

        return self.send_message(message)

    def get_node_info(self) -> Optional[Dict]:
        """
        Get information about the connected Meshtastic node.

        Returns:
            Dictionary with node info or None if not available
        """
        if not self.connected or not self.interface:
            return None

        try:
            node_info = {
                'connected': self.connected,
                'messages_sent': self.messages_sent,
                'messages_received': self.messages_received,
                'last_message_time': self.last_message_time
            }

            # Try to get additional node details
            if hasattr(self.interface, 'myInfo'):
                my_info = self.interface.myInfo
                if my_info:
                    node_info.update({
                        'node_id': my_info.get('user', {}).get('id'),
                        'long_name': my_info.get('user', {}).get('longName'),
                        'short_name': my_info.get('user', {}).get('shortName'),
                    })

            return node_info

        except Exception as e:
            logger.error(f"Error getting node info: {e}")
            return None

    def close(self):
        """Close the Meshtastic connection."""
        if self.interface:
            try:
                self.interface.close()
                logger.info("Closed Meshtastic connection")
            except Exception as e:
                logger.error(f"Error closing Meshtastic connection: {e}")
        self.connected = False

    def is_healthy(self) -> bool:
        """
        Check if the Meshtastic connection is healthy.

        Returns:
            True if healthy, False otherwise
        """
        if SIMULATE_MESSAGES:
            return True

        if not self.connected:
            return False

        try:
            # Check if interface is still responsive
            # This is a simple check - in production you might want more sophisticated health checks
            return self.interface is not None
        except:
            return False


def create_message(
    rfid: str,
    timestamp: float,
    message_type: str,
    station_id: str = STATION_ID,
    priority: str = 'normal',
    **kwargs
) -> Dict:
    """
    Factory function to create a standardized message.

    Args:
        rfid: RFID tag ID
        timestamp: Unix timestamp
        message_type: Type of message ('START', 'FINISH', etc.)
        station_id: Station identifier
        priority: Message priority
        **kwargs: Additional fields to include

    Returns:
        Message dictionary
    """
    message = {
        'rfid': rfid,
        'timestamp': timestamp,
        'timestamp_h': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
        'message_type': message_type,
        'station_id': station_id,
        'priority': priority
    }

    # Add any additional fields
    message.update(kwargs)

    return message
