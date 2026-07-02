FROM python:3.11-slim

WORKDIR /app

# PyMuPDF may require minimal system libraries on slim images.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libmupdf-dev \
        mupdf-tools \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY covenant_pipeline ./covenant_pipeline
COPY config ./config
COPY viewer/backend ./viewer/backend

RUN pip install --no-cache-dir -e ".[viewer]"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--app-dir", "viewer/backend", "--host", "0.0.0.0", "--port", "8000"]
