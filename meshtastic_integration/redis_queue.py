"""
Redis Queue Manager for RFID Messages

Handles queueing, rate limiting, and message persistence.
"""

import redis
import json
import time
import logging
from datetime import datetime
from typing import Dict, Optional, List

from config import (
    REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD,
    REDIS_QUEUE_START, REDIS_QUEUE_FINISH, REDIS_QUEUE_FAILED,
    MESSAGE_EXPIRATION_TIME, MAX_QUEUE_SIZE,
    get_transmission_delay, QUEUE_ALERT_WARNING, QUEUE_ALERT_CRITICAL
)

logger = logging.getLogger(__name__)


class RedisQueue:
    """
    Redis-based message queue with persistence and monitoring.
    """

    def __init__(self, queue_name: str = REDIS_QUEUE_START):
        """
        Initialize Redis connection and queue.

        Args:
            queue_name: Name of the Redis queue to use
        """
        self.queue_name = queue_name
        self.redis_client = None
        self.connect()

    def connect(self):
        """Establish connection to Redis server."""
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def enqueue(self, message: Dict) -> bool:
        """
        Add a message to the queue.

        Args:
            message: Dictionary containing message data

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check queue size
            current_size = self.get_depth()
            if current_size >= MAX_QUEUE_SIZE:
                logger.error(f"Queue full ({current_size} messages). Cannot enqueue.")
                return False

            # Add queue timestamp if not present
            if 'queue_time' not in message:
                message['queue_time'] = datetime.utcnow().isoformat()

            # Convert message to JSON and push to queue
            message_json = json.dumps(message)
            self.redis_client.rpush(self.queue_name, message_json)

            logger.debug(f"Enqueued message: {message.get('rfid', 'unknown')} "
                        f"(queue depth: {current_size + 1})")
            return True

        except Exception as e:
            logger.error(f"Error enqueueing message: {e}")
            return False

    def dequeue(self) -> Optional[Dict]:
        """
        Remove and return the next message from the queue.

        Returns:
            Message dictionary or None if queue is empty
        """
        try:
            # Pop from left (FIFO)
            message_json = self.redis_client.lpop(self.queue_name)

            if message_json:
                message = json.loads(message_json)
                logger.debug(f"Dequeued message: {message.get('rfid', 'unknown')}")
                return message
            return None

        except Exception as e:
            logger.error(f"Error dequeuing message: {e}")
            return None

    def peek(self) -> Optional[Dict]:
        """
        View the next message without removing it.

        Returns:
            Message dictionary or None if queue is empty
        """
        try:
            message_json = self.redis_client.lindex(self.queue_name, 0)
            if message_json:
                return json.loads(message_json)
            return None
        except Exception as e:
            logger.error(f"Error peeking at message: {e}")
            return None

    def get_depth(self) -> int:
        """
        Get current queue depth.

        Returns:
            Number of messages in queue
        """
        try:
            return self.redis_client.llen(self.queue_name)
        except Exception as e:
            logger.error(f"Error getting queue depth: {e}")
            return 0

    def get_all_messages(self) -> List[Dict]:
        """
        Get all messages in the queue without removing them.

        Returns:
            List of message dictionaries
        """
        try:
            messages_json = self.redis_client.lrange(self.queue_name, 0, -1)
            messages = [json.loads(msg) for msg in messages_json]
            return messages
        except Exception as e:
            logger.error(f"Error getting all messages: {e}")
            return []

    def move_to_failed(self, message: Dict, error_reason: str):
        """
        Move a message to the failed queue.

        Args:
            message: Message that failed to transmit
            error_reason: Description of why it failed
        """
        try:
            message['failed_at'] = datetime.utcnow().isoformat()
            message['failure_reason'] = error_reason
            message_json = json.dumps(message)
            self.redis_client.rpush(REDIS_QUEUE_FAILED, message_json)
            logger.warning(f"Moved message to failed queue: {message.get('rfid')} - {error_reason}")
        except Exception as e:
            logger.error(f"Error moving message to failed queue: {e}")

    def get_oldest_message_age(self) -> Optional[float]:
        """
        Get age of oldest message in queue.

        Returns:
            Age in seconds, or None if queue is empty
        """
        try:
            message = self.peek()
            if message and 'queue_time' in message:
                queue_time = datetime.fromisoformat(message['queue_time'])
                age = (datetime.utcnow() - queue_time).total_seconds()
                return age
            return None
        except Exception as e:
            logger.error(f"Error calculating oldest message age: {e}")
            return None

    def cleanup_expired_messages(self):
        """
        Move expired messages to failed queue.
        Messages older than MESSAGE_EXPIRATION_TIME are considered expired.
        """
        try:
            messages = self.get_all_messages()
            now = datetime.utcnow()
            expired_count = 0

            for message in messages:
                if 'queue_time' in message:
                    queue_time = datetime.fromisoformat(message['queue_time'])
                    age = (now - queue_time).total_seconds()

                    if age > MESSAGE_EXPIRATION_TIME:
                        # Remove from queue and move to failed
                        self.dequeue()  # Remove oldest (FIFO)
                        self.move_to_failed(message, f"Expired after {age:.0f} seconds")
                        expired_count += 1

            if expired_count > 0:
                logger.warning(f"Cleaned up {expired_count} expired messages")

        except Exception as e:
            logger.error(f"Error cleaning up expired messages: {e}")

    def get_stats(self) -> Dict:
        """
        Get queue statistics.

        Returns:
            Dictionary with queue stats
        """
        try:
            depth = self.get_depth()
            oldest_age = self.get_oldest_message_age()
            failed_count = self.redis_client.llen(REDIS_QUEUE_FAILED)

            # Determine alert level
            alert_level = 'normal'
            if depth >= QUEUE_ALERT_CRITICAL:
                alert_level = 'critical'
            elif depth >= QUEUE_ALERT_WARNING:
                alert_level = 'warning'

            return {
                'queue_name': self.queue_name,
                'depth': depth,
                'oldest_message_age': oldest_age,
                'failed_count': failed_count,
                'alert_level': alert_level,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {}

    def clear_queue(self):
        """Clear all messages from the queue. USE WITH CAUTION."""
        try:
            count = self.get_depth()
            self.redis_client.delete(self.queue_name)
            logger.warning(f"Cleared {count} messages from queue {self.queue_name}")
        except Exception as e:
            logger.error(f"Error clearing queue: {e}")

    def is_healthy(self) -> bool:
        """
        Check if Redis connection is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            self.redis_client.ping()
            return True
        except:
            return False


