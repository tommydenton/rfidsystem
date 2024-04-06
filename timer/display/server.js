// server.ejs
const express = require('express');
const axios = require('axios');
const path = require('path');
const {
    Pool
} = require('pg');

// Initialize the Express application
const app = express();
const PORT = 3000;

// PostgreSQL pool configuration
const pool = new Pool({
    user: 'postgres',
    host: 'localhost',
    database: 'rfid_system',
    password: 'r0ckkrush3r',
    port: 5432,
});

// Breadcrumb middleware
app.use((req, res, next) => {
    res.locals.breadcrumbPath = [{
            text: 'Home',
            href: '/display'
        },
        {
            text: 'Time Display',
            href: '/time'
        },
        {
            text: 'Data Entry',
            href: '/dataentry'
        },
        // Add or remove breadcrumb items as needed
    ];
    next();
});

// Set the view engine to EJS and the views directory
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Serve static files from the 'public' directory
app.use(express.static(path.join(__dirname, 'public')));

// Parse URL-encoded bodies (as sent by HTML forms)
app.use(express.urlencoded({
    extended: true
}));

// Route for the homepage
app.get('/display', (req, res) => {
    res.render('index');
});

// Route for the data entry form
app.get('/dataentry', async (req, res) => {
    try {
        const result = await pool.query('SELECT * FROM DEMODATA');
        res.render('dataentry', {
            demoData: result.rows
        });
    } catch (error) {
        console.error('Error fetching data:', error);
        res.render('dataentry', {
            demoData: []
        });
    }
});

// Route for inserting data into the database
app.post('/insert-demo-data', async (req, res) => {
    const {
        fname,
        lname,
        gender,
        age,
        council,
        district,
        unittype,
        unitnumber,
        race,
        boat,
        bibnumber
    } = req.body;
    try {
        // Check if bibnumber already exists
        const checkResult = await pool.query(
            'SELECT * FROM DEMODATA WHERE BibNumber = $1',
            [bibnumber]
        );
        if (checkResult.rows.length > 0) {
            // BibNumber already exists, handle accordingly
            return res.status(400).send('BibNumber already exists. Please use a unique BibNumber.');
        }

        // Proceed with insertion if bibnumber is unique
        const insertResult = await pool.query(
            'INSERT INTO DEMODATA (fname, lname, gender, age, council, district, unittype, unitnumber, race, boat, bibnumber) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11) RETURNING *',
            [fname, lname, gender, age, council, district, unittype, unitnumber, race, boat, bibnumber]
        );
        res.redirect('/dataentry');
    } catch (error) {
        console.error('Error inserting data:', error);
        res.status(500).send('Error inserting data');
    }
});

// Route for displaying the edit form
app.get('/editdata', async (req, res) => {
    const {
        uid
    } = req.query; // Get the UID from the query parameter

    try {
        const result = await pool.query('SELECT * FROM DEMODATA WHERE uid = $1', [uid]);
        if (result.rows.length > 0) {
            // Render an edit form with the data pre-populated
            res.render('editdata', {
                rowData: result.rows[0]
            });
        } else {
            res.send('Row not found');
        }
    } catch (error) {
        console.error('Error fetching row:', error);
        res.status(500).send('Error fetching row');
    }
});

// Route for updating data in the database
app.post('/update-demo-data', async (req, res) => {
    const {
        uid,
        fname,
        lname,
        gender,
        age,
        council,
        district,
        unittype,
        unitnumber,
        race,
        boat,
        bibnumber
    } = req.body;

    try {
        await pool.query(
            'UPDATE DEMODATA SET fname = $1, lname = $2, gender = $3, age = $4, council = $5, district = $6, unittype = $7, unitnumber = $8, race = $9, boat = $10, bibnumber = $11 WHERE uid = $12',
            [fname, lname, gender, age, council, district, unittype, unitnumber, race, boat, bibnumber, uid]
        );
        res.redirect('/dataentry');
    } catch (error) {
        console.error('Error updating data:', error);
        res.status(500).send('Error updating data');
    }
});

// Start the server
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});

//Info APIs
// Route for displaying time
app.get('/time', async (req, res) => {
    try {
        const response = await axios.get('http://localhost:3001/time');
        const cloudTime = response.data.ntpTime;
        const localTime = new Date().toISOString();
        res.render('time', {
            cloudTime,
            localTime
        });
    } catch (error) {
        console.error('Error fetching time data:', error);
        res.send('Error fetching time data');
    }
});