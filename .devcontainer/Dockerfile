FROM mcr.microsoft.com/devcontainers/python:3.11

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt* /tmp/
RUN if [ -f /tmp/requirements.txt ]; then pip install --no-cache-dir -r /tmp/requirements.txt; fi

ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_RUN_ON_SAVE=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    PYTHONUNBUFFERED=1

WORKDIR /workspace
