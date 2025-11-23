# RFID Meshtastic Integration

This system integrates RFID timing data with Meshtastic LoRa mesh network for reliable transmission between start and finish lines in river race events.

## System Overview

The system consists of two main stations:

### START LINE STATION
- Raspberry Pi with RFID reader
- PostgreSQL database (local timing record)
- 5-minute wait logic (ensures paddlers have departed)
- Redis queue (handles burst scenarios)
- Meshtastic LoRa radio (Heltec WiFi LoRa 32 V3)

### FINISH LINE STATION
- Raspberry Pi with RFID reader
- PostgreSQL database (finish records)
- Meshtastic LoRa radio (receives start messages)
- "On Water" tracking system
- Safety dashboard integration

### RELAY NODES
- 6× RAK WisMesh Mini repeaters
- Solar-powered
- Spaced ~1.5 miles apart along river course

## Key Features

- **5-Minute Wait Logic**: Prevents false starts by waiting 5 minutes before transmitting
- **Burst Handling**: Redis queue absorbs 30+ simultaneous departures
- **Rate Limiting**: Adaptive delays (2-3 seconds) prevent LoRa collisions
- **Safety Alerts**: Track time on water with configurable thresholds
- **Reliability**: Local databases maintain complete records regardless of transmission success

## Components

```
meshtastic_integration/
├── config.py                    # All tunable parameters
├── redis_queue.py               # Queue management and rate limiting
├── meshtastic_interface.py     # LoRa communication
├── start_line_sender.py         # Start line operations
├── finish_line_receiver.py      # Finish line operations
├── queue_monitor.py             # Health monitoring and alerts
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Installation

### Prerequisites

1. **Hardware**:
   - Raspberry Pi (tested on Pi 4)
   - Heltec WiFi LoRa 32 V3 (connected via USB)
   - PostgreSQL database running
   - Redis server

2. **Software**:
   - Python 3.8+
   - PostgreSQL 12+
   - Redis 6+

### Step 1: Install Redis

```bash
# On Debian/Raspberry Pi OS
sudo apt update
sudo apt install redis-server

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify Redis is running
redis-cli ping
# Should respond: PONG
```

### Step 2: Install Python Dependencies

```bash
cd /home/user/rfidsystem/meshtastic_integration

# Install dependencies
pip3 install -r requirements.txt
```

### Step 3: Connect Meshtastic Device

```bash
# Connect Heltec V3 via USB
# Find the device port
ls /dev/ttyUSB*

# Should show something like /dev/ttyUSB2
# Update config.py with the correct port
```

### Step 4: Configure the System

Edit `config.py` to match your setup:

```python
# Key parameters to configure:

# Station type (START or FINISH)
STATION_TYPE = 'START'  # or 'FINISH'
STATION_ID = 'START_LINE_1'

# 5-minute wait time (300 seconds)
DEPARTURE_WAIT_TIME = 300

# Meshtastic serial port
MESHTASTIC_SERIAL_PORT = '/dev/ttyUSB2'

# Database connection
DB_HOST = 'localhost'
DB_NAME = 'rfid_system'
DB_USER = 'postgres'
DB_PASSWORD = 'your_password'

# Safety alert thresholds
ALERT_YELLOW_THRESHOLD = 14400   # 4 hours
ALERT_RED_THRESHOLD = 21600      # 6 hours
ALERT_CRITICAL_THRESHOLD = 28800  # 8 hours
```

## Configuration Variables

All configurable parameters are in `config.py`:

### Timing Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `DEPARTURE_WAIT_TIME` | 300 | Seconds to wait before confirming departure |
| `TRANSMISSION_DELAY_NORMAL` | 3.0 | Normal spacing between messages (seconds) |
| `TRANSMISSION_DELAY_MEDIUM` | 2.5 | Medium queue depth spacing |
| `TRANSMISSION_DELAY_FAST` | 2.0 | High queue depth spacing |
| `QUEUE_DEPTH_HIGH` | 50 | Threshold for fast mode |
| `QUEUE_DEPTH_MEDIUM` | 20 | Threshold for medium mode |

### Queue Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `QUEUE_ALERT_WARNING` | 50 | Warning threshold for queue depth |
| `QUEUE_ALERT_CRITICAL` | 100 | Critical threshold for queue depth |
| `MAX_QUEUE_SIZE` | 1000 | Maximum messages in queue |
| `MESSAGE_EXPIRATION_TIME` | 3600 | Message expiry time (seconds) |

### Safety Alert Thresholds

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ALERT_YELLOW_THRESHOLD` | 14400 | 4 hours - Yellow alert |
| `ALERT_RED_THRESHOLD` | 21600 | 6 hours - Red alert |
| `ALERT_CRITICAL_THRESHOLD` | 28800 | 8 hours - Critical alert |

