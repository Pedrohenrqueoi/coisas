FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements/base.txt requirements/base.txt
COPY requirements/production.txt requirements/production.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements/production.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads done temp logs

# Expose port
EXPOSE 5000

# Default command (overridden in docker-compose)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]