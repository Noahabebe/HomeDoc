# Use the official Python image.
FROM python:3.11

# Set non-interactive mode for Debian.
ARG DEBIAN_FRONTEND=noninteractive

# Install dependencies required for Playwright to run Chromium.
RUN apt-get update -q && \
    apt-get install -y -qq --no-install-recommends \
        xvfb \
        libxcomposite1 \
        libxdamage1 \
        libatk1.0-0 \
        libasound2 \
        libdbus-1-3 \
        libnspr4 \
        libgbm1 \
        libatk-bridge2.0-0 \
        libcups2 \
        libxkbcommon0 \
        libatspi2.0-0 \
        libnss3

# Install Python dependencies and Playwright.
COPY requirements.txt . 
RUN pip install -r requirements.txt && \
    pip install playwright && \
    playwright install chromium

# Copy your application script.
COPY app.py .

# Set environment variable for display.
ENV DISPLAY=:99

# Run the X virtual framebuffer and your Playwright script.
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
