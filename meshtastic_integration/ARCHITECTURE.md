# System Architecture

## Physical Layout

```
┌─────────────────────────────────────────┐
│         START LINE STATION              │
│                                         │
│  ┌────────────┐      ┌──────────────┐  │
│  │   RFID     │──USB─│ Raspberry Pi │  │
│  │   Reader   │      │              │  │
│  └────────────┘      │  PostgreSQL  │  │
│                      │  Redis       │  │
│                      │  Python      │  │
│                      └───────┬──────┘  │
│                              │ USB     │
│                      ┌───────▼──────┐  │
│                      │  Heltec V3   │  │
│                      │  LoRa Radio  │  │
│                      └──────────────┘  │
└─────────────────────────────────────────┘
                       │
                       │ LoRa Mesh
                       ▼
             ┌──────────────────┐
             │  Relay Node 1    │
             │  (RAK WisMesh)   │
             └────────┬─────────┘
                      │
                      ▼
             ┌──────────────────┐
             │  Relay Node 2-6  │
             │  (~1.5 mi apart) │
             └────────┬─────────┘
                      │
                      ▼
┌─────────────────────────────────────────┐
│        FINISH LINE STATION              │
│                                         │
│                      ┌──────────────┐  │
│                      │  Heltec V3   │  │
│                      │  LoRa Radio  │  │
│                      └───────┬──────┘  │
│                              │ USB     │
│  ┌────────────┐      ┌──────▼───────┐  │
│  │   RFID     │──USB─│ Raspberry Pi │  │
│  │   Reader   │      │              │  │
│  └────────────┘      │  PostgreSQL  │  │
│                      │  Python      │  │
│                      └──────┬───────┘  │
│                             │ Internet │
└─────────────────────────────┼──────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │ Safety Dashboard│
                     │   at Race HQ    │
                     └─────────────────┘
```

## Software Architecture

### Start Line Station

```
┌──────────────────────────────────────────────────────┐
│            start_line_sender.py                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  Monitor RFID JSON File                    │    │
│  │  (/var/www/html/timer/uploads/...)         │    │
│  └────────────────┬───────────────────────────┘    │
│                   │                                  │
│                   ▼                                  │
│  ┌────────────────────────────────────────────┐    │
│  │  DepartureTracker                          │    │
│  │  • Record each RFID read                   │    │
│  │  • Track last seen time                    │    │
│  │  • Wait DEPARTURE_WAIT_TIME (5 min)        │    │
│  │  • Confirm if not re-read                  │    │
│  └────────────────┬───────────────────────────┘    │
│                   │                                  │
│                   ▼                                  │
│  ┌────────────────────────────────────────────┐    │
│  │  RedisQueue                                │    │
│  │  • Enqueue confirmed departures            │    │
│  │  • Persist messages                        │    │
│  │  • Handle bursts (30+ RFIDs)               │    │
│  └────────────────┬───────────────────────────┘    │
│                   │                                  │
│                   ▼                                  │
│  ┌────────────────────────────────────────────┐    │
│  │  RateLimitedQueueProcessor                 │    │
│  │  • Dequeue messages                        │    │
│  │  • Adaptive delay (2-3 sec)                │    │
│  │  • Fast mode if queue > 50                 │    │
│  └────────────────┬───────────────────────────┘    │
│                   │                                  │
│                   ▼                                  │
│  ┌────────────────────────────────────────────┐    │
│  │  MeshtasticInterface                       │    │
│  │  • Send JSON message                       │    │
│  │  • Retry on failure                        │    │
│  │  • Log transmission                        │    │
│  └────────────────┬───────────────────────────┘    │
│                   │                                  │
└───────────────────┼──────────────────────────────────┘
                    │
                    ▼
           [LoRa Mesh Network]
```

### Finish Line Station

```
           [LoRa Mesh Network]
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│           finish_line_receiver.py                    │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  MeshtasticInterface                       │    │
│  │  • Receive messages                        │    │
│  │  • Parse JSON                              │    │
│  │  • Extract RFID + timestamp                │    │
│  └────────────────┬───────────────────────────┘    │
│                   │                                  │
│                   ▼                                  │
│  ┌────────────────────────────────────────────┐    │
│  │  OnWaterTracker                            │    │
│  │  • Record START messages                   │    │
│  │  • Track RFIDs on water                    │    │
│  │  • Calculate time on water                 │    │
│  │  • Generate alerts                         │    │
│  └────────────────┬───────────────────────────┘    │
│                   │                                  │
│                   ▼                                  │
│  ┌────────────────────────────────────────────┐    │
│  │  PostgreSQL Database                       │    │
│  │  • meshtastic_starts table                 │    │
│  │  • Store start messages                    │    │
│  │  • Link with finish reads                  │    │
│  └────────────────┬───────────────────────────┘    │
│                   │                                  │
│  ┌────────────────▼───────────────────────────┐    │
│  │  Monitor Local RFID Reads                  │    │
│  │  • timeresults table                       │    │
│  │  • Match RFIDs                             │    │
│  │  • Calculate durations                     │    │
│  │  • Remove from "on water"                  │    │
│  └────────────────┬───────────────────────────┘    │
│                   │                                  │
└───────────────────┼──────────────────────────────────┘
                    │
                    ▼
         [Safety Dashboard Queries]
```

