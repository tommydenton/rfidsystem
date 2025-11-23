"""
Start Line Monitor - RFID Tracking and Safety Dashboard

Monitors local RFID reads, receives FINISH messages via Meshtastic,
and tracks which RFIDs are currently on the water for safety monitoring.
"""

import json
import time
import logging
import threading
import psycopg2
from datetime import datetime
from typing import Dict, Optional

from config import (
    DEPARTURE_WAIT_TIME,
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
    RFID_OUTPUT_DIR, RFID_OUTPUT_FILE,
    FILE_MONITOR_INTERVAL,
    STATION_ID,
    get_alert_level
)
from meshtastic_interface import MeshtasticInterface

logger = logging.getLogger(__name__)


class DepartureTracker:
    """
    Tracks RFID reads and implements 5-minute wait logic.

    The 5-minute wait ensures that paddlers have actually departed
    the start area before their time is considered official.
    """

    def __init__(self, wait_time: int = DEPARTURE_WAIT_TIME):
        """
        Initialize departure tracker.

        Args:
            wait_time: Seconds to wait before confirming departure
        """
        self.wait_time = wait_time
        self.pending_departures = {}  # rfid -> {'first_seen': timestamp, 'last_seen': timestamp, 'data': dict}
        self.confirmed_departures = {}  # rfid -> {'timestamp': float, 'data': dict}
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

                    # Move to confirmed
                    self.confirmed_departures[rfid] = {
                        'timestamp': data['first_seen'],
                        'data': data['data']
                    }

                    wait_minutes = self.wait_time / 60
                    logger.info(f"Confirmed departure for RFID {rfid} after {wait_minutes:.1f} minute wait")

            # Remove confirmed RFIDs from pending
            for rfid in rfids_to_remove:
                del self.pending_departures[rfid]

        return confirmed

    def get_start_time(self, rfid: str) -> Optional[float]:
        """
        Get the confirmed start time for an RFID.

        Args:
            rfid: RFID tag ID

        Returns:
            Start timestamp or None if not found
        """
        with self.lock:
            if rfid in self.confirmed_departures:
                return self.confirmed_departures[rfid]['timestamp']
            return None

    def get_pending_count(self) -> int:
        """Get count of RFIDs pending confirmation."""
        with self.lock:
            return len(self.pending_departures)

    def get_confirmed_count(self) -> int:
        """Get count of confirmed departures."""
        with self.lock:
            return len(self.confirmed_departures)


class OnWaterTracker:
    """
    Tracks RFIDs that are currently on the water.
    Combines local START times with received FINISH messages.
    """

    def __init__(self, departure_tracker: DepartureTracker):
        """
        Initialize the tracker.

        Args:
            departure_tracker: DepartureTracker instance for getting start times
        """
        self.departure_tracker = departure_tracker
        self.finished_rfids = {}  # rfid -> finish_timestamp
        self.lock = threading.Lock()

        # Statistics
        self.total_finished = 0
        self.messages_received = 0

    def record_finish(self, rfid: str, finish_timestamp: float, finish_data: Dict = None):
        """
        Record an RFID finish from Meshtastic message.

        Args:
            rfid: RFID tag ID
            finish_timestamp: Unix timestamp of finish
            finish_data: Optional finish message data
        """
        with self.lock:
            start_time = self.departure_tracker.get_start_time(rfid)

            if start_time:
                duration = finish_timestamp - start_time
                self.finished_rfids[rfid] = {
                    'finish_timestamp': finish_timestamp,
                    'start_timestamp': start_time,
                    'duration': duration,
                    'data': finish_data or {}
                }
                self.total_finished += 1

                logger.info(f"RFID {rfid} finished - duration {duration / 3600:.2f} hours "
                          f"({self.get_on_water_count()} remaining on water)")
                return duration
            else:
                logger.warning(f"RFID {rfid} finished but no start record found")
                # Still record the finish
                self.finished_rfids[rfid] = {
                    'finish_timestamp': finish_timestamp,
                    'start_timestamp': None,
                    'duration': None,
                    'data': finish_data or {}
                }
                self.total_finished += 1
                return None

    def get_on_water_count(self) -> int:
        """Get count of RFIDs currently on water."""
        with self.lock:
            started = self.departure_tracker.get_confirmed_count()
            finished = len(self.finished_rfids)
            return max(0, started - finished)

    def get_on_water_rfids(self) -> Dict:
        """
        Get all RFIDs currently on water with their data.

        Returns:
            Dictionary of rfid -> start_data
        """
        with self.lock:
            on_water = {}

            # Get all confirmed departures
            for rfid, start_data in self.departure_tracker.confirmed_departures.items():
                # Check if not yet finished
                if rfid not in self.finished_rfids:
                    on_water[rfid] = start_data

            return on_water

    def get_alerts(self) -> list:
        """
        Get RFIDs that exceed time thresholds.

        Returns:
            List of alert dictionaries
        """
        alerts = []
        current_time = time.time()

        on_water = self.get_on_water_rfids()

        for rfid, start_data in on_water.items():
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


