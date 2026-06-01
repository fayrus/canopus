FROM python:3.12-slim AS builder

WORKDIR /app

COPY pyproject.toml .
COPY canopus/ canopus/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ".[postgres,mysql]"


FROM python:3.12-slim AS runtime

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY canopus/ canopus/
COPY app.py .

ENV CANOPUS_DEBUG=false
ENV CANOPUS_HOST=0.0.0.0
ENV CANOPUS_PORT=2107

EXPOSE 2107

CMD ["python", "app.py"]
