"""
Start Line Sender - RFID to Meshtastic Bridge

Monitors RFID reads, implements 5-minute wait logic, and queues messages for transmission.
"""

import json
import time
import logging
import threading
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, Set
from pathlib import Path

from config import (
    DEPARTURE_WAIT_TIME,
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
    RFID_OUTPUT_DIR, RFID_OUTPUT_FILE,
    FILE_MONITOR_INTERVAL,
    STATION_ID
)
from redis_queue import RedisQueue, RateLimitedQueueProcessor
from meshtastic_interface import MeshtasticInterface

logger = logging.getLogger(__name__)


class DepartureTracker:
    """
    Tracks RFID reads and implements 5-minute wait logic.

    The 5-minute wait ensures that paddlers have actually departed
    the start area before their time is transmitted.
    """

    def __init__(self, wait_time: int = DEPARTURE_WAIT_TIME):
        """
        Initialize departure tracker.

        Args:
            wait_time: Seconds to wait before confirming departure
        """
        self.wait_time = wait_time
        self.pending_departures = {}  # rfid -> {'first_seen': timestamp, 'last_seen': timestamp, 'data': dict}
        self.confirmed_departures = set()  # RFIDs that have been confirmed as departed
        self.lock = threading.Lock()

    def record_rfid_read(self, rfid: str, timestamp: float, tag_data: Dict = None):
        """
        Record an RFID read.

        Args:
            rfid: RFID tag ID
            timestamp: Unix timestamp of read
            tag_data: Optional additional tag data
        """
        with self.lock:
            if rfid in self.confirmed_departures:
                # Already confirmed, ignore subsequent reads
                logger.debug(f"RFID {rfid} already confirmed departed, ignoring")
                return

            if rfid in self.pending_departures:
                # Update last seen time
                self.pending_departures[rfid]['last_seen'] = timestamp
                logger.debug(f"Updated last seen for RFID {rfid}")
            else:
                # New RFID read
                self.pending_departures[rfid] = {
                    'first_seen': timestamp,
                    'last_seen': timestamp,
                    'data': tag_data or {}
                }
                logger.info(f"New RFID detected: {rfid} at {datetime.fromtimestamp(timestamp)}")

    def get_confirmed_departures(self) -> list:
        """
        Get RFIDs that have completed the wait period without being re-read.

        Returns:
            List of dictionaries with RFID and departure data
        """
        confirmed = []
        current_time = time.time()

        with self.lock:
            rfids_to_remove = []

            for rfid, data in self.pending_departures.items():
                time_since_last_seen = current_time - data['last_seen']

                # If wait time has elapsed since last seen, confirm departure
                if time_since_last_seen >= self.wait_time:
                    confirmed.append({
                        'rfid': rfid,
                        'timestamp': data['first_seen'],  # Use first seen as official start time
                        'last_seen': data['last_seen'],
                        'data': data['data']
                    })
                    rfids_to_remove.append(rfid)
                    self.confirmed_departures.add(rfid)

                    wait_minutes = self.wait_time / 60
                    logger.info(f"Confirmed departure for RFID {rfid} after {wait_minutes:.1f} minute wait")

            # Remove confirmed RFIDs from pending
            for rfid in rfids_to_remove:
                del self.pending_departures[rfid]

        return confirmed

    def get_pending_count(self) -> int:
        """Get count of RFIDs pending confirmation."""
        with self.lock:
            return len(self.pending_departures)

    def get_confirmed_count(self) -> int:
        """Get count of confirmed departures."""
        with self.lock:
            return len(self.confirmed_departures)

    def reset(self):
        """Reset the tracker (for testing or new event)."""
        with self.lock:
            self.pending_departures.clear()
            self.confirmed_departures.clear()
            logger.info("Departure tracker reset")


