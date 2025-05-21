# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create uploads folder if it doesn't exist
RUN mkdir -p app/static/uploads

# Set environment variables
ENV FLASK_APP=wsgi.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose the port the app will run on
EXPOSE 8080

# Command to run the application with Gunicorn
CMD exec gunicorn --bind :8080 --workers 1 --threads 8 --timeout 0 wsgi:app
