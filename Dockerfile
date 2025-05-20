FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Create a non-root user
RUN addgroup --system app && \
    adduser --system --ingroup app app

WORKDIR /app

# Copy requirements and install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create cache directory with proper permissions
RUN mkdir -p .cache && chown -R app:app .cache

# Set the proper ownership
RUN chown -R app:app /app

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Run the server
CMD ["python", "server.py"]