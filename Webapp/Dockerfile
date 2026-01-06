FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./

# Expose port for Dash
EXPOSE 8050

# Run the Dash application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8050", "app:server"]
