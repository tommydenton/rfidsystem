// Importing modules using ES module syntax
import express from 'express';
import { getNetworkTime } from 'ntp-client';

const app = express();
const PORT = 3001;
const TIME_SERVER = 'time.cloudflare.com';
const TIME_SERVER_PORT = 123;

app.get('/time', (req, res) => {
  getNetworkTime(TIME_SERVER, TIME_SERVER_PORT, (err, date) => {
    if (err) {
      console.error(err);
      return res.status(500).json({ error: 'Error fetching NTP time' });
    }

    const ntpTime = date.toISOString();
    const localTime = new Date().toISOString();

    // Send the NTP time and local system time in JSON format
    res.json({
      ntpTime: ntpTime,
      localTime: localTime
    });
  });
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
