# Build stage
FROM python:3.13-bookworm AS builder
RUN apt-get update && apt-get install -y libxapian-dev
RUN pip install --no-cache-dir uv==0.6.6
WORKDIR /app
COPY pyproject.toml uv.lock /app/
RUN uv sync --no-dev --frozen && ./.venv/bin/python -m ensurepip


# Final Image
FROM python:3.13-alpine
WORKDIR /app
COPY --from=builder /app/.venv/ /venv/
COPY . /app
CMD ["/venv/bin/python", "-m", "retrievvy"]