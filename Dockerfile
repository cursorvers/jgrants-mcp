FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY jgrants_mcp_server/ ./jgrants_mcp_server/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "jgrants_mcp_server.server:app", "--host", "0.0.0.0", "--port", "8000"]

