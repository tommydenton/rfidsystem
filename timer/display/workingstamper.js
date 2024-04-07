const { SerialPort } = require('serialport');

const port = new SerialPort({
  path: '/dev/ttyUSB0',
  baudRate: 57600
});

port.on('open', function() {
  console.log('Serial port opened');
});

port.on('data', function(data) {
  console.log('Data:', data.toString());
});