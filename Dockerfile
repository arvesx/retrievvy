# Build stage
FROM python:3.13-bookworm AS builder
ENV TORCH_CUDA_ARCH_LIST=""
RUN apt-get update && apt-get install -y --no-install-recommends libxapian-dev && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv==0.6.6
WORKDIR /app
COPY pyproject.toml uv.lock /app/
RUN uv sync --no-dev --frozen && \
    find .venv -type d -name "__pycache__" -exec rm -r {} + && \
    find .venv -type f -name "*.pyc" -delete

# Final Image
FROM python:3.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get install -y libxapian30 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /app/.venv/ /venv/
COPY . /app
ENTRYPOINT ["/venv/bin/python", "-m", "retrievvy"]