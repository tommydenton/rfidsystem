#!/usr/bin/env python3
"""
Example Test Script for RFID Meshtastic Integration

This script demonstrates how to:
1. Create test RFID reads
2. Queue messages to Redis
3. Send messages via Meshtastic (simulation mode)
4. Monitor queue health

Run this to verify your setup is working correctly.
"""

import json
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_redis_connection():
    """Test Redis connection."""
    logger.info("=" * 70)
    logger.info("TEST 1: Redis Connection")
    logger.info("=" * 70)

    try:
        from redis_queue import RedisQueue

        queue = RedisQueue()
        logger.info("✓ Successfully connected to Redis")

        # Test basic operations
        test_message = {
            'rfid': 'TEST001',
            'timestamp': time.time(),
            'message_type': 'START',
            'test': True
        }

        # Enqueue
        success = queue.enqueue(test_message)
        if success:
            logger.info("✓ Successfully enqueued test message")
        else:
            logger.error("✗ Failed to enqueue test message")
            return False

        # Get depth
        depth = queue.get_depth()
        logger.info(f"✓ Queue depth: {depth}")

        # Dequeue
        message = queue.dequeue()
        if message and message.get('rfid') == 'TEST001':
            logger.info("✓ Successfully dequeued test message")
        else:
            logger.error("✗ Failed to dequeue test message")
            return False

        logger.info("✓ Redis tests PASSED")
        return True

    except Exception as e:
        logger.error(f"✗ Redis test FAILED: {e}")
        return False


def test_meshtastic_interface():
    """Test Meshtastic interface (simulation mode)."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("TEST 2: Meshtastic Interface (Simulation Mode)")
    logger.info("=" * 70)

    try:
        # Enable simulation mode
        import config
        config.SIMULATE_MESSAGES = True

        from meshtastic_interface import MeshtasticInterface

        mesh = MeshtasticInterface()
        logger.info("✓ Meshtastic interface created")

        # Send test message
        success = mesh.send_rfid_start(
            rfid='TEST002',
            timestamp=time.time(),
            tag_data={'tag_type': 'E200TEST', 'tag_position': 'A001'}
        )

        if success:
            logger.info("✓ Successfully sent test message (simulated)")
        else:
            logger.error("✗ Failed to send test message")
            return False

        # Get node info
        node_info = mesh.get_node_info()
        if node_info:
            logger.info(f"✓ Node info: {node_info}")
        else:
            logger.info("⚠ No node info available (expected in simulation mode)")

        logger.info("✓ Meshtastic tests PASSED")
        return True

    except Exception as e:
        logger.error(f"✗ Meshtastic test FAILED: {e}")
        return False


def test_departure_tracker():
    """Test the 5-minute departure tracking logic."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("TEST 3: Departure Tracker (Accelerated)")
    logger.info("=" * 70)

    try:
        from start_line_sender import DepartureTracker

        # Use 5-second wait time for testing (instead of 5 minutes)
        tracker = DepartureTracker(wait_time=5)
        logger.info("✓ Created departure tracker (5 second wait time)")

        # Record an RFID read
        test_rfid = 'TEST003'
        test_time = time.time()

        tracker.record_rfid_read(test_rfid, test_time)
        logger.info(f"✓ Recorded RFID read for {test_rfid}")

        # Check pending count
        pending = tracker.get_pending_count()
        if pending == 1:
            logger.info(f"✓ Pending count: {pending}")
        else:
            logger.error(f"✗ Expected pending count 1, got {pending}")
            return False

        # Wait less than 5 seconds and check
        logger.info("⏳ Waiting 3 seconds...")
        time.sleep(3)

        confirmed = tracker.get_confirmed_departures()
        if len(confirmed) == 0:
            logger.info("✓ No departures confirmed yet (expected)")
        else:
            logger.error("✗ Departure confirmed too early")
            return False

        # Wait for confirmation
        logger.info("⏳ Waiting 3 more seconds (total 6)...")
        time.sleep(3)

        confirmed = tracker.get_confirmed_departures()
        if len(confirmed) == 1 and confirmed[0]['rfid'] == test_rfid:
            logger.info(f"✓ Departure confirmed for {test_rfid}")
        else:
            logger.error("✗ Departure not confirmed after wait time")
            return False

        logger.info("✓ Departure tracker tests PASSED")
        return True

    except Exception as e:
        logger.error(f"✗ Departure tracker test FAILED: {e}")
        return False