class StartLineMonitor:
    """
    Main class for start line operations.
    Monitors local RFID reads and receives FINISH messages to track on-water status.
    """

    def __init__(self):
        """Initialize the start line monitor."""
        self.departure_tracker = DepartureTracker()
        self.on_water_tracker = OnWaterTracker(self.departure_tracker)
        self.meshtastic = MeshtasticInterface(on_receive_callback=self.on_message_received)
        self.running = False

        # Database connection
        self.db_conn = None
        self.connect_database()

        # Statistics
        self.rfids_read = 0

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

    def save_finish_to_database(self, message: Dict):
        """
        Save received FINISH message to a tracking table.

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
                CREATE TABLE IF NOT EXISTS meshtastic_finishes (
                    id SERIAL PRIMARY KEY,
                    rfid VARCHAR(255) NOT NULL,
                    finish_timestamp DOUBLE PRECISION,
                    finish_timestamp_h VARCHAR(255),
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    station_id VARCHAR(255),
                    tag_type VARCHAR(255),
                    tag_position VARCHAR(255),
                    message_data JSONB
                )
                """
            )

            # Insert the finish message
            cursor.execute(
                """
                INSERT INTO meshtastic_finishes
                (rfid, finish_timestamp, finish_timestamp_h, station_id, tag_type, tag_position, message_data)
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
            logger.debug(f"Saved FINISH message for RFID {message.get('rfid')} to database")

        except Exception as e:
            logger.error(f"Error saving FINISH message to database: {e}")
            self.db_conn.rollback()

    def on_message_received(self, message: Dict):
        """
        Callback when a FINISH message is received via Meshtastic.

        Args:
            message: Message dictionary
        """
        try:
            message_type = message.get('message_type')
            rfid = message.get('rfid')

            if not rfid:
                logger.warning("Received message without RFID")
                return

            if message_type == 'FINISH':
                # Record finish
                timestamp = message.get('timestamp')
                if timestamp:
                    self.on_water_tracker.record_finish(rfid, timestamp, message)

                    # Save to database
                    self.save_finish_to_database(message)

                    logger.info(f"Received FINISH for RFID {rfid} from {message.get('station_id')}")
                else:
                    logger.warning(f"FINISH message for {rfid} missing timestamp")

            else:
                logger.debug(f"Received message type: {message_type}")

        except Exception as e:
            logger.error(f"Error processing received message: {e}")

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
        Process a single RFID read (START).

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
        Check for confirmed departures (for local tracking only, no transmission).
        """
        confirmed = self.departure_tracker.get_confirmed_departures()

        for departure in confirmed:
            logger.info(f"RFID {departure['rfid']} confirmed on water at "
                       f"{datetime.fromtimestamp(departure['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")

    def check_alerts(self):
        """Check for and log any safety alerts."""
        alerts = self.on_water_tracker.get_alerts()

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
        logger.info("Starting Start Line Monitor")
        logger.info(f"Departure wait time: {DEPARTURE_WAIT_TIME / 60:.1f} minutes")
        logger.info(f"Listening for FINISH messages from finish line")

        try:
            while self.running:
                # Monitor for new RFID reads (starts)
                self.monitor_json_file()

                # Check for confirmed departures (local tracking)
                self.check_confirmed_departures()

                # Check for safety alerts
                self.check_alerts()

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
        """Stop the monitor."""
        self.running = False
        logger.info("Stopping Start Line Monitor")

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
        on_water = self.on_water_tracker.get_on_water_count()
        alerts = self.on_water_tracker.get_alerts()

        logger.info("=" * 60)
        logger.info("START LINE MONITOR STATISTICS")
        logger.info(f"RFIDs Read (Starts):  {self.rfids_read}")
        logger.info(f"Pending Departures:   {self.departure_tracker.get_pending_count()}")
        logger.info(f"Confirmed Starts:     {self.departure_tracker.get_confirmed_count()}")
        logger.info(f"Finishes Received:    {self.on_water_tracker.total_finished}")
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

    # Create and run monitor
    monitor = StartLineMonitor()
    monitor.run()


if __name__ == '__main__':
    main()