class StartLineSender:
    """
    Main class for start line operations.
    Monitors RFID reads, tracks departures, and queues messages.
    """

    def __init__(self):
        """Initialize the start line sender."""
        self.departure_tracker = DepartureTracker()
        self.redis_queue = RedisQueue()
        self.meshtastic = MeshtasticInterface()
        self.running = False

        # Database connection
        self.db_conn = None
        self.connect_database()

        # Statistics
        self.rfids_read = 0
        self.messages_queued = 0

        # Last processed JSON offset (for file monitoring)
        self.last_json_index = 0

    def connect_database(self):
        """Connect to PostgreSQL database."""
        try:
            self.db_conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self.db_conn = None

    def save_to_database(self, tag_data: Dict):
        """
        Save RFID read to timeresults table.

        Args:
            tag_data: Dictionary with tag_type, tag_id, tag_position, timestamp
        """
        if not self.db_conn:
            logger.warning("No database connection, skipping save")
            return

        try:
            cursor = self.db_conn.cursor()
            cursor.execute(
                """
                INSERT INTO timeresults (tag_type, tag_id, tag_position, timestamp, timestamp_h)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    tag_data.get('tag_type'),
                    tag_data.get('tag_id'),
                    tag_data.get('tag_position'),
                    tag_data.get('timestamp'),
                    tag_data.get('timestamp_h')
                )
            )
            self.db_conn.commit()
            logger.debug(f"Saved RFID {tag_data.get('tag_id')} to database")
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            self.db_conn.rollback()

    def monitor_json_file(self):
        """
        Monitor the JSON output file from RFID reader.
        This integrates with the existing stamper.py system.
        """
        json_file = Path(RFID_OUTPUT_DIR) / RFID_OUTPUT_FILE

        if not json_file.exists():
            logger.warning(f"JSON file not found: {json_file}")
            return

        try:
            with open(json_file, 'r') as f:
                data = json.load(f)

            # Process new entries since last check
            new_entries = data[self.last_json_index:]

            for entry in new_entries:
                self.process_rfid_read(entry)

            self.last_json_index = len(data)

        except Exception as e:
            logger.error(f"Error reading JSON file: {e}")

    def process_rfid_read(self, tag_data: Dict):
        """
        Process a single RFID read.

        Args:
            tag_data: Dictionary with tag data
        """
        rfid = tag_data.get('tag_id')
        timestamp = tag_data.get('timestamp')

        if not rfid or not timestamp:
            logger.warning(f"Invalid tag data: {tag_data}")
            return

        # Save to database (local record)
        self.save_to_database(tag_data)

        # Record for departure tracking
        self.departure_tracker.record_rfid_read(rfid, timestamp, tag_data)

        self.rfids_read += 1

    def check_confirmed_departures(self):
        """
        Check for confirmed departures and queue them for transmission.
        """
        confirmed = self.departure_tracker.get_confirmed_departures()

        for departure in confirmed:
            message = {
                'rfid': departure['rfid'],
                'timestamp': departure['timestamp'],
                'last_seen': departure['last_seen'],
                'timestamp_h': datetime.fromtimestamp(departure['timestamp']).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'message_type': 'START',
                'station_id': STATION_ID,
                'priority': 'normal'
            }

            # Add tag data if available
            if departure['data']:
                message.update({
                    'tag_type': departure['data'].get('tag_type'),
                    'tag_position': departure['data'].get('tag_position')
                })

            # Queue for transmission
            if self.redis_queue.enqueue(message):
                self.messages_queued += 1
                logger.info(f"Queued departure for RFID {departure['rfid']}")
            else:
                logger.error(f"Failed to queue departure for RFID {departure['rfid']}")

    def start_queue_processor(self):
        """Start the queue processor in a separate thread."""
        def transmit_callback(message):
            """Callback function for transmitting messages."""
            return self.meshtastic.send_message(message)

        processor = RateLimitedQueueProcessor(self.redis_queue, transmit_callback)

        processor_thread = threading.Thread(target=processor.start, daemon=True)
        processor_thread.start()

        logger.info("Started queue processor thread")

    def run(self):
        """Main run loop."""
        self.running = True
        logger.info("Starting Start Line Sender")
        logger.info(f"Departure wait time: {DEPARTURE_WAIT_TIME / 60:.1f} minutes")

        # Start queue processor
        self.start_queue_processor()

        try:
            while self.running:
                # Monitor for new RFID reads
                self.monitor_json_file()

                # Check for confirmed departures
                self.check_confirmed_departures()

                # Log statistics periodically
                if int(time.time()) % 60 == 0:  # Every minute
                    self.log_statistics()

                # Sleep before next iteration
                time.sleep(FILE_MONITOR_INTERVAL)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop()

    def stop(self):
        """Stop the sender."""
        self.running = False
        logger.info("Stopping Start Line Sender")

        # Close connections
        if self.db_conn:
            self.db_conn.close()

        if self.meshtastic:
            self.meshtastic.close()

        # Final statistics
        self.log_statistics()

    def log_statistics(self):
        """Log current statistics."""
        queue_stats = self.redis_queue.get_stats()
        node_info = self.meshtastic.get_node_info()

        logger.info("=" * 60)
        logger.info("START LINE SENDER STATISTICS")
        logger.info(f"RFIDs Read:           {self.rfids_read}")
        logger.info(f"Pending Departures:   {self.departure_tracker.get_pending_count()}")
        logger.info(f"Confirmed Departures: {self.departure_tracker.get_confirmed_count()}")
        logger.info(f"Messages Queued:      {self.messages_queued}")
        logger.info(f"Queue Depth:          {queue_stats.get('depth', 0)}")
        logger.info(f"Queue Alert Level:    {queue_stats.get('alert_level', 'unknown')}")
        if node_info:
            logger.info(f"Mesh Messages Sent:   {node_info.get('messages_sent', 0)}")
        logger.info("=" * 60)


def main():
    """Main entry point."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create and run sender
    sender = StartLineSender()
    sender.run()


if __name__ == '__main__':
    main()
