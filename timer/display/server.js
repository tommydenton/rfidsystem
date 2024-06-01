// server.js
const express = require('express');
const morgan = require('morgan');
const axios = require('axios');
const path = require('path');
const moment = require('moment');
const multer = require('multer');
const session = require('express-session');
const flash = require('connect-flash');
const WebSocket = require('ws');
const wss = new WebSocket.Server({
    noServer: true
});
const fs = require('fs');
const util = require('util');
const readdir = util.promisify(fs.readdir);
const rfidEmitter = require('./stamper.js');
const {
    Pool
} = require('pg');
const uploadsDirectory = path.join(__dirname, '..', 'uploads');

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

// Set the view engine to EJS and the views directory
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Set the time backend for each view
app.locals.moment = moment;

// Serve static files from the 'public' directory
app.use(express.static(path.join(__dirname, 'public')));

// Parse URL-encoded bodies (as sent by HTML forms)
app.use(express.urlencoded({
    extended: true
}));

// Session
app.use(session({
    secret: 'rfidcookies',
    resave: false,
    saveUninitialized: true,
    cookie: {
        secure: true
    }
}));

// Flash Messages
app.use(flash());

// Async/Await Error Handling
require('express-async-errors');

// Logging with Morgan Middleware
app.use(morgan('tiny', {
    skip: function(req, res) {
        return res.statusCode < 400
    }
}));

// Compression Middleware
const compression = require('compression');
app.use(compression());

// Multer Middleware
const storage = multer.diskStorage({
    destination: function(req, file, cb) {
        cb(null, uploadsDirectory)
    },
    filename: function(req, file, cb) {
        const originalName = path.parse(file.originalname).name;
        const extension = path.parse(file.originalname).ext;
        const timestamp = Date.now();
        cb(null, `${originalName}-${timestamp}${extension}`);
    }
});

const upload = multer({
    storage: storage
});

// Define the fetchTimeData middleware
async function fetchTimeData(req, res, next) {
    try {
        const response = await axios.get('http://localhost:3001/time');
        const cloudTime = response.data.ntpTime;
        const localTime = new Date();
        const epochTime = Math.floor(localTime.getTime() / 1000);
        res.locals.timeData = {
            cloudTime,
            localTime: localTime.toISOString(),
            epochTime
        };
    } catch (error) {
        console.error('Error fetching time data:', error);
        res.locals.timeData = {
            cloudTime: 'Unavailable',
            localTime: 'Unavailable',
            epochTime: 'Unavailable'
        };
    }
    next();
}

// Time for all pages
app.use(fetchTimeData);

// Breadcrumb middleware
app.use((req, res, next) => {
    res.locals.breadcrumbPath = [{
            text: 'Home',
            href: '/display'
        },
        {
            text: 'Data Entry',
            href: '/dataentry'
        },
        {
            text: 'RFID Linker',
            href: '/link-rfid'
        },
        {
            text: 'Delete RFID Link',
            href: '/delete-rfid-link'
        },
        {
            text: 'Boat Linker',
            href: '/boats'
        },
        {
            text: 'Import Data',
            href: '/importdata'
        },
        // Add or remove breadcrumb items as needed
    ];
    next();
});

class AppError extends Error {
    constructor(statusCode, message) {
        super();
        this.statusCode = statusCode;
        this.message = message;
    }
}

// Route for the homepage
app.get('/display', async (req, res, next) => {
    try {
        const timeResults = await pool.query(`
            SELECT tag_id, MIN(timestamp) AS first_timestamp, MAX(timestamp) AS last_timestamp
            FROM TIMERESULTS
            GROUP BY tag_id
        `);
        const demoBoatRFIDdata = await pool.query(`
            SELECT d.fname, d.lname, d.bibnumber, l.rfidtag, b.boatnumber
            FROM DEMODATA d
            JOIN LINKER l ON d.bibnumber = l.bibnumber
            INNER JOIN BOATS b ON d.bibnumber = b.bibnumber1 OR d.bibnumber = b.bibnumber2
        `);
        res.render('index', {
            timeResults: timeResults.rows,
            demoBoatRFIDdata: demoBoatRFIDdata.rows
        });
    } catch (error) {
        next(new AppError(500, 'Error fetching data - get - display'));
    }
});

// Route for the data entry form
app.get('/dataentry', async (req, res, next) => {
    try {
        const result = await pool.query('SELECT * FROM DEMODATA');
        res.render('dataentry', {
            demoData: result.rows
        });
    } catch (error) {
        next(new AppError(500, 'Error fetching data - get - dataentry'));
    }
});

// Route for inserting data into the database
app.post('/insert-demo-data', async (req, res, next) => {
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
        next(new AppError(500, 'Error inserting data - post - insert-demo-data'));
    }
});

// Route for displaying the edit form
app.get('/editdata', async (req, res, next) => {
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
        next(new AppError(500, 'Error editing data - get - editdata'));
    }
});

// Route for updating data in the database
app.post('/update-demo-data', async (req, res, next) => {
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
        next(new AppError(500, 'Error updating data - post - update-demo-data'));
    }
});

