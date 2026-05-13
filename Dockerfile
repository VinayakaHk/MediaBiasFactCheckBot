# syntax=docker/dockerfile:1.7

FROM python:3.12-slim AS base

# -- System dependencies ------------------------------------------------------
# - firefox-esr + geckodriver: selenium scraping in src/perplexity.py
# - xvfb + libs: PyVirtualDisplay path in src/llm_automation.py
# - build-essential/libs: only needed if any wheel falls back to source build
# - tini: clean signal handling for the long-running bot process
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      wget \
      gnupg \
      tini \
      firefox-esr \
      xvfb \
      libgl1 \
      libglib2.0-0 \
      fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# -- geckodriver (architecture-aware) -----------------------------------------
ARG GECKODRIVER_VERSION=0.35.0
RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in \
      amd64) gecko_arch="linux64" ;; \
      arm64) gecko_arch="linux-aarch64" ;; \
      *) echo "Unsupported arch: $arch" >&2; exit 1 ;; \
    esac; \
    wget -q "https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-${gecko_arch}.tar.gz" \
        -O /tmp/geckodriver.tgz; \
    tar -xzf /tmp/geckodriver.tgz -C /usr/local/bin; \
    chmod +x /usr/local/bin/geckodriver; \
    rm /tmp/geckodriver.tgz; \
    geckodriver --version

# -- Python environment -------------------------------------------------------
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install Python deps first so they cache across code changes
COPY requirements.txt ./
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# -- App ----------------------------------------------------------------------
# Copy the rest of the project. .dockerignore keeps .venv, db/, .env, .git, caches out.
COPY . .

# src/perplexity.py hardcodes geckodriver to /opt/homebrew/bin (Darwin) or
# /usr/local/bin (Linux). We install it at /usr/local/bin, so Linux path is correct.

# Run as non-root for safety
RUN useradd --create-home --shell /bin/bash appuser \
 && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "main.py"]
