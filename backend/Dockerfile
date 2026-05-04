FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
# libraqm + harfbuzz/fribidi enable complex-script shaping (Devanagari, Arabic, etc.)
# in Pillow. The Pillow wheel on PyPI isn't built against libraqm, so we install
# from source below to pick it up.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libraqm-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libfreetype6-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies — Pillow built from source so it links libraqm.
COPY requirements.txt .
RUN pip install --no-cache-dir --no-binary Pillow -r requirements.txt

# Copy backend source code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
