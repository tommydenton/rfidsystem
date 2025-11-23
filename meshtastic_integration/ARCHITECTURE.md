# System Architecture

## Physical Layout

```
┌──────────────────────────────────────────┐
│    START LINE STATION (Monitoring Hub)   │
│                                          │
│  ┌────────────┐      ┌──────────────┐   │
│  │   RFID     │──USB─│ Raspberry Pi │   │
│  │   Reader   │      │              │   │
│  └────────────┘      │  PostgreSQL  │   │
│                      │  Python      │   │
│                      └───────┬──────┘   │
│                              │ USB      │
│                      ┌───────▼──────┐   │
│                      │  Heltec V3   │   │
│                      │  LoRa Radio  │   │
│                      │  (RECEIVES)  │   │
│                      └──────────────┘   │
│                                          │
│         Safety Dashboard Here            │
└──────────────────────────────────────────┘
                       ▲
                       │ LoRa Mesh
                       │ (FINISH msgs)
             ┌─────────┴─────────┐
             │  Relay Node 1     │
             │  (RAK WisMesh)    │
             └─────────┬─────────┘
                       │
                       ▼
             ┌──────────────────┐
             │  Relay Node 2-6  │
             │  (~1.5 mi apart) │
             └────────┬─────────┘
                      │
                      ▼
┌──────────────────────────────────────────┐
│   FINISH LINE STATION (Data Transmitter) │
│                                          │
│                      ┌──────────────┐   │
│                      │  Heltec V3   │   │
│                      │  LoRa Radio  │   │
│                      │  (SENDS)     │   │
│                      └───────┬──────┘   │
│                              │ USB      │
│  ┌────────────┐      ┌──────▼───────┐   │
│  │   RFID     │──USB─│ Raspberry Pi │   │
│  │   Reader   │      │              │   │
│  └────────────┘      │  PostgreSQL  │   │
│                      │  Redis       │   │
│                      │  Python      │   │
│                      └──────┬───────┘   │
│                             │ Internet  │
│                      ┌──────▼───────┐   │
│                      │   Starlink   │   │
│                      └──────────────┘   │
└──────────────────────────────────────────┘
```

## Software Architecture

### Start Line Station (Monitoring Hub)

```
┌──────────────────────────────────────────────────────┐
│            start_line_monitor.py                     │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  Monitor Local RFID JSON File              │    │
│  │  (/var/www/html/timer/uploads/...)         │    │
│  │  • Read START times from local reader      │    │
│  └────────────────┬───────────────────────────┘    │
│                   │                                  │
│                   ▼                                  │
│  ┌────────────────────────────────────────────┐    │
│  │  DepartureTracker                          │    │
│  │  • Record each RFID read                   │    │
│  │  • Track last seen time                    │    │
│  │  • Wait DEPARTURE_WAIT_TIME (5 min)        │    │
│  │  • Confirm departure (local only)          │    │
│  │  • Save to PostgreSQL (timeresults)        │    │
│  └────────────────┬───────────────────────────┘    │
│                   │                                  │
│                   ▼                                  │
│       [No transmission - local tracking only]       │
│                                                      │
│           ┌──────────────────────────┐              │
│           │  MeshtasticInterface     │              │
│           │  • RECEIVE mode          │              │
│           │  • Listen for FINISH msg │              │
│           └──────────┬───────────────┘              │
│                      │                               │
│                      ▼                               │
│  ┌────────────────────────────────────────────┐    │
│  │  OnWaterTracker                            │    │
│  │  • Match START (local) with FINISH (rcvd)  │    │
│  │  • Track RFIDs on water                    │    │
│  │  • Calculate time on water                 │    │
│  │  • Generate safety alerts                  │    │
│  └────────────────┬───────────────────────────┘    │
│                   │                                  │
│                   ▼                                  │
│  ┌────────────────────────────────────────────┐    │
│  │  PostgreSQL Database                       │    │
│  │  • timeresults (local STARTs)              │    │
│  │  • meshtastic_finishes (received)          │    │
│  └────────────────┬───────────────────────────┘    │
│                   │                                  │
└───────────────────┼──────────────────────────────────┘
                    │
                    ▼
         [Safety Dashboard Queries]
                    ▲
                    │ LoRa Mesh (receives FINISH)
```

### Finish Line Station (Data Transmitter)

```
┌──────────────────────────────────────────────────────┐
│            finish_line_sender.py                     │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  Monitor Local RFID JSON File              │    │
│  │  (/var/www/html/timer/uploads/...)         │    │
│  │  • Read FINISH times from local reader     │    │
│  └────────────────┬───────────────────────────┘    │
│                   │                                  │
│                   ▼                                  │
│  ┌────────────────────────────────────────────┐    │
│  │  FinishTracker                             │    │
│  │  • Record each RFID finish                 │    │
│  │  • Dwell time check (prevent duplicates)   │    │
│  │  • Save to PostgreSQL (timeresults)        │    │
│  └────────────────┬───────────────────────────┘    │
│                   │                                  │
│                   ▼                                  │
│  ┌────────────────────────────────────────────┐    │
│  │  RedisQueue                                │    │
│  │  • Enqueue FINISH messages                 │    │
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
│  │  • SEND mode                               │    │
│  │  • Transmit FINISH messages                │    │
│  │  • Retry on failure                        │    │
│  └────────────────┬───────────────────────────┘    │
│                   │                                  │
└───────────────────┼──────────────────────────────────┘
                    │
                    ▼
           [LoRa Mesh Network]
```

## Message Flow

### Normal Flow (Single RFID)

```
Time   Event
─────  ────────────────────────────────────────────────
08:15  Paddler enters start area with RFID
08:15  START LINE: RFID Reader detects tag → Write to JSON
08:15  START LINE: start_line_monitor reads JSON
08:15  START LINE: DepartureTracker records RFID (first_seen: 08:15)
08:16  START LINE: RFID detected again (last_seen: 08:16)
08:17  START LINE: RFID detected again (last_seen: 08:17)
08:18  START LINE: Paddler leaves start area (no more reads)
08:23  START LINE: 5 minutes elapsed since last_seen (08:18)
08:23  START LINE: DepartureTracker confirms departure
08:23  START LINE: Saved to timeresults table (local only)
08:23  START LINE: RFID now tracked as "on water"
       ... paddler travels down river ...
14:22  FINISH LINE: RFID detected at finish
14:22  FINISH LINE: Saved to timeresults table (local)
14:22  FINISH LINE: Message queued to Redis
14:22  FINISH LINE: Queue depth: 1, delay: 3 seconds
14:22  FINISH LINE: FINISH message sent via Meshtastic
14:22  LoRa transmission (~1-2 seconds)
14:23  Relay nodes forward message back to start
14:25  START LINE: Receives FINISH message
14:25  START LINE: OnWaterTracker matches with local START
14:25  START LINE: Calculates duration: 6.03 hours
14:25  START LINE: Database updated (meshtastic_finishes)
14:25  START LINE: RFID removed from "on water" tracking
```

### Burst Flow (30 RFIDs)

```
Time   Event
─────  ────────────────────────────────────────────────
08:00  30 paddlers stage in start area
08:00  START LINE: All 30 RFIDs detected repeatedly
08:05  Race starts, all 30 paddlers depart
08:05  START LINE: Last RFID reads at ~08:05:20
08:10  START LINE: 5 minutes elapsed for all RFIDs
08:10  START LINE: All 30 departures confirmed simultaneously
08:10  START LINE: All saved to local database
08:10  START LINE: Dashboard shows 30 RFIDs on water
       ... paddlers travel down river ...
14:20  FINISH LINE: First finisher arrives
14:20  FINISH LINE: RFIDs start arriving rapidly
14:35  FINISH LINE: 30 RFIDs detected in ~15 minutes
14:35  FINISH LINE: All 30 FINISH messages queued to Redis (< 1 second)
14:35  FINISH LINE: Queue depth: 30, switch to fast mode (2 sec/msg)
14:35  FINISH LINE: Start transmitting messages
14:36  FINISH LINE: Queue depth: 25 (5 transmitted)
14:36  FINISH LINE: Still in fast mode
14:37  FINISH LINE: Queue depth: 15 (15 transmitted)
14:37  FINISH LINE: Queue depth < 20, switch to medium (2.5 sec)
14:38  FINISH LINE: Queue depth: 5 (25 transmitted)
14:38  FINISH LINE: Queue depth < 20, use normal delay (3 sec)
14:39  FINISH LINE: Queue empty (all 30 transmitted)
14:39  Total time: ~90 seconds for 30 messages
14:39  START LINE: All messages received via LoRa mesh
14:39  START LINE: Dashboard updated - 0 RFIDs on water
```

## Data Structures

### Message Format (JSON via Meshtastic)

```json
{
  "rfid": "2302",
  "timestamp": 1696162123.456,
  "timestamp_h": "2025-10-01 14:22:03.456",
  "message_type": "FINISH",
  "station_id": "FINISH_LINE_1",
  "priority": "normal",
  "tag_type": "E2001234567890AB",
  "tag_position": "A001",
  "queue_time": "2025-10-01T14:22:03Z",
  "sent_at": "2025-10-01T14:22:05Z",
  "sent_by": "FINISH_LINE_1"
}
```

### Database Tables

#### meshtastic_finishes (Start Line)
```sql
CREATE TABLE meshtastic_finishes (
    id SERIAL PRIMARY KEY,
    rfid VARCHAR(255) NOT NULL,
    finish_timestamp DOUBLE PRECISION,
    finish_timestamp_h VARCHAR(255),
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
