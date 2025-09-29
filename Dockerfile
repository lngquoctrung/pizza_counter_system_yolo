FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    ca-certificates \
    openssl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY app.py pizza_counter.py ./
COPY templates/ ./templates/

RUN mkdir -p /app/videos /app/models /app/logs

RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

ENV DISPLAY=
ENV QT_QPA_PLATFORM=offscreen

EXPOSE 5000
CMD ["python", "app.py"]