class RateLimitedQueueProcessor:
    """
    Processes queue messages with adaptive rate limiting.
    """

    def __init__(self, queue: RedisQueue, transmit_callback):
        """
        Initialize the processor.

        Args:
            queue: RedisQueue instance
            transmit_callback: Function to call for transmitting messages
        """
        self.queue = queue
        self.transmit_callback = transmit_callback
        self.running = False
        self.messages_transmitted = 0
        self.messages_failed = 0
        self.last_transmission_time = 0

    def start(self):
        """Start processing messages from the queue."""
        self.running = True
        logger.info("Starting rate-limited queue processor")

        while self.running:
            try:
                self._process_next_message()
            except Exception as e:
                logger.error(f"Error in queue processor: {e}")
                time.sleep(1)

    def stop(self):
        """Stop processing messages."""
        self.running = False
        logger.info("Stopping queue processor")

    def _process_next_message(self):
        """Process the next message in the queue with rate limiting."""
        depth = self.queue.get_depth()

        if depth > 0:
            # Get adaptive delay based on queue depth
            delay = get_transmission_delay(depth)

            # Wait for rate limit
            elapsed = time.time() - self.last_transmission_time
            if elapsed < delay:
                time.sleep(delay - elapsed)

            # Get and transmit message
            message = self.queue.dequeue()
            if message:
                try:
                    success = self.transmit_callback(message)
                    if success:
                        self.messages_transmitted += 1
                        self.last_transmission_time = time.time()
                        logger.info(f"Transmitted RFID {message.get('rfid')} "
                                  f"(queue depth: {depth - 1})")
                    else:
                        self.messages_failed += 1
                        self.queue.move_to_failed(message, "Transmission failed")
                except Exception as e:
                    logger.error(f"Error transmitting message: {e}")
                    self.messages_failed += 1
                    self.queue.move_to_failed(message, str(e))
        else:
            # Queue empty, check less frequently
            time.sleep(0.5)

    def get_stats(self) -> Dict:
        """Get processor statistics."""
        return {
            'messages_transmitted': self.messages_transmitted,
            'messages_failed': self.messages_failed,
            'running': self.running
        }
