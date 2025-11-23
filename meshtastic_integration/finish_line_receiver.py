"""
Finish Line Receiver - Meshtastic to Database Bridge

Receives RFID start messages via Meshtastic and updates the database
to track which RFIDs are currently on the water.
"""

import json
import time
import logging
import threading
import psycopg2
from datetime import datetime
from typing import Dict, Optional

from config import (
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
    STATION_ID,
    get_alert_level
)
from meshtastic_interface import MeshtasticInterface

logger = logging.getLogger(__name__)


class OnWaterTracker:
    """
    Tracks RFIDs that are currently on the water.
    Combines START messages from Meshtastic with local FINISH reads.
    """

    def __init__(self):
        """Initialize the tracker."""
        self.on_water = {}  # rfid -> start_data
        self.lock = threading.Lock()

        # Statistics
        self.total_started = 0
        self.total_finished = 0
        self.messages_received = 0

    def record_start(self, rfid: str, start_data: Dict):
        """
        Record an RFID start from Meshtastic message.

        Args:
            rfid: RFID tag ID
            start_data: Dictionary with start timestamp and metadata
        """
        with self.lock:
            if rfid not in self.on_water:
                self.on_water[rfid] = start_data
                self.total_started += 1
                logger.info(f"RFID {rfid} started - now on water "
                          f"({len(self.on_water)} total on water)")
            else:
                logger.warning(f"RFID {rfid} already on water, updating data")
                self.on_water[rfid].update(start_data)

    def record_finish(self, rfid: str, finish_timestamp: float):
        """
        Record an RFID finish from local reader.

        Args:
            rfid: RFID tag ID
            finish_timestamp: Unix timestamp of finish
        """
        with self.lock:
            if rfid in self.on_water:
                start_data = self.on_water[rfid]
                start_time = start_data.get('timestamp', 0)
                duration = finish_timestamp - start_time

                self.total_finished += 1
                del self.on_water[rfid]

                logger.info(f"RFID {rfid} finished - duration {duration / 3600:.2f} hours "
                          f"({len(self.on_water)} remaining on water)")

                return duration
            else:
                logger.warning(f"RFID {rfid} finished but no start record found")
                self.total_finished += 1
                return None

    def get_on_water_count(self) -> int:
        """Get count of RFIDs currently on water."""
        with self.lock:
            return len(self.on_water)

    def get_on_water_rfids(self) -> Dict:
        """
        Get all RFIDs currently on water with their data.

        Returns:
            Dictionary of rfid -> start_data
        """
        with self.lock:
            return self.on_water.copy()

    def get_alerts(self) -> list:
        """
        Get RFIDs that exceed time thresholds.

        Returns:
            List of alert dictionaries
        """
        alerts = []
        current_time = time.time()

        with self.lock:
            for rfid, start_data in self.on_water.items():
                start_time = start_data.get('timestamp', 0)
                time_on_water = current_time - start_time

                alert_level = get_alert_level(time_on_water)

                if alert_level != 'normal':
                    alerts.append({
                        'rfid': rfid,
                        'start_time': start_time,
                        'time_on_water': time_on_water,
                        'alert_level': alert_level,
                        'start_data': start_data
                    })

        # Sort by time on water (longest first)
        alerts.sort(key=lambda x: x['time_on_water'], reverse=True)

        return alerts