## Usage

### Start Line Station

Run the start line sender:

```bash
cd /home/user/rfidsystem/meshtastic_integration
python3 start_line_sender.py
```

**What it does**:
1. Monitors RFID reads from the existing stamper.py system
2. Tracks each RFID for 5 minutes
3. If RFID is not re-read within 5 minutes, confirms departure
4. Queues confirmed departures to Redis
5. Transmits messages via Meshtastic with rate limiting

**Expected output**:
```
INFO - Starting Start Line Sender
INFO - Departure wait time: 5.0 minutes
INFO - Connected to Redis at localhost:6379
INFO - Connected to Meshtastic via serial: /dev/ttyUSB2
INFO - New RFID detected: 2302 at 2025-10-01 08:15:23
INFO - Confirmed departure for RFID 2302 after 5.0 minute wait
INFO - Queued departure for RFID 2302
INFO - Transmitted RFID 2302 (queue depth: 0)
```

### Finish Line Station

Run the finish line receiver:

```bash
cd /home/user/rfidsystem/meshtastic_integration
python3 finish_line_receiver.py
```

**What it does**:
1. Listens for START messages via Meshtastic
2. Monitors local RFID reads for finishes
3. Tracks which RFIDs are currently on water
4. Generates safety alerts for long times on water

**Expected output**:
```
INFO - Starting Finish Line Receiver
INFO - Listening for messages on station: FINISH_LINE_1
INFO - Connected to Meshtastic via serial: /dev/ttyUSB2
INFO - Received START for RFID 2302 from START_LINE_1
INFO - RFID 2302 started - now on water (1 total on water)
INFO - RFID 2302 finished - duration 3.45 hours (0 remaining on water)
```

### Queue Monitor (Optional)

Monitor queue health:

```bash
python3 queue_monitor.py
```

**What it does**:
- Monitors Redis queue depth
- Checks for expired messages
- Reports failed transmissions
- Alerts on threshold violations

## Message Format

Messages transmitted via Meshtastic use this JSON format:

```json
{
  "rfid": "2302",
  "timestamp": 1696155323.456,
  "timestamp_h": "2025-10-01 08:15:23.456",
  "last_seen": 1696155323.456,
  "message_type": "START",
  "station_id": "START_LINE_1",
  "priority": "normal",
  "tag_type": "E2001234567890AB",
  "tag_position": "A001",
  "queue_time": "2025-10-01T08:20:23Z",
  "sent_at": "2025-10-01T08:20:25Z",
  "sent_by": "START_LINE_1"
}
```

## Testing

### Test 1: Verify Redis Connection

```bash
# Start Redis CLI
redis-cli

# Check queue
LLEN rfid:queue:start
# Should return 0 if empty

# Exit
exit
```

### Test 2: Simulate RFID Read

```bash
# Add test data to RFID JSON file
python3 << EOF
import json
import time

data = {
    "tag_type": "E2001234567890AB",
    "tag_id": "TEST001",
    "tag_position": "A001",
    "timestamp": time.time(),
    "timestamp_h": "2025-10-01|08:15:23:456"
}

with open('/var/www/html/timer/uploads/rfid_output.json', 'w') as f:
    json.dump([data], f)
EOF
```

### Test 3: Verify Message Flow

1. **Start monitor in terminal 1**:
   ```bash
   python3 queue_monitor.py
   ```

2. **Start sender in terminal 2**:
   ```bash
   python3 start_line_sender.py
   ```

3. **Start receiver in terminal 3**:
   ```bash
   python3 finish_line_receiver.py
   ```

4. **Simulate RFID read** (from test 2)

5. **Wait 5 minutes** and observe:
   - Sender: "Confirmed departure for RFID TEST001"
   - Sender: "Queued departure for RFID TEST001"
   - Sender: "Transmitted RFID TEST001"
   - Receiver: "Received START for RFID TEST001"
   - Monitor: Shows queue depth changes

## Troubleshooting

### Meshtastic Connection Issues

```bash
# Check if device is connected
ls -l /dev/ttyUSB*

# Check permissions
sudo usermod -a -G dialout $USER
# Log out and back in

# Test with meshtastic CLI
meshtastic --info
```

### Redis Connection Issues

```bash
# Check Redis status
sudo systemctl status redis-server

# Check Redis logs
sudo journalctl -u redis-server -n 50

# Test connection
redis-cli ping
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -h localhost -U postgres -d rfid_system -c "SELECT 1"

# Check database exists
psql -U postgres -c "\l" | grep rfid_system

# Check tables
psql -U postgres -d rfid_system -c "\dt"
```

### No Messages Received

1. **Check Meshtastic settings**:
   - Both devices on same channel
   - Same region settings (US)
   - Both devices showing "connected"

