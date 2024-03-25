const express = require('express');
const axios = require('axios');
const path = require('path');
const { Pool } = require('pg');

// Initialize the Express application
const app = express();
const PORT = 3000; // Ensure this is different from your API's port

// PostgreSQL pool configuration
const pool = new Pool({
    user: 'postgres',
    host: 'localhost',
    database: 'rfid_system',
    password: 'r0ckkrush3r', // Make sure to set your password
    port: 5432,
});

// Set the view engine to ejs
app.set('view engine', 'ejs');

// Set the views directory
app.set('views', path.join(__dirname, 'views'));

// Use express.urlencoded middleware to parse URL-encoded form data
app.use(express.urlencoded({ extended: true }));

// Serve the index page with time data
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

// POST endpoint to handle form submission and insert data into DEMODATA
app.post('/insert-demo-data', async (req, res) => {
    const { fname, lname, district, age, team, bibnumber } = req.body;

    try {
        const result = await pool.query(
            'INSERT INTO DEMODATA (FName, LName, District, Age, Team, BibNumber) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *',
            [fname, lname, district, age, team, bibnumber]
        );
        // Redirect back to the home page or render a success message
        res.redirect('/');
    } catch (error) {
        console.error('Error inserting data:', error);
        res.status(500).send('Error inserting data');
    }
});

// Start the server
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
