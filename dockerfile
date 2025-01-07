# Use a base Python image
FROM python:3.12-slim

# Set environment variables to avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory in the container
WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    dos2unix \
    nano \
    curl \
    libx11-xcb1 \
    libxcomposite1 \
    libxrandr2 \
    libxi6 \
    libgdk-pixbuf2.0-0 \
    libdbus-1-3 \
    libnss3 \
    libxtst6 \
    libatk1.0-0 \
    libnspr4 \
    libatspi2.0-0 \
    xdg-utils \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm-dev \
    redis-server \
    ufw \
    certbot \
    wget && \
    # Clean up apt cache to reduce image size
    rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get update && \
    apt-get install -y --no-install-recommends ./google-chrome-stable_current_amd64.deb && \
    rm -f google-chrome-stable_current_amd64.deb && \
    apt-get clean && \
    # Clean up apt cache to reduce image size
    rm -rf /var/lib/apt/lists/*

RUN chmod +x /usr/bin/google-chrome

# Copy the requirements.txt file to the container
COPY requirements.txt .

# Install Python dependencies and clean pip cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Copy start.sh and fix line endings
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh && dos2unix /app/start.sh