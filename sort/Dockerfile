FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy all necessary files
COPY requirements.txt .
COPY *.py .

# Install dependencies
RUN pip install -r requirements.txt

# Expose FastAPI port
EXPOSE 8000

# Set the default command
CMD ["uvicorn", "sort_server:app", "--host", "0.0.0.0", "--port", "8000"] 