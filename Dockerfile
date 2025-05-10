# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Add placeholder Twilio environment variables (needed only for build)


# Set the working directory in the container
WORKDIR /app

# Install system dependencies if needed (e.g., for psycopg2-binary if using PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Specify the command to run on container start
# Use the run.py script which runs uvicorn
CMD ["python", "run.py"] 