2. **Check message size**:
   - Messages must be < 200 bytes
   - Enable DEBUG logging to see message size

3. **Check range**:
   - Test at close range first
   - Add relay nodes for longer distances

### Queue Backing Up

If queue depth keeps growing:

1. **Check transmission rate**:
   - Are messages being sent?
   - Check Meshtastic logs

2. **Adjust delays**:
   ```python
   # In config.py
   TRANSMISSION_DELAY_FAST = 1.5  # Speed up
   ```

3. **Check for errors**:
   ```bash
   # View failed queue
   redis-cli LRANGE rfid:queue:failed 0 -1
   ```

## Performance Tuning

### For High-Volume Events (500+ boats)

```python
# config.py adjustments

# Speed up transmission during bursts
TRANSMISSION_DELAY_FAST = 1.5
TRANSMISSION_DELAY_MEDIUM = 2.0
TRANSMISSION_DELAY_NORMAL = 2.5

# Increase queue size
MAX_QUEUE_SIZE = 2000

# Adjust thresholds
QUEUE_DEPTH_HIGH = 75
QUEUE_DEPTH_MEDIUM = 30
```

### For Low-Volume Events (< 100 boats)

```python
# config.py adjustments

# More conservative timing
TRANSMISSION_DELAY_NORMAL = 3.0

# Smaller queue
MAX_QUEUE_SIZE = 500
```

## Production Deployment

### Create Systemd Services

**Start Line Service** (`/etc/systemd/system/rfid-meshtastic-start.service`):

```ini
[Unit]
Description=RFID Meshtastic Start Line Sender
After=network.target redis.target postgresql.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/user/rfidsystem/meshtastic_integration
ExecStart=/usr/bin/python3 start_line_sender.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Finish Line Service** (`/etc/systemd/system/rfid-meshtastic-finish.service`):

```ini
[Unit]
Description=RFID Meshtastic Finish Line Receiver
After=network.target redis.target postgresql.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/user/rfidsystem/meshtastic_integration
ExecStart=/usr/bin/python3 finish_line_receiver.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start**:

```bash
sudo systemctl daemon-reload
sudo systemctl enable rfid-meshtastic-start
sudo systemctl start rfid-meshtastic-start
sudo systemctl status rfid-meshtastic-start
```

## Monitoring

### View Logs

```bash
# Start line logs
sudo journalctl -u rfid-meshtastic-start -f

# Finish line logs
sudo journalctl -u rfid-meshtastic-finish -f
```

### Check Queue Status

```bash
# Queue depths
redis-cli << EOF
LLEN rfid:queue:start
LLEN rfid:queue:finish
LLEN rfid:queue:failed
EOF
```

### Check Database

```bash
# Count start messages received
psql -U postgres -d rfid_system -c "SELECT COUNT(*) FROM meshtastic_starts"

# View recent starts
psql -U postgres -d rfid_system -c "
  SELECT rfid, start_timestamp_h, station_id
  FROM meshtastic_starts
  ORDER BY received_at DESC
  LIMIT 10
"
```

## Safety Dashboard Integration

The finish line receiver creates a `meshtastic_starts` table that can be used by a safety dashboard:

```sql
-- Get RFIDs currently on water
SELECT
  ms.rfid,
  ms.start_timestamp,
  ms.start_timestamp_h,
  EXTRACT(EPOCH FROM (NOW() - ms.received_at)) as seconds_on_water
FROM meshtastic_starts ms
LEFT JOIN timeresults tr ON ms.rfid = tr.tag_id
WHERE tr.tag_id IS NULL  -- Not yet finished
ORDER BY ms.start_timestamp;

-- Get alerts (> 4 hours on water)
SELECT
  ms.rfid,
  ms.start_timestamp_h,
  EXTRACT(EPOCH FROM (NOW() - ms.received_at))/3600 as hours_on_water,
  CASE
    WHEN EXTRACT(EPOCH FROM (NOW() - ms.received_at)) > 28800 THEN 'CRITICAL'
    WHEN EXTRACT(EPOCH FROM (NOW() - ms.received_at)) > 21600 THEN 'RED'
    WHEN EXTRACT(EPOCH FROM (NOW() - ms.received_at)) > 14400 THEN 'YELLOW'
    ELSE 'NORMAL'
  END as alert_level
FROM meshtastic_starts ms
LEFT JOIN timeresults tr ON ms.rfid = tr.tag_id
WHERE tr.tag_id IS NULL
  AND EXTRACT(EPOCH FROM (NOW() - ms.received_at)) > 14400
ORDER BY hours_on_water DESC;
```

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
- Check the troubleshooting section
- Review logs with `sudo journalctl -u rfid-meshtastic-* -n 100`
- Verify all configuration parameters in `config.py`
