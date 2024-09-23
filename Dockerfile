# Use an official Python runtime as a base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt /app/

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SUPERUSER_USERNAME=meshya
ENV DJANGO_SUPERUSER_EMAIL=admin@example.com
ENV DJANGO_SUPERUSER_PASSWORD=okiptabledotcom
ENV DJANGO_SETTINGS_MODULE=mewray.settings
ENV MEWRAY_DEBUG 0

# Copy the rest of the application code into the container
# COPY . /app/

RUN touch ee
RUN  python /app/manage.py migrate --noinput 
RUN  python /app/manage.py collectstatic --noinput
RUN  python /app/manage.py inituser

# Expose the application port for Daphne (default 8000)
EXPOSE 8000

# Command to run Django migrations and start the app with Daphne
CMD ["sh", "-c", "daphne -b 0.0.0.0 -p 8000 mewray.asgi:application"]
