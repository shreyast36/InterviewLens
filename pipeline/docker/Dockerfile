FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY configs/ configs/
COPY pyproject.toml .

ENV PYTHONPATH=/app/src

EXPOSE 8000
CMD ["uvicorn", "interviewlens.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
