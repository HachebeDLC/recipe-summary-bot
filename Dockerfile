# Use a specific Python runtime as a parent image
FROM python:3.9.16-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Create a non-root user
RUN addgroup --system app && adduser --system --group app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY main.py .

# Change the owner of the files to the app user
RUN chown -R app:app /app

# Switch to the non-root user
USER app

# Run main.py when the container launches
CMD ["python", "main.py"]
