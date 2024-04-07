const { SerialPort } = require('serialport');

const SERIAL_PORT = '/dev/ttyUSB0';
const BAUD_RATE = 57600;

const port = new SerialPort({
  path: SERIAL_PORT,
  baudRate: BAUD_RATE
});

port.on('open', () => {
  console.log('Serial port opened');
});

port.on('error', (err) => {
  console.log('Error:', err.message);
});

port.on('data', (data) => {
  const hexData = data.toString('hex').toUpperCase();
  console.log(`Raw RFID Tag Data: ${hexData}`);
  
  // Assuming the RFID data format follows the structure in the Python script
  const tagType = hexData.substring(0, 14);
  const tagId = hexData.substring(14, hexData.length - 4);
  const tagPosition = hexData.substring(hexData.length - 4);
  const formattedData = `${tagType}-${tagId}-${tagPosition}`;
  
  console.log(`Formatted RFID Tag Data: ${formattedData}`);
});