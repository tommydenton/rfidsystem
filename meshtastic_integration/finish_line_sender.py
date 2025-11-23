"""
Finish Line Sender - RFID to Meshtastic Bridge

Monitors RFID reads at finish line and sends FINISH messages back to start line.
"""

import json
import time
import logging
import threading
import psycopg2
from datetime import datetime
from typing import Dict, Set
from pathlib import Path

from config import (
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
    RFID_OUTPUT_DIR, RFID_OUTPUT_FILE,
    FILE_MONITOR_INTERVAL,
    STATION_ID,
    RFID_DWELL_TIME
)
from redis_queue import RedisQueue, RateLimitedQueueProcessor
from meshtastic_interface import MeshtasticInterface

logger = logging.getLogger(__name__)


class FinishTracker:
    """
    Tracks RFID finish reads and prevents duplicate transmissions.
    Uses dwell time to avoid sending multiple messages for the same RFID.
    """

    def __init__(self, dwell_time: int = RFID_DWELL_TIME):
        """
        Initialize finish tracker.

        Args:
            dwell_time: Seconds between duplicate reads
        """
        self.dwell_time = dwell_time
        self.processed_rfids = {}  # rfid -> last_transmitted_timestamp
        self.lock = threading.Lock()

    def should_transmit(self, rfid: str, timestamp: float) -> bool:
        """
        Check if an RFID finish should be transmitted.

        Args:
            rfid: RFID tag ID
            timestamp: Current timestamp

        Returns:
            True if should transmit, False if too recent
        """
        with self.lock:
            if rfid in self.processed_rfids:
                last_transmitted = self.processed_rfids[rfid]
                time_diff = timestamp - last_transmitted

                if time_diff < self.dwell_time:
                    logger.debug(f"RFID {rfid} seen again within dwell time, skipping")
                    return False

            # Update last transmitted time
            self.processed_rfids[rfid] = timestamp
            return True

    def get_processed_count(self) -> int:
        """Get count of processed RFIDs."""
        with self.lock:
            return len(self.processed_rfids)


class FinishLineSender:
    """
    Main class for finish line operations.
    Monitors RFID reads and sends FINISH messages via Meshtastic.
    """

    def __init__(self):
        """Initialize the finish line sender."""
        self.finish_tracker = FinishTracker()
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
        Process a single RFID read (FINISH).

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

        self.rfids_read += 1

        # Check if should transmit (dwell time check)
        if not self.finish_tracker.should_transmit(rfid, timestamp):
            return

        # Queue FINISH message for transmission
        self.queue_finish_message(rfid, timestamp, tag_data)

    def queue_finish_message(self, rfid: str, timestamp: float, tag_data: Dict = None):
        """
        Queue a FINISH message for transmission.

        Args:
            rfid: RFID tag ID
            timestamp: Finish timestamp
            tag_data: Optional tag data
        """
        message = {
            'rfid': rfid,
            'timestamp': timestamp,
            'timestamp_h': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'message_type': 'FINISH',
            'station_id': STATION_ID,
            'priority': 'normal'
        }

        # Add tag data if available
        if tag_data:
            message.update({
                'tag_type': tag_data.get('tag_type'),
                'tag_position': tag_data.get('tag_position')
            })

        # Queue for transmission
        if self.redis_queue.enqueue(message):
            self.messages_queued += 1
            logger.info(f"Queued FINISH for RFID {rfid}")
        else:
            logger.error(f"Failed to queue FINISH for RFID {rfid}")

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
        logger.info("Starting Finish Line Sender")
        logger.info(f"Sending FINISH messages back to start line")

        # Start queue processor
        self.start_queue_processor()

        try:
            while self.running:
                # Monitor for new RFID reads
                self.monitor_json_file()

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
        logger.info("Stopping Finish Line Sender")

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
        logger.info("FINISH LINE SENDER STATISTICS")
        logger.info(f"RFIDs Read (Finishes): {self.rfids_read}")
        logger.info(f"Messages Queued:       {self.messages_queued}")
        logger.info(f"Queue Depth:           {queue_stats.get('depth', 0)}")
        logger.info(f"Queue Alert Level:     {queue_stats.get('alert_level', 'unknown')}")
        if node_info:
            logger.info(f"Mesh Messages Sent:    {node_info.get('messages_sent', 0)}")
        logger.info("=" * 60)


def main():
    """Main entry point."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create and run sender
    sender = FinishLineSender()
    sender.run()


if __name__ == '__main__':
    main()
