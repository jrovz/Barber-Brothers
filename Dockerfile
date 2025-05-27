# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create uploads folder if it doesn't exist
RUN mkdir -p app/static/uploads

# Set environment variables
ENV FLASK_APP=wsgi.py \
    FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Create a startup script
RUN echo '#!/bin/bash\n\
echo "Starting Barberia App service..."\n\
echo "Environment variables:"\n\
echo "- INSTANCE_CONNECTION_NAME: $INSTANCE_CONNECTION_NAME"\n\
echo "- DB_USER: $DB_USER"\n\
echo "- DB_NAME: $DB_NAME"\n\
echo "- GOOGLE_CLOUD_PROJECT: $GOOGLE_CLOUD_PROJECT"\n\
echo "- FLASK_ENV: $FLASK_ENV"\n\
echo "- REGION: $REGION"\n\
echo "Database initialization starting..."\n\
python -u setup_db.py || echo "Database setup exited with code $?. Continuing anyway..."\n\
echo "Database initialization completed."\n\
echo "Starting Gunicorn server..."\n\
exec gunicorn --bind :$PORT --workers 2 --threads 8 --timeout 0 wsgi:app\n\
' > /app/startup.sh

# Make startup script executable
RUN chmod +x /app/startup.sh

# Expose the port the app will run on
EXPOSE 8080

# Command to run the application with Gunicorn
CMD ["/app/startup.sh"]