class FinishLineReceiver:
    """
    Main class for finish line operations.
    Receives messages via Meshtastic and tracks on-water status.
    """

    def __init__(self):
        """Initialize the finish line receiver."""
        self.tracker = OnWaterTracker()
        self.meshtastic = MeshtasticInterface(on_receive_callback=self.on_message_received)
        self.running = False

        # Database connection
        self.db_conn = None
        self.connect_database()

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

    def save_start_to_database(self, message: Dict):
        """
        Save received START message to a tracking table.

        This creates a table to store start messages received via Meshtastic.

        Args:
            message: Message dictionary from Meshtastic
        """
        if not self.db_conn:
            logger.warning("No database connection, skipping save")
            return

        try:
            cursor = self.db_conn.cursor()

            # Create table if it doesn't exist
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS meshtastic_starts (
                    id SERIAL PRIMARY KEY,
                    rfid VARCHAR(255) NOT NULL,
                    start_timestamp DOUBLE PRECISION,
                    start_timestamp_h VARCHAR(255),
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    station_id VARCHAR(255),
                    tag_type VARCHAR(255),
                    tag_position VARCHAR(255),
                    message_data JSONB
                )
                """
            )

            # Insert the start message
            cursor.execute(
                """
                INSERT INTO meshtastic_starts
                (rfid, start_timestamp, start_timestamp_h, station_id, tag_type, tag_position, message_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    message.get('rfid'),
                    message.get('timestamp'),
                    message.get('timestamp_h'),
                    message.get('station_id'),
                    message.get('tag_type'),
                    message.get('tag_position'),
                    json.dumps(message)
                )
            )

            self.db_conn.commit()
            logger.debug(f"Saved START message for RFID {message.get('rfid')} to database")

        except Exception as e:
            logger.error(f"Error saving START message to database: {e}")
            self.db_conn.rollback()

    def on_message_received(self, message: Dict):
        """
        Callback when a message is received via Meshtastic.

        Args:
            message: Message dictionary
        """
        try:
            message_type = message.get('message_type')
            rfid = message.get('rfid')

            if not rfid:
                logger.warning("Received message without RFID")
                return

            if message_type == 'START':
                # Record start
                self.tracker.record_start(rfid, message)

                # Save to database
                self.save_start_to_database(message)

                logger.info(f"Received START for RFID {rfid} from {message.get('station_id')}")

            else:
                logger.debug(f"Received message type: {message_type}")

        except Exception as e:
            logger.error(f"Error processing received message: {e}")

    def monitor_local_finishes(self):
        """
        Monitor the local timeresults table for finish reads.
        Checks for new RFID reads and marks them as finished.
        """
        if not self.db_conn:
            return

        try:
            cursor = self.db_conn.cursor()

            # Create a tracking table for last processed ID
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS finish_processing_state (
                    id INTEGER PRIMARY KEY,
                    last_processed_id INTEGER DEFAULT 0
                )
                """
            )

            # Get last processed ID
            cursor.execute("SELECT last_processed_id FROM finish_processing_state WHERE id = 1")
            result = cursor.fetchone()

            if result:
                last_id = result[0]
            else:
                # Initialize
                cursor.execute("INSERT INTO finish_processing_state (id, last_processed_id) VALUES (1, 0)")
                self.db_conn.commit()
                last_id = 0

            # Get new finish reads
            cursor.execute(
                """
                SELECT id, tag_id, timestamp
                FROM timeresults
                WHERE id > %s
                ORDER BY id
                """,
                (last_id,)
            )

            new_finishes = cursor.fetchall()

            for finish_id, rfid, timestamp in new_finishes:
                # Record finish
                self.tracker.record_finish(rfid, timestamp)

                # Update last processed ID
                cursor.execute(
                    "UPDATE finish_processing_state SET last_processed_id = %s WHERE id = 1",
                    (finish_id,)
                )
                self.db_conn.commit()

        except Exception as e:
            logger.error(f"Error monitoring local finishes: {e}")
            if self.db_conn:
                self.db_conn.rollback()

    def check_alerts(self):
        """Check for and log any alerts."""
        alerts = self.tracker.get_alerts()

        if alerts:
            logger.warning("=" * 60)
            logger.warning(f"SAFETY ALERTS: {len(alerts)} RFIDs exceed time thresholds")
            logger.warning("=" * 60)

            for alert in alerts:
                rfid = alert['rfid']
                time_on_water = alert['time_on_water']
                level = alert['alert_level']
                hours = time_on_water / 3600

                level_emoji = {
                    'yellow': '⚠',
                    'red': '🚨',
                    'critical': '🆘'
                }

                logger.warning(f"{level_emoji.get(level, '⚠')} [{level.upper()}] "
                             f"RFID {rfid} - {hours:.2f} hours on water")

    def run(self):
        """Main run loop."""
        self.running = True
        logger.info("Starting Finish Line Receiver")
        logger.info(f"Listening for messages on station: {STATION_ID}")

        try:
            while self.running:
                # Monitor for local finish reads
                self.monitor_local_finishes()

                # Check for alerts
                self.check_alerts()

                # Log statistics every minute
                if int(time.time()) % 60 == 0:
                    self.log_statistics()

                # Sleep before next iteration
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop()

    def stop(self):
        """Stop the receiver."""
        self.running = False
        logger.info("Stopping Finish Line Receiver")

        # Close connections
        if self.db_conn:
            self.db_conn.close()

        if self.meshtastic:
            self.meshtastic.close()

        # Final statistics
        self.log_statistics()

    def log_statistics(self):
        """Log current statistics."""
        node_info = self.meshtastic.get_node_info()
        on_water = self.tracker.get_on_water_count()
        alerts = self.tracker.get_alerts()

        logger.info("=" * 60)
        logger.info("FINISH LINE RECEIVER STATISTICS")
        logger.info(f"Total Started:        {self.tracker.total_started}")
        logger.info(f"Total Finished:       {self.tracker.total_finished}")
        logger.info(f"Currently On Water:   {on_water}")
        logger.info(f"Active Alerts:        {len(alerts)}")
        if node_info:
            logger.info(f"Mesh Messages Received: {node_info.get('messages_received', 0)}")
        logger.info("=" * 60)


def main():
    """Main entry point."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create and run receiver
    receiver = FinishLineReceiver()
    receiver.run()


if __name__ == '__main__':
    main()