// Listen for RFID tag scanned event
rfidEmitter.on('tagScanned', (rfidTag) => {
    // Broadcast the RFID tag to all connected clients
    wss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify({
                rfidTag: rfidTag
            }));
        }
    });
});

// Route for linking RFID tag to bibnumber
app.get('/link-rfid', async (req, res, next) => {
    try {
        const linkerResult = await pool.query(`
            SELECT bibnumber AS linkerbibnumber, rfidtag, tag_id
            FROM LINKER
        `);
        // Query for orphaned BIBNUMBERs
        const orphanedBibNumbersResult = await pool.query(`
            SELECT bibnumber
            FROM DEMODATA
            WHERE bibnumber NOT IN (SELECT bibnumber FROM LINKER)
        `);
        const scannedRFIDTag = app.locals.scannedRFIDTag || '';
        res.render('linker', {
            linkerResult: linkerResult.rows,
            orphanedBibNumbers: orphanedBibNumbersResult.rows,
            scannedRFIDTag: scannedRFIDTag
        });
    } catch (error) {
        console.error(error); // Add this line to log the error
        next(new AppError(500, 'Error linking data - get - link-rfid'));
    }
});

// Route for linking RFID tag to bibnumber
app.post('/link-rfid', async (req, res, next) => {
    const {
        bibnumber,
        rfidtag
    } = req.body;

    // Split the rfidtag into id_type, id_tag, and id_position
    const [id_type, id_tag, id_position] = rfidtag.split('-');

    try {
        // Insert or update the LINKER table with the new RFID tag and bibnumber link
        await pool.query(`
            INSERT INTO LINKER (bibnumber, rfidtag, type_id, tag_id, position_id)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (bibnumber)
            DO UPDATE SET rfidtag = EXCLUDED.rfidtag, id_type = EXCLUDED.id_type, id_tag = EXCLUDED.id_tag, id_position = EXCLUDED.id_position
        `, [bibnumber, rfidtag, id_type, id_tag, id_position]);
        res.redirect('/link-rfid');
    } catch (error) {
        next(new AppError(500, 'Error linking data - post - link-rfid'));
    }
});

// Define the route for rendering the deletelink.ejs view
app.get('/delete-rfid-link', async (req, res, next) => {
    try {
        // Fetch necessary data from your database if needed
        // For example, let's say you want to display all RFID links in the deletelink.ejs page
        const result = await pool.query('SELECT * FROM LINKER'); // Adjust the query according to your database schema

        // Render the deletelink.ejs file and pass the fetched data to it
        res.render('deletelink', {
            demoData: result.rows // Assuming 'demoData' will be used in your deletelink.ejs to display the data
        });
    } catch (error) {
        next(new AppError(500, 'Error fetching data - get - delete-rfid-link'));
    }
});

// Route for deleting RFID link
app.post('/delete-rfid-link', async (req, res, next) => {
    const {
        bibnumber
    } = req.body;
    try {

        await pool.query('DELETE FROM LINKER WHERE bibnumber = $1', [bibnumber]);

        res.redirect('/delete-rfid-link');
    } catch (error) {
        next(new AppError(500, 'Error deleting RFID link - post - delete-rfid-link'));
    }
});

// Route for displaying unpaired bibnumber
app.get('/boats', async (req, res, next) => {
    try {
        // Fetch all bib numbers that are not yet paired
        const unpairedBibsResult = await pool.query(`
        SELECT d.fname, d.lname, d.unittype, d.unitnumber, d.bibnumber
        FROM DEMODATA d
        LEFT JOIN BOATS b ON d.bibnumber = b.bibnumber1 OR d.bibnumber = b.bibnumber2
        WHERE b.bibnumber1 IS NULL OR b.bibnumber2 IS NULL
        `);

        // Fetch all boat numbers along with their associated bib numbers
        const boatBibsResult = await pool.query(`
        SELECT boatnumber, bibnumber1, bibnumber2
        FROM BOATS
        `);

        // Render the boats.ejs file, passing both unpaired bibs data and boat bibs data
        res.render('boats', {
            unpairedBibs: unpairedBibsResult.rows,
            boatBibs: boatBibsResult.rows // Pass the fetched boat bibs data to the template
        });
    } catch (error) {
        next(new AppError(500, 'Error fetching data - get - boats'));
    }
});


// Route for creating a boatnumber out of two bibnumber
app.post('/boats', async (req, res, next) => {
    const {
        bibnumber1,
        bibnumber2
    } = req.body;

    // Check if bibnumber1 and bibnumber2 are not the same and not already paired
    if (bibnumber1 === bibnumber2) {
        return res.status(400).send('Cannot pair the same bibnumber.');
    }

    try {
        // Check if bibnumber1 or bibnumber2 is already in a pair
        const existingPairCheck = await pool.query(
            'SELECT * FROM BOATS WHERE bibnumber1 = $1 OR bibnumber2 = $2 OR bibnumber1 = $2 OR bibnumber2 = $1',
            [bibnumber1, bibnumber2]
        );
        if (existingPairCheck.rows.length > 0) {
            return res.status(400).send('One or both bibnumbers are already paired.');
        }

        // Generate a unique boatnumber using the nextval function
        const boatnumberResult = await pool.query('SELECT nextval(\'boats_boatnumber_seq\')');
        const boatnumber = boatnumberResult.rows[0].nextval;

        // Insert the bib numbers and the generated boatnumber into the BOATS table
        await pool.query(
            'INSERT INTO BOATS (bibnumber1, bibnumber2, boatnumber) VALUES ($1, $2, $3)',
            [bibnumber1, bibnumber2, boatnumber]
        );

        res.redirect('/boats');
    } catch (error) {
        next(new AppError(500, 'Error inserting data - post - boats'))
    }
});

