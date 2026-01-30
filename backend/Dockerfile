# Use official Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies (for building python packages if needed)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file (use the IMS specific one)
COPY requirements-ims.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-ims.txt

# Copy Prisma schema and generate client
COPY prisma/ ./prisma/
RUN prisma generate

# Copy the application code
COPY app/ ./app/
COPY frontend-test/ ./frontend-test/
COPY *.py .

# Expose the API port
EXPOSE 8000

# Command to run the application
# We use bash to chain commands: 
# 1. Update DB schema (prisma db push)
# 2. Seed initial data (safe to run multiple times)
# 3. Start the server
CMD ["bash", "-c", "prisma db push && python seed.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
