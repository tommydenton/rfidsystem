const ntp = require('ntp-client');
const server = 'pool.ntp.org';
const callback = function(err, time) {
  if (err) {
    console.log('Error: ' + err);
  } else {
    console.log('Time: ' + time);
  }
};
ntp.getNetworkTime(server, callback);

const express = require('express');
const app = express();
const port = 3000;

app.get('/time', (req, res) => {
  ntp.getNetworkTime(server, (err, time) => {
    if (err) {
      res.status(500).send('Error: ' + err);
    } else {
      res.send('Time: ' + time);
    }
  });
});

app.listen(port, () => {
  console.log(`Time API listening at http://localhost:${port}`);
});
