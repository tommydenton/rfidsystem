"""
Queue Monitor - Health Monitoring and Alerting

Monitors Redis queue health, Meshtastic connectivity, and system performance.
"""

import time
import logging
from datetime import datetime
from typing import Dict, List

from config import (
    QUEUE_MONITOR_INTERVAL,
    QUEUE_ALERT_WARNING,
    QUEUE_ALERT_CRITICAL,
    MESSAGE_EXPIRATION_TIME
)
from redis_queue import RedisQueue, REDIS_QUEUE_START, REDIS_QUEUE_FINISH, REDIS_QUEUE_FAILED

logger = logging.getLogger(__name__)


class QueueMonitor:
    """
    Monitors queue health and generates alerts.
    """

    def __init__(self):
        """Initialize the monitor."""
        self.start_queue = RedisQueue(REDIS_QUEUE_START)
        self.finish_queue = RedisQueue(REDIS_QUEUE_FINISH)
        self.failed_queue = RedisQueue(REDIS_QUEUE_FAILED)

        self.running = False
        self.alerts = []

        # Statistics
        self.total_checks = 0
        self.total_warnings = 0
        self.total_critical = 0

    def check_queue_health(self, queue: RedisQueue, queue_name: str) -> Dict:
        """
        Check health of a specific queue.

        Args:
            queue: RedisQueue instance
            queue_name: Name for logging

        Returns:
            Health status dictionary
        """
        health = {
            'queue_name': queue_name,
            'healthy': True,
            'issues': [],
            'stats': {}
        }

        try:
            # Get queue statistics
            stats = queue.get_stats()
            health['stats'] = stats

            depth = stats.get('depth', 0)
            oldest_age = stats.get('oldest_message_age')

            # Check queue depth
            if depth >= QUEUE_ALERT_CRITICAL:
                health['healthy'] = False
                health['issues'].append(f"CRITICAL: Queue depth {depth} exceeds critical threshold")
                self.total_critical += 1
            elif depth >= QUEUE_ALERT_WARNING:
                health['issues'].append(f"WARNING: Queue depth {depth} exceeds warning threshold")
                self.total_warnings += 1

            # Check message age
            if oldest_age and oldest_age > MESSAGE_EXPIRATION_TIME:
                health['healthy'] = False
                health['issues'].append(f"CRITICAL: Oldest message is {oldest_age / 60:.1f} minutes old")
                self.total_critical += 1
            elif oldest_age and oldest_age > (MESSAGE_EXPIRATION_TIME * 0.5):
                health['issues'].append(f"WARNING: Oldest message is {oldest_age / 60:.1f} minutes old")
                self.total_warnings += 1

            # Check Redis connectivity
            if not queue.is_healthy():
                health['healthy'] = False
                health['issues'].append("CRITICAL: Redis connection lost")
                self.total_critical += 1

        except Exception as e:
            health['healthy'] = False
            health['issues'].append(f"ERROR: Failed to check queue health: {e}")
            logger.error(f"Error checking queue health: {e}")

        return health

    def check_failed_queue(self) -> Dict:
        """
        Check the failed messages queue.

        Returns:
            Health status dictionary
        """
        health = {
            'queue_name': 'failed',
            'healthy': True,
            'issues': [],
            'stats': {}
        }

        try:
            failed_count = self.failed_queue.get_depth()
            health['stats']['failed_count'] = failed_count

            # Warn if there are failed messages
            if failed_count > 0:
                health['issues'].append(f"WARNING: {failed_count} messages in failed queue")
                self.total_warnings += 1

                # Get details of failed messages
                failed_messages = self.failed_queue.get_all_messages()

                if failed_messages:
                    # Group by failure reason
                    reasons = {}
                    for msg in failed_messages:
                        reason = msg.get('failure_reason', 'Unknown')
                        reasons[reason] = reasons.get(reason, 0) + 1

                    health['stats']['failure_reasons'] = reasons

        except Exception as e:
            health['healthy'] = False
            health['issues'].append(f"ERROR: Failed to check failed queue: {e}")

        return health

    def generate_report(self) -> Dict:
        """
        Generate a comprehensive health report.

        Returns:
            Health report dictionary
        """
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_healthy': True,
            'queues': {},
            'summary': {
                'total_checks': self.total_checks,
                'total_warnings': self.total_warnings,
                'total_critical': self.total_critical
            }
        }

        # Check all queues
        start_health = self.check_queue_health(self.start_queue, 'start')
        finish_health = self.check_queue_health(self.finish_queue, 'finish')
        failed_health = self.check_failed_queue()

        report['queues']['start'] = start_health
        report['queues']['finish'] = finish_health
        report['queues']['failed'] = failed_health

        # Determine overall health
        if not start_health['healthy'] or not finish_health['healthy'] or not failed_health['healthy']:
            report['overall_healthy'] = False

        self.total_checks += 1

        return report

    def print_report(self, report: Dict):
        """
        Print a formatted health report.

        Args:
            report: Health report dictionary
        """
        logger.info("=" * 70)
        logger.info("QUEUE HEALTH REPORT")
        logger.info(f"Timestamp: {report['timestamp']}")
        logger.info(f"Overall Status: {'✓ HEALTHY' if report['overall_healthy'] else '✗ UNHEALTHY'}")
        logger.info("=" * 70)

        # Print each queue
        for queue_name, queue_health in report['queues'].items():
            if queue_name == 'failed':
                continue  # Handle separately

            stats = queue_health.get('stats', {})
            depth = stats.get('depth', 0)
            oldest_age = stats.get('oldest_message_age')

            logger.info(f"\n{queue_name.upper()} Queue:")
            logger.info(f"  Depth: {depth}")
            if oldest_age:
                logger.info(f"  Oldest Message: {oldest_age / 60:.1f} minutes")
            logger.info(f"  Status: {'✓' if queue_health['healthy'] else '✗'}")

            # Print issues
            if queue_health['issues']:
                logger.info("  Issues:")
                for issue in queue_health['issues']:
                    logger.info(f"    - {issue}")

        # Print failed queue summary
        failed_health = report['queues'].get('failed', {})
        failed_stats = failed_health.get('stats', {})
        failed_count = failed_stats.get('failed_count', 0)

        logger.info(f"\nFailed Messages: {failed_count}")
        if failed_count > 0:
            reasons = failed_stats.get('failure_reasons', {})
            logger.info("  Failure Reasons:")
            for reason, count in reasons.items():
                logger.info(f"    - {reason}: {count}")

        # Print summary
        summary = report['summary']
        logger.info("\nSummary:")
        logger.info(f"  Total Checks: {summary['total_checks']}")
        logger.info(f"  Total Warnings: {summary['total_warnings']}")
        logger.info(f"  Total Critical: {summary['total_critical']}")
        logger.info("=" * 70)

    def cleanup_expired_messages(self):
        """Clean up expired messages from all queues."""
        try:
            logger.info("Running expired message cleanup...")
            self.start_queue.cleanup_expired_messages()
            self.finish_queue.cleanup_expired_messages()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def run(self):
        """Main monitoring loop."""
        self.running = True
        logger.info("Starting Queue Monitor")
        logger.info(f"Check interval: {QUEUE_MONITOR_INTERVAL} seconds")

        try:
            while self.running:
                # Generate and print report
                report = self.generate_report()
                self.print_report(report)

                # Clean up expired messages
                self.cleanup_expired_messages()

                # Sleep until next check
                time.sleep(QUEUE_MONITOR_INTERVAL)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop()

    def stop(self):
        """Stop the monitor."""
        self.running = False
        logger.info("Stopping Queue Monitor")


