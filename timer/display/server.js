const express = require('express');
const axios = require('axios');
const path = require('path'); // Import the path module
const app = express();
const PORT = 3000; // Ensure this is different from your API's port

app.set('view engine', 'ejs');

// If your server.js file is located in /var/www/rfidsystem/timer/display, this line is correct
// If server.js is located elsewhere, you'll need to adjust the path accordingly
app.set('views', path.join(__dirname, 'views'));

app.get('/', async (req, res) => {
  try {
    const response = await axios.get('http://192.168.1.22:3001/time');
    const cloudTime = response.data.ntpTime;
    const localTime = new Date().toISOString();

    // Render the index.ejs template with the cloudTime and localTime variables
    res.render('index', { cloudTime, localTime });
  } catch (error) {
    console.error('Error fetching time data:', error);
    res.send('Error fetching time data');
  }
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