// Route for displaying the edit form
app.get('/editboats', async (req, res, next) => {
    const {
        boatnumber
    } = req.query;

    try {
        const result = await pool.query('SELECT bibnumber1, bibnumber2 FROM BOATS WHERE boatnumber = $1', [boatnumber]);
        if (result.rows.length > 0) {
            // Render the edit form with the current bib numbers
            res.render('editboats', {
                boatnumber: boatnumber,
                currentBib1: result.rows[0].bibnumber1,
                currentBib2: result.rows[0].bibnumber2
            });
        } else {
            res.send('Boat not found');
        }
    } catch (error) {
        next(new AppError(500, 'Error editing data - get - editboats'))
    }
});

// Route for updating bib numbers in the database
app.post('/update-boat-data', async (req, res, next) => {
    const {
        boatnumber,
        bibnumber1,
        bibnumber2
    } = req.body;
    try {
        await pool.query(
            'UPDATE BOATS SET bibnumber1 = $1, bibnumber2 = $2 WHERE boatnumber = $3',
            [bibnumber1, bibnumber2, boatnumber]
        );
        res.redirect('/boats');
    } catch (error) {
        next(new AppError(500, 'Error updating data - post - update-boat-data'));
    }
});

app.get('/importdata', async (req, res, next) => {
    let file = [];
    try {
        file = await readdir(uploadsDirectory);
        console.log('Files:', file); // Log the file
    } catch (error) {
        console.error('Error:', error); // Log the error
    }
    try {
        res.render('importdata', {
            messages: req.flash(),
            file: file
        });
    } catch (error) {
        next(new AppError(500, 'Error fetching data - get - importdata'));
    }
});

// Route for uploading a file
app.post('/upload', upload.single('file'), async (req, res, next) => {
    try {
        req.flash('success', 'File uploaded successfully');
        let file = [];
        try {
            file = await readdir(uploadsDirectory);
            console.log('Files:', file); // Log the file
        } catch (error) {
            console.error('Error:', error); // Log the error
        }
        res.render('importdata', {
            messages: req.flash(),
            file: file
        });
    } catch (error) {
        next(new AppError(500, 'Error uploading file - post - upload'));
    }
});

// Route for downloading a file
app.get('/download/:filename', (req, res, next) => {
    try {
        const filename = req.params.filename;
        const file = path.join(uploadsDirectory, filename);
        res.download(file); // Set disposition and send it.
    } catch (error) {
        next(new AppError(500, 'Error downloading file - get - download'));
    }
});

// Route for deleting a file
app.post('/delete-file', (req, res, next) => {
    try {
        const filename = req.body.filename;
        fs.unlink(path.join(uploadsDirectory, filename), err => {
            if (err) {
                console.error(err);
                res.status(500).send('An error occurred while deleting the file.');
            } else {
                res.redirect('/importdata');
            }
        });
    } catch (error) {
        next(new AppError(502, 'Error deleting file - post - delete-file'));
    }
});

// Route for Importing Time Data
app.post('/importime', async (req, res, next) => {
    try {
        const filename = req.body.filename; // Get the filename from the form data
        const filePath = path.join(uploadsDirectory, filename);
        const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));

        for (const item of data) {
            await pool.query(`
                INSERT INTO timeresults (tag_type, tag_id, tag_position, timestamp, timestamp_h)
                VALUES ($1, $2, $3, $4, $5)
        `, [item.tag_type, item.tag_id, item.tag_position, item.timestamp, item.timestamp_h]);
        }
        req.flash('success', 'Data imported successfully');

        let file = [];
        try {
            file = await readdir(uploadsDirectory);
            console.log('Files:', file); // Log the file
        } catch (error) {
            console.error('Error:', error); // Log the error
        }

        res.render('importdata', {
            messages: req.flash(),
            file: file
        }); // Redirect back to the importdata page
    } catch (error) {
        console.error('Detailed error:', error);
        next(new AppError(500, 'Error importing time data - post - importime'));
    }
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack);
    if (err instanceof AppError) {
        res.status(err.statusCode).send(err.message);
    } else {
        res.status(500).send('Something broke!');
    }
});

// Helmet Middleware
const helmet = require('helmet');
app.use(helmet());

// Start the server
const server = app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});

server.on('upgrade', (request, socket, head) => {
    wss.handleUpgrade(request, socket, head, (ws) => {
        wss.emit('connection', ws, request);
    });
});