# Use a Node.js base image based on Debian
FROM node:20-slim

# Install LibreOffice and necessary dependencies for headless operation
# Fonts are crucial for proper document rendering and conversion fidelity
RUN apt-get update && apt-get install -y \
    libreoffice \
    fonts-noto \
    fonts-dejavu \
    # Clean up APT cache to reduce image size
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy package.json and install Node.js dependencies
# We assume 'package.json' only contains express and cors
COPY package.json ./
RUN npm install --omit=dev

# Copy the rest of the application code
COPY server.js .
# FIX: Copy the converter.js file, which is required by server.js
COPY converter.js .

# Create the directory for uploads and ensure it has necessary permissions 
# for LibreOffice to write and Node to read/write.
RUN mkdir -p uploads && chmod 777 uploads

# Expose the port the app runs on (must match the port 3000 in server.js)
EXPOSE 3000

# Command to run the application
CMD ["node", "server.js"]