def test_queue_monitor():
    """Test queue monitoring."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("TEST 4: Queue Monitor")
    logger.info("=" * 70)

    try:
        from queue_monitor import QueueMonitor

        monitor = QueueMonitor()
        logger.info("✓ Created queue monitor")

        # Generate a report
        report = monitor.generate_report()
        logger.info("✓ Generated health report")

        # Print report
        monitor.print_report(report)

        logger.info("✓ Queue monitor tests PASSED")
        return True

    except Exception as e:
        logger.error(f"✗ Queue monitor test FAILED: {e}")
        return False


def test_message_flow():
    """Test complete message flow (simulation mode)."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("TEST 5: Complete Message Flow (Simulation)")
    logger.info("=" * 70)

    try:
        # Enable simulation mode
        import config
        config.SIMULATE_MESSAGES = True

        from redis_queue import RedisQueue, RateLimitedQueueProcessor
        from meshtastic_interface import MeshtasticInterface

        # Create components
        queue = RedisQueue()
        mesh = MeshtasticInterface()

        logger.info("✓ Created queue and Meshtastic interface")

        # Create test messages
        test_rfids = ['TEST100', 'TEST101', 'TEST102']
        for rfid in test_rfids:
            message = {
                'rfid': rfid,
                'timestamp': time.time(),
                'timestamp_h': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'message_type': 'START',
                'station_id': 'TEST_STATION',
                'priority': 'normal'
            }
            queue.enqueue(message)

        logger.info(f"✓ Enqueued {len(test_rfids)} test messages")
        logger.info(f"✓ Queue depth: {queue.get_depth()}")

        # Process messages
        def transmit_callback(msg):
            return mesh.send_message(msg)

        processor = RateLimitedQueueProcessor(queue, transmit_callback)

        logger.info("⏳ Processing messages...")

        # Process a few messages
        for i in range(len(test_rfids)):
            processor._process_next_message()
            time.sleep(0.5)

        # Check queue is empty
        depth = queue.get_depth()
        if depth == 0:
            logger.info("✓ All messages processed")
        else:
            logger.warning(f"⚠ Queue still has {depth} messages")

        # Check stats
        stats = processor.get_stats()
        logger.info(f"✓ Messages transmitted: {stats['messages_transmitted']}")
        logger.info(f"✓ Messages failed: {stats['messages_failed']}")

        logger.info("✓ Message flow tests PASSED")
        return True

    except Exception as e:
        logger.error(f"✗ Message flow test FAILED: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("RFID MESHTASTIC INTEGRATION - TEST SUITE")
    logger.info("=" * 70)
    logger.info("")

    results = {
        'Redis Connection': test_redis_connection(),
        'Meshtastic Interface': test_meshtastic_interface(),
        'Departure Tracker': test_departure_tracker(),
        'Queue Monitor': test_queue_monitor(),
        'Message Flow': test_message_flow()
    }

    # Print summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)

    passed = 0
    failed = 0

    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{test_name:.<40} {status}")
        if result:
            passed += 1
        else:
            failed += 1

    logger.info("-" * 70)
    logger.info(f"Total: {passed + failed} | Passed: {passed} | Failed: {failed}")
    logger.info("=" * 70)

    if failed == 0:
        logger.info("")
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Configure config.py for your hardware")
        logger.info("2. Connect your Meshtastic device")
        logger.info("3. Update MESHTASTIC_SERIAL_PORT in config.py")
        logger.info("4. Run: python3 start_line_sender.py")
        logger.info("")
        return 0
    else:
        logger.error("")
        logger.error("⚠ SOME TESTS FAILED")
        logger.error("Check the errors above and verify your configuration")
        logger.error("")
        return 1


if __name__ == '__main__':
    exit(main())
