FROM python:3.10-slim-buster

ARG SERVICE_PORT=8000
ENV SERVICE_PORT=${SERVICE_PORT}

# Set up working directory
WORKDIR /kapital

# Copy only requirements file first for caching
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

# Install additional packages
RUN apt update && \
    apt install -y ca-certificates curl && \
    apt install -y poppler-utils

# Copy the rest of the application code
COPY . /kapital

# Set app working directory
WORKDIR /kapital

# Health check
HEALTHCHECK CMD curl --fail http://localhost:${SERVICE_PORT}/api/health || exit 1

# Start the application with uvicorn
CMD uvicorn app.api:app --host 0.0.0.0 --port ${SERVICE_PORT} --reload
