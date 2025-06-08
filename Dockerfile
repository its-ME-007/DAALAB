FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy all necessary files
COPY requirements.txt .
COPY heap_sort.py .
COPY merge_sort.py .
COPY quick_sort.py .
COPY insertion_sort.py .
COPY sort_server.py .

# Install dependencies
RUN pip install -r requirements.txt

# Expose FastAPI port
EXPOSE 8000

# Set the default command
CMD ["uvicorn", "sort_server:app", "--host", "0.0.0.0", "--port", "8000"]