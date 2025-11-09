import fs from 'fs/promises';
import path from 'path';
import { exec } from 'child_process';

const UPLOAD_DIR = './uploads';

/**
 * Executes the LibreOffice conversion command in a non-blocking child process.
 * Updates the provided conversionSessions object upon completion or failure.
 * @param {string} sessionId - The unique ID for the conversion job.
 * @param {object} conversionSessions - The in-memory map holding all session data.
 */
export function startConversion(sessionId, conversionSessions) {
    const session = conversionSessions[sessionId];
    if (!session || session.status !== 'uploaded') return;

    // Immediately update status to processing (the main server request has already returned 202)
    session.status = 'processing';
    session.conversionProgress = 50; // Indicates upload is done, conversion is running
    
    const inputPath = session.tempFilePath;
    // The input file name includes the session ID prefix, e.g., '123-filename.pptx'
    const inputFileName = path.basename(inputPath);
    
    // LibreOffice outputs a file named after the original input name (excluding the session prefix)
    const expectedLibreOfficeOutputBaseName = inputFileName.split('-').slice(1).join('-').replace(/\.(ppt|pptx)$/i, '.pdf'); 

    // Define the final, session-specific download path
    const finalDownloadPath = path.join(UPLOAD_DIR, `${sessionId}.pdf`); 

    // Command: Convert input file to PDF, outputting it to the UPLOAD_DIR
    const libreOfficeCommand = 
        `libreoffice --headless --convert-to pdf:writer_pdf_Export --outdir ${UPLOAD_DIR} ${inputPath}`;

    console.log(`[${sessionId}] Conversion queued. Executing in background...`);
    
    // Run the conversion in a separate, non-blocking process
    exec(libreOfficeCommand, async (error, stdout, stderr) => {
        
        // 1. Check for Command Execution Errors
        if (error) {
            console.error(`[${sessionId}] Conversion execution failed:`, error);
            session.status = 'failed';
            session.error = `Conversion failed. Shell Error: ${error.message}`;
        } else {
            // 2. Conversion Success: Find and rename the output file
            try {
                // Find the file LibreOffice created
                const tempOutputFilePath = path.join(UPLOAD_DIR, expectedLibreOfficeOutputBaseName);
                
                await fs.access(tempOutputFilePath); // Verify output file exists
                await fs.rename(tempOutputFilePath, finalDownloadPath); // Rename it to the final session ID path
                
                session.status = 'complete';
                session.conversionProgress = 100;
                session.downloadPath = finalDownloadPath; 
                console.log(`[${sessionId}] Conversion successful. PDF saved.`);

            } catch (fileError) {
                console.error(`[${sessionId}] Post-conversion File Error:`, fileError);
                session.status = 'failed';
                session.error = 'Conversion succeeded but the output PDF could not be found or renamed.';
            }
        }

        // 3. Cleanup the original input file regardless of success
        try {
            if (await fs.stat(inputPath)) {
                await fs.unlink(inputPath);
                console.log(`[${sessionId}] Cleaned up temporary input file: ${inputPath}`);
            }
        } catch (cleanupError) {
            // Log this, but don't fail the whole job
            console.error(`[${sessionId}] Failed to clean up input file:`, cleanupError.message);
        }
    });
}