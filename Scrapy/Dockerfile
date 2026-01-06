FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for scrapy-impersonate
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pymongo

# Copy application code
COPY crawler/ ./crawler/
COPY scrapy.cfg .

# Create data directory
RUN mkdir -p /app/data

# Default command: run the spider
CMD ["scrapy", "crawl", "animals", "-o", "data/animals.json"]
