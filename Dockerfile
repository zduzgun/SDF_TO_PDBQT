# SDF to PDBQT Converter Docker Image
# Multi-stage build for optimization

# Base stage with system dependencies
FROM ubuntu:20.04 as base

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    bzip2 \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -b -p /opt/conda \
    && rm /tmp/miniconda.sh

# Add conda to PATH
ENV PATH="/opt/conda/bin:$PATH"

# Install OpenBabel
RUN conda install -c conda-forge openbabel>=3.1.0 -y

# Development stage
FROM base as development

# Copy environment file
COPY environment.yml /tmp/environment.yml

# Create conda environment
RUN conda env create -f /tmp/environment.yml

# Activate environment
SHELL ["conda", "run", "-n", "sdf_pdbqt", "/bin/bash", "-c"]

# Copy source code
WORKDIR /app
COPY . .

# Install package in development mode
RUN pip install -e .[dev]

# Default command
CMD ["conda", "run", "-n", "sdf_pdbqt", "python", "sdf_to_pdbqt_converter.py"]

# Production stage
FROM base as production

# Copy environment file
COPY environment.yml /tmp/environment.yml

# Create conda environment
RUN conda env create -f /tmp/environment.yml

# Activate environment
SHELL ["conda", "run", "-n", "sdf_pdbqt", "/bin/bash", "-c"]

# Copy source code
WORKDIR /app
COPY . .

# Install package
RUN pip install .

# Create directories for data
RUN mkdir -p /data/input /data/output /data/logs

# Set environment variables
ENV INPUT_BASE_DIR="/data/input" \
    OUTPUT_BASE_DIR="/data/output" \
    PYTHONPATH="/app"

# Default command
CMD ["conda", "run", "-n", "sdf_pdbqt", "python", "sdf_to_pdbqt_converter.py"]

# Labels
LABEL maintainer="TR-GRID Team <info@tr-grid.org>" \
      version="1.0.0" \
      description="SDF to PDBQT Converter Pipeline" \
      org.opencontainers.image.source="https://github.com/tr-grid/SDF_TO_PDBQT" 