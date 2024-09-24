# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=mewray.settings
ENV DJANGO_SUPERUSER_USERNAME=meshya
ENV DJANGO_SUPERUSER_EMAIL=mew@mew.mew
ENV DJANGO_SUPERUSER_PASSWORD=mewmew

RUN mkdir -p /mewray
RUN touch /f

# Set working directory
WORKDIR /mewray


# Install Python dependencies
COPY requirements.txt /mewray/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the Django app code
COPY . /mewray/

EXPOSE 8000


RUN python manage.py migrate
RUN python manage.py inituser


# Default command to run your Django app using gunicorn
CMD ["bash", "-c", "daphne mewray.asgi:application -b 0.0.0.0 -p 8000 & celery -A core beat --loglevel=info & celery -A core worker --loglevel=info"]
