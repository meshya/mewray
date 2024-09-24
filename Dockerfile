# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the Django app code
COPY . /app/

# Expose the port for the app (if not using NGINX as a reverse proxy)
EXPOSE 8000

# Default command to run your Django app using gunicorn
CMD ["bash", "-c", "daphne mewray.asgi:application -b 0.0.0.0 -p 8000 & celery -A core beat --loglevel=info & celery -A core worker --loglevel=info"]
