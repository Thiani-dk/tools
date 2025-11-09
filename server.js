// --- SERVER.JS (Updated for Asynchronous Conversion) ---

import express from 'express';
import cors from 'cors';
import fs from 'fs/promises'; 
import path from 'path';
import { createReadStream } from 'fs'; 
import crypto from 'crypto';
// REMOVED: import { exec } from 'child_process'; 

// NEW: Import the background conversion worker
import { startConversion } from './converter.js'; 

const app = express();
const PORT = 3000;
const UPLOAD_DIR = './uploads';

// In a real application, this would be a database/in-memory store.
// This is now the shared state object passed to the converter.
const conversionSessions = {}; 

// --- MIDDLEWARE SETUP ---
app.use(cors({ origin: '*' })); 

// 1. Parse JSON first: Handles the /api/upload/session route payload.
app.use(express.json()); 
// 2. Parse Raw/Binary second: Handles the chunk uploads (must be application/octet-stream or similar on client side).
app.use(express.raw({ type: '*/*', limit: '5mb' })); 

// Ensure the upload directory exists
async function initializeServer() {
    try {
        await fs.mkdir(UPLOAD_DIR, { recursive: true });
        console.log(`Upload directory created at: ${UPLOAD_DIR}`);
    } catch (error) {
        console.error("Failed to initialize server directory:", error);
        // If we can't create the directory, the server cannot run.
        process.exit(1); 
    }
}

// NOTE: The function startConversion was moved to converter.js


// --- 1. START SESSION (POST /api/upload/session) ---
app.post('/api/upload/session', (req, res) => {
    const { fileName, fileSize } = req.body;
    if (!fileName || !fileSize) {
        return res.status(400).json({ error: 'Missing fileName or fileSize' });
    }

    const sessionId = crypto.randomUUID();
    // Prefix the file name with the session ID to make it unique
    const tempFilePath = path.join(UPLOAD_DIR, `${sessionId}-${fileName}`);

    conversionSessions[sessionId] = {
        sessionId,
        fileName,
        fileSize,
        tempFilePath,
        chunksReceived: 0,
        status: 'pending', 
        conversionProgress: 0,
        createdAt: Date.now()
    };

    console.log(`[${sessionId}] Session created for ${fileName} (${(fileSize / 1024 / 1024).toFixed(2)} MB).`);
    // NOTE: This response should also be updated on the client side to use the new polling flow.
    res.json({ sessionId });
});


// --- 2. UPLOAD CHUNK (POST /api/upload/chunk/:sessionId) ---
app.post('/api/upload/chunk/:sessionId', async (req, res) => {
    const sessionId = req.params.sessionId;
    const session = conversionSessions[sessionId];

    if (!session || session.status === 'processing' || session.status === 'complete') {
        return res.status(404).json({ error: 'Session not found or conversion already started.' });
    }

    const chunkIndex = parseInt(req.query.chunkIndex); // Index sent by client

    if (isNaN(chunkIndex)) {
        return res.status(400).json({ error: 'Missing or invalid chunkIndex.' });
    }

    try {
        const tempPath = session.tempFilePath;

        // Ensure req.body is a buffer (which it should be if express.raw ran correctly)
        if (!Buffer.isBuffer(req.body)) {
             // This happens if the JSON parser consumed the stream due to a wrong client Content-Type header.
             throw new Error('Received non-Buffer data. Check client Content-Type header for chunk upload.');
        }

        // Append the raw binary chunk data (req.body is a Buffer due to express.raw)
        await fs.appendFile(tempPath, req.body);
        
        session.chunksReceived++;
        session.status = 'uploading';
        
        console.log(`[${sessionId}] Chunk ${chunkIndex} received. Current chunk size: ${req.body.length}`);

        return res.json({ status: 'received', chunks: session.chunksReceived });

    } catch (error) {
        console.error(`[${sessionId}] Failed to write chunk:`, error.message);
        session.status = 'failed';
        return res.status(500).json({ error: `Failed to save chunk to disk. Cause: ${error.message}` });
    }
});


// --- 3. COMPLETE UPLOAD / START ASYNC CONVERSION (POST /api/upload/complete/:sessionId) ---
app.post('/api/upload/complete/:sessionId', (req, res) => {
    const sessionId = req.params.sessionId;
    const session = conversionSessions[sessionId];

    if (!session || session.status !== 'uploading') {
        return res.status(404).json({ error: 'Session not found or incomplete upload.' });
    }

    session.status = 'uploaded';
    console.log(`[${sessionId}] File assembly complete. Starting ASYNC conversion...`);

    // **CRITICAL CHANGE:** Start the conversion but DO NOT await the result.
    // The converter.js file is responsible for updating the status later.
    startConversion(sessionId, conversionSessions); 

    // Return immediately with a 202 Accepted status.
    // This immediately frees up the request, preventing the timeout.
    res.status(202).json({ 
        status: 'accepted', 
        message: 'Conversion job started in background. Poll /api/conversion/status/:sessionId for result.' 
    });
});


// --- 4. CONVERSION STATUS (GET /api/conversion/status/:sessionId) ---
// This route now functions as the client's polling endpoint.
app.get('/api/conversion/status/:sessionId', (req, res) => {
    const sessionId = req.params.sessionId;
    const session = conversionSessions[sessionId];

    if (!session) {
        return res.status(404).json({ error: 'Session not found.' });
    }
    
    // Status is dynamically updated by the background worker (converter.js)
    res.json({
        status: session.status,
        progress: session.conversionProgress, 
        downloadUrl: session.status === 'complete' ? `/api/download/${sessionId}` : null,
        error: session.error
    });
});


// --- 5. DOWNLOAD FILE (GET /api/download/:sessionId) ---
app.get('/api/download/:sessionId', async (req, res) => {
    const sessionId = req.params.sessionId;
    const session = conversionSessions[sessionId];

    if (!session || session.status !== 'complete' || !session.downloadPath) {
        return res.status(404).send('File not found or conversion not complete.');
    }

    try {
        await fs.access(session.downloadPath); // Final check that the file exists on disk
        
        // Use the original filename to set the download name for the user
        const originalFileName = session.fileName; 
        const downloadFileName = originalFileName.replace(/\.(ppt|pptx)$/i, '.pdf');

        res.setHeader('Content-Type', 'application/pdf');
        res.setHeader('Content-Disposition', `attachment; filename="${downloadFileName}"`);
        
        // Stream the actual converted PDF file
        const fileStream = createReadStream(session.downloadPath);
        fileStream.pipe(res);

    } catch (error) {
        console.error(`[${sessionId}] Error accessing or streaming download file:`, error);
        return res.status(500).send('Error serving the converted file.');
    }
});


// Start the server
initializeServer().then(() => {
    app.listen(PORT, () => {
        console.log(`Server running on http://localhost:${PORT}`);
        console.log("Conversion engine: LibreOffice (requires installation via Docker or host environment).");
    });
});