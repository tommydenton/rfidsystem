import serial
import binascii
import time

# Configure the serial port based on your RFID reader's configuration
SERIAL_PORT = '/dev/ttyS0'
BAUD_RATE = 57600
DWELL_TIME = 1  # Dwell time in seconds, configurable

def setup_serial_connection(port, baud_rate):
    try:
        return serial.Serial(port, baud_rate, timeout=1)
    except Exception as e:
        print(f"Failed to establish serial connection: {e}")
        return None

def read_rfid_tag(ser, last_seen_tags):
    try:
        data = ser.read(100)  # Adjust the byte size as needed
        if data:
            hex_data = binascii.hexlify(data).decode('ascii').upper()
            # Extract the tag type, ID, and position from the hex_data
            tag_type = hex_data[:14]  # First 14 characters are the tag type
            tag_id = hex_data[14:-4]  # The actual ID of the tag
            tag_position = hex_data[-4:]  # Last 4 characters are the position
            formatted_data = f"{tag_type}-{tag_id}-{tag_position}"
            
            current_time = time.time()
            # Check if the tag has been seen recently
            if tag_id not in last_seen_tags or (current_time - last_seen_tags[tag_id] > DWELL_TIME):
                last_seen_tags[tag_id] = current_time
                return formatted_data
            else:
                return "Tag seen recently, ignoring due to dwell time."
        else:
            return None
    except Exception as e:
        print(f"Error reading RFID data: {e}")
        return None

if __name__ == "__main__":
    print("Starting RFID reader...")
    ser = setup_serial_connection(SERIAL_PORT, BAUD_RATE)
    last_seen_tags = {}  # Dictionary to store the last seen time for each tag
    
    if ser is not None:
        try:
            while True:
                formatted_tag_data = read_rfid_tag(ser, last_seen_tags)
                if formatted_tag_data and "Tag seen recently" not in formatted_tag_data:
                    print(f"RFID Tag Data: {formatted_tag_data}")
                time.sleep(0.1)  # Adjust the sleep time as needed
        except KeyboardInterrupt:
            print("Stopping RFID reader...")
        finally:
            ser.close()
    else:
        print("Serial connection could not be established.")