## Message Flow

### Normal Flow (Single RFID)

```
Time   Event
─────  ────────────────────────────────────────────────
08:15  Paddler enters start area with RFID
08:15  RFID Reader detects tag → Write to JSON
08:15  start_line_sender reads JSON
08:15  DepartureTracker records RFID (first_seen: 08:15)
08:16  RFID detected again (last_seen: 08:16)
08:17  RFID detected again (last_seen: 08:17)
08:18  Paddler leaves start area (no more reads)
08:23  5 minutes elapsed since last_seen (08:18)
08:23  DepartureTracker confirms departure
08:23  Message queued to Redis
08:23  Queue depth: 1, delay: 3 seconds
08:23  Message sent via Meshtastic
08:23  LoRa transmission (~1-2 seconds)
08:24  Relay nodes forward message
08:25  Finish line receives message
08:25  OnWaterTracker records start
08:25  Database updated (meshtastic_starts)
```

### Burst Flow (30 RFIDs)

```
Time   Event
─────  ────────────────────────────────────────────────
08:00  30 paddlers stage in start area
08:00  All 30 RFIDs detected repeatedly
08:05  Race starts, all 30 paddlers depart
08:05  Last RFID reads at ~08:05:20
08:10  5 minutes elapsed for all RFIDs
08:10  All 30 departures confirmed simultaneously
08:10  All 30 messages queued to Redis (< 1 second)
08:10  Queue depth: 30, switch to fast mode (2 sec/msg)
08:10  Start transmitting messages
08:11  Queue depth: 25 (5 transmitted)
08:11  Still in fast mode
08:12  Queue depth: 15 (15 transmitted)
08:12  Queue depth < 20, switch to medium (2.5 sec)
08:13  Queue depth: 5 (25 transmitted)
08:13  Queue depth < 20, use normal delay (3 sec)
08:14  Queue empty (all 30 transmitted)
08:14  Total time: ~90 seconds for 30 messages
08:14  All messages received at finish line
08:14  Dashboard shows 30 RFIDs on water
```

## Data Structures

### Message Format (JSON via Meshtastic)

```json
{
  "rfid": "2302",
  "timestamp": 1696155323.456,
  "timestamp_h": "2025-10-01 08:15:23.456",
  "last_seen": 1696155383.789,
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

### Database Tables

#### meshtastic_starts (Finish Line)
```sql
CREATE TABLE meshtastic_starts (
    id SERIAL PRIMARY KEY,
    rfid VARCHAR(255) NOT NULL,
    start_timestamp DOUBLE PRECISION,
    start_timestamp_h VARCHAR(255),
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    station_id VARCHAR(255),
    tag_type VARCHAR(255),
    tag_position VARCHAR(255),
    message_data JSONB
);
```

#### timeresults (Both Stations - Existing)
```sql
CREATE TABLE timeresults (
    id SERIAL PRIMARY KEY,
    tag_type VARCHAR(255),
    tag_id VARCHAR(255),
    tag_position VARCHAR(255),
    timestamp DOUBLE PRECISION,
    timestamp_h VARCHAR(255)
);
```

## Configuration Hierarchy

```
Environment Variables
         ↓
    config.py
         ↓
   ┌──────┴──────┬──────────┬──────────┐
   ▼             ▼          ▼          ▼
Redis      Meshtastic   Database   Timing
Queue      Interface    Connector  Parameters
```

## Error Handling

```
Message Send Error
       ↓
   Retry (3x)
       ↓
   Still Failed?
       ↓
Move to REDIS_QUEUE_FAILED
       ↓
Log Error + Reason
       ↓
Continue Processing Queue
```

## Monitoring Points

1. **Queue Health**
   - Depth (messages waiting)
   - Oldest message age
   - Failed messages count

2. **Meshtastic Health**
   - Connection status
   - Messages sent/received
   - Last message time

3. **Database Health**
   - Connection status
   - Query response time

4. **Safety Metrics**
   - RFIDs on water
   - Alert counts (yellow/red/critical)
   - Longest time on water

## Performance Characteristics

### Capacity

- **Normal**: 30-50 boats/hour = 40-80 messages/hour
- **Peak**: 75 boats/hour = 160-190 messages/hour
- **Theoretical Max**: 1,200-1,800 messages/hour
- **Load**: 5-10% of capacity

### Latency

- **RFID Read to Queue**: < 1 second
- **Queue to Transmission**: 2-3 seconds (adaptive)
- **Transmission**: 1-2 seconds
- **Relay Hops**: ~0.5 seconds each (6 hops = 3 sec)
- **Total**: 6-9 seconds typical
- **Burst Delay**: +60-90 seconds max

### Reliability

- **Expected Message Success**: 90-95%
- **Acceptable Minimum**: 85%
- **Fallback**: Local database has 100% record
