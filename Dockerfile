# 1. Use a lightweight Python base image
FROM python:3.10-slim

# 2. Set environment variables to keep Python clean
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Install system dependencies needed for dlib and opencv
# This is the magic step that prevents the memory crash
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    && rm -rf /var/lib/apt/lists/*

# 4. Set the working directory
WORKDIR /app

# 5. Copy requirements and install them
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of the project code
COPY . /app/

# 7. Make the build script executable (optional but good practice)
COPY build.sh /app/
RUN chmod +x /app/build.sh

# 8. Expose the port Render expects
EXPOSE 8000

# 9. The command to start the server (Run migrations then start Gunicorn)
CMD ["sh", "-c", "python manage.py collectstatic --no-input && python manage.py migrate && gunicorn smart_attendance.wsgi:application --bind 0.0.0.0:8000"]