FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
COPY heap_sort.py .
COPY merge_sort.py .
COPY quick_sort.py .
COPY insertion_sort.py .
COPY sort_server.py .

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "sort_server:app", "--host", "0.0.0.0", "--port", "8000"] 