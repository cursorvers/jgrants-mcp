FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade "pip>=26.2.2" "certifi>=2026.10.19" \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY jgrants_mcp_server/ ./jgrants_mcp_server/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "jgrants_mcp_server.server:app", "--host", "0.0.0.0", "--port", "8000"]
