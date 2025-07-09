# Base image using slim Python for smaller footprint
FROM python:3.11-slim

# Avoid interactive prompts & Python bytecode generation
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user (optional but recommended)
ARG USER=appuser
ARG UID=1000
RUN useradd -m -u ${UID} ${USER}

# Set workdir
WORKDIR /app

# Install Python dependencies first (leverages Docker cache)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . /app

# Switch to non-root user
USER ${USER}

# Expose Jupyter/default port for debugging or UI tools
EXPOSE 8888

# Default command keeps container alive for interactive debugging
CMD ["bash"]