class SystemMonitor:
    """
    Comprehensive system monitor including queue, Meshtastic, and database health.
    """

    def __init__(self, meshtastic_interface=None, database_connection=None):
        """
        Initialize system monitor.

        Args:
            meshtastic_interface: Optional MeshtasticInterface instance
            database_connection: Optional database connection
        """
        self.queue_monitor = QueueMonitor()
        self.meshtastic = meshtastic_interface
        self.db_conn = database_connection

    def check_meshtastic_health(self) -> Dict:
        """
        Check Meshtastic connection health.

        Returns:
            Health status dictionary
        """
        health = {
            'component': 'meshtastic',
            'healthy': True,
            'issues': []
        }

        if not self.meshtastic:
            health['healthy'] = False
            health['issues'].append("No Meshtastic interface configured")
            return health

        try:
            if not self.meshtastic.is_healthy():
                health['healthy'] = False
                health['issues'].append("Meshtastic connection not healthy")

            node_info = self.meshtastic.get_node_info()
            if node_info:
                health['stats'] = node_info
            else:
                health['issues'].append("Unable to get node info")

        except Exception as e:
            health['healthy'] = False
            health['issues'].append(f"Error checking Meshtastic: {e}")

        return health

    def check_database_health(self) -> Dict:
        """
        Check database connection health.

        Returns:
            Health status dictionary
        """
        health = {
            'component': 'database',
            'healthy': True,
            'issues': []
        }

        if not self.db_conn:
            health['healthy'] = False
            health['issues'].append("No database connection configured")
            return health

        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
        except Exception as e:
            health['healthy'] = False
            health['issues'].append(f"Database connection error: {e}")

        return health

    def generate_system_report(self) -> Dict:
        """
        Generate comprehensive system health report.

        Returns:
            System health report
        """
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_healthy': True,
            'components': {}
        }

        # Queue health
        queue_report = self.queue_monitor.generate_report()
        report['components']['queues'] = queue_report

        if not queue_report['overall_healthy']:
            report['overall_healthy'] = False

        # Meshtastic health
        meshtastic_health = self.check_meshtastic_health()
        report['components']['meshtastic'] = meshtastic_health

        if not meshtastic_health['healthy']:
            report['overall_healthy'] = False

        # Database health
        db_health = self.check_database_health()
        report['components']['database'] = db_health

        if not db_health['healthy']:
            report['overall_healthy'] = False

        return report


def main():
    """Main entry point for standalone queue monitor."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create and run monitor
    monitor = QueueMonitor()
    monitor.run()


if __name__ == '__main__':
    main()
