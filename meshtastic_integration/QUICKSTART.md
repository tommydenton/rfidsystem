# Quick Start Guide

## Installation (5 minutes)

```bash
# 1. Install Redis
sudo apt install redis-server
sudo systemctl start redis-server

# 2. Install Python dependencies
cd /home/user/rfidsystem/meshtastic_integration
pip3 install -r requirements.txt

# 3. Run tests
python3 example_test.py
```

## Configuration (2 minutes)

Edit `config.py` and set:

```python
# REQUIRED SETTINGS
STATION_TYPE = 'START'  # or 'FINISH'
STATION_ID = 'START_LINE_1'
MESHTASTIC_SERIAL_PORT = '/dev/ttyUSB2'  # Find with: ls /dev/ttyUSB*

# DATABASE
DB_NAME = 'rfid_system'
DB_USER = 'postgres'
DB_PASSWORD = 'your_password'
```

## Running (1 minute)

### Start Line Station
```bash
python3 start_line_sender.py
```

### Finish Line Station
```bash
python3 finish_line_receiver.py
```

### Monitor Queue
```bash
python3 queue_monitor.py
```

## Key Features

| Feature | Configuration | Default |
|---------|--------------|---------|
| 5-minute wait | `DEPARTURE_WAIT_TIME` | 300 seconds |
| Normal message spacing | `TRANSMISSION_DELAY_NORMAL` | 3.0 seconds |
| Queue warning threshold | `QUEUE_ALERT_WARNING` | 50 messages |
| Yellow alert (time on water) | `ALERT_YELLOW_THRESHOLD` | 4 hours |
| Red alert (time on water) | `ALERT_RED_THRESHOLD` | 6 hours |

## Testing Without Hardware

Set in `config.py`:
```python
SIMULATE_MESSAGES = True
DRY_RUN = True
```

Then run:
```bash
python3 example_test.py
```

## Troubleshooting

### Can't connect to Redis
```bash
sudo systemctl status redis-server
redis-cli ping  # Should return PONG
```

### Can't connect to Meshtastic
```bash
ls -l /dev/ttyUSB*  # Find your device
sudo usermod -a -G dialout $USER  # Add permissions
# Log out and back in
```

### Database connection error
```bash
psql -h localhost -U postgres -d rfid_system -c "SELECT 1"
```

## Message Flow

```
RFID Read
    ↓
5-Minute Wait
    ↓
Redis Queue
    ↓
Rate Limiter (2-3 sec/msg)
    ↓
Meshtastic LoRa
    ↓
Relay Nodes
    ↓
Finish Line Receiver
    ↓
Database + Dashboard
```

## Queue Behavior

| Queue Depth | Delay Between Messages |
|-------------|----------------------|
| 0-20 | 3.0 seconds (normal) |
| 21-50 | 2.5 seconds (medium) |
| 51+ | 2.0 seconds (fast) |

**Burst Handling**: 30 RFIDs in 20 seconds → 60-90 seconds to transmit all

## Safety Alerts

| Time on Water | Alert Level | Color |
|---------------|-------------|-------|
| < 4 hours | Normal | - |
| 4-6 hours | Yellow | ⚠ |
| 6-8 hours | Red | 🚨 |
| > 8 hours | Critical | 🆘 |

## Production Deployment

```bash
# Create systemd service
sudo cp rfid-meshtastic-start.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rfid-meshtastic-start
sudo systemctl start rfid-meshtastic-start

# View logs
sudo journalctl -u rfid-meshtastic-start -f
```

## Files Reference

| File | Purpose |
|------|---------|
| `config.py` | All tunable parameters |
| `start_line_sender.py` | Start line operations |
| `finish_line_receiver.py` | Finish line operations |
| `redis_queue.py` | Queue management |
| `meshtastic_interface.py` | LoRa communication |
| `queue_monitor.py` | Health monitoring |
| `example_test.py` | Test suite |

## Support

See `README.md` for detailed documentation.
