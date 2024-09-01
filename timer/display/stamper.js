const { SerialPort } = require('serialport');
const { EventEmitter } = require('events');
const { Pool } = require('pg');

const SERIAL_PORT0 = '/dev/ttyUSB0';
const SERIAL_PORT1 = '/dev/ttyUSB1';
const BAUD_RATE = 57600;

const port0 = new SerialPort({
  path: SERIAL_PORT0,
  baudRate: BAUD_RATE
});

const port1 = new SerialPort({
  path: SERIAL_PORT1,
  baudRate: BAUD_RATE
});

// PostgreSQL pool configuration
const pool = new Pool({
  user: 'postgres',
  host: 'localhost',
  database: 'rfid_system',
  password: 'r0ckkrush3r',
  port: 5432,
});

const rfidEmitter = new EventEmitter();

const handlePortData = (portName) => (data) => {
  const hexData = data.toString('hex').toUpperCase();
 
  // Assuming the RFID data format follows the structure in the Python script
  const tagType = hexData.substring(0, 14);
  const tagId = hexData.substring(14, hexData.length - 4);
  const tagPosition = hexData.substring(hexData.length - 4);
  const formattedData = `${tagType}-${tagId}-${tagPosition}`;

  const timestamp = new Date().toISOString();
  console.log(`RFID Tag ID: ${portName}-${tagId} at ${timestamp}`);
  rfidEmitter.emit('tagScanned', formattedData);

  // Insert the data into the database
  // pool.query(
  //   'INSERT INTO LINKER (tag_type, tag_id, tag_position, rfidtag, timestamp) VALUES ($1, $2, $3, $4, $5)',
  //   [tagType, tagId, tagPosition, formattedData, timestamp],
  //   (err, res) => {
  //     if (err) {
  //       console.error('Error inserting data into database:', err);
  //     } else {
  //       console.log('Data inserted into database successfully');
  //     }
  //   }
  // );
};

const setupPort = (port, portName) => {
  port.on('open', () => {
    console.log(`Serial ${portName} opened`);
  });

  port.on('error', (err) => {
    console.log('Error:', err.message);
  });

  port.on('data', handlePortData(portName));
};

setupPort(port0, 'port0');
setupPort(port1, 'port1');

module.exports = rfidEmitter;