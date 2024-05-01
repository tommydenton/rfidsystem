import serial
import binascii
import time
import json
import os
from datetime import datetime
import threading

# Configuration
SERIAL_PORTS = ['/dev/ttyUSB0', '/dev/ttyUSB1']
BAUD_RATE = 57600
DWELL_TIME = 2  # Dwell time in seconds, configurable
OUTPUT_DIR = '/var/www/html/timer/uploads/'  # Configurable output directory
OUTPUT_FILE = 'rfid_output.json'  # Configurable output file name

def setup_serial_connection(port, baud_rate):
    try:
        return serial.Serial(port, baud_rate, timeout=1)
    except Exception as e:
        print(f"Failed to establish serial connection on {port}: {e}")
        return None

def parse_tag_data(hex_data):
    tags = []
    for i in range(0, len(hex_data), 38):
        chunk = hex_data[i:i+38]
        if len(chunk) == 38:
            tags.append(chunk)
    return tags

def read_rfid_tag(ser, last_seen_tags, port):
    try:
        data = ser.read(100)
        if data:
            hex_data = binascii.hexlify(data).decode('ascii').upper()
            tags = parse_tag_data(hex_data)
            valid_tags = []
            for tag in tags:
                tag_type = tag[:14]
                tag_id = tag[14:-4]
                tag_position = tag[-4:]
                timestamp = time.time()
                formatted_data = {
                    "tag_type": tag_type,
                    "tag_id": tag_id,
                    "tag_position": tag_position,
                    "timestamp": timestamp,
                    "timestamp_h": datetime.fromtimestamp(timestamp).strftime('%m-%d-%Y|%H:%M:%S:%f')[:-3]
                }
                current_time = time.time()
                if tag_id not in last_seen_tags or (current_time - last_seen_tags[tag_id] > DWELL_TIME):
                    last_seen_tags[tag_id] = current_time
                    valid_tags.append(formatted_data)
            return valid_tags
        else:
            return None
    except Exception as e:
        print(f"Error reading RFID data from {port}: {e}")
        return None

def write_to_json(data, directory, filename):
    if data:
        filepath = os.path.join(directory, filename)
        with open(filepath, 'a') as f:  # Change to 'w' to overwrite each time
            json.dump(data, f, indent=4)  # Use json.dump to write the entire list

def monitor_rfid_reader(port):
    print(f"Starting RFID reader on {port}...")
    ser = setup_serial_connection(port, BAUD_RATE)
    last_seen_tags = {}
    
    if ser is not None:
        try:
            while True:
                formatted_tag_data = read_rfid_tag(ser, last_seen_tags, port)
                if formatted_tag_data:
                    for tag_data in formatted_tag_data:
                        print(f"RFID Tag Data from {port}: {tag_data}")
                        write_to_json(tag_data, OUTPUT_DIR, OUTPUT_FILE)
                time.sleep(0.1)
        except KeyboardInterrupt:
            print(f"Stopping RFID reader on {port}...")
        finally:
            ser.close()
    else:
        print(f"Serial connection on {port} could not be established.")

if __name__ == "__main__":
    threads = []
    for port in SERIAL_PORTS:
        thread = threading.Thread(target=monitor_rfid_reader, args=(port,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()