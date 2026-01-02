FROM python:3.10-slim

# 1. Standard environment settings
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 2. CRITICAL: Force cmake to use only 1 core to prevent running out of RAM
ENV CMAKE_BUILD_PARALLEL_LEVEL=1

# 3. Install system dependencies (needed for dlib/opencv)
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 4. Install python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/
COPY build.sh /app/
RUN chmod +x /app/build.sh

EXPOSE 8000

CMD ["./build.sh"]