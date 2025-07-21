FROM python:3.12.10-slim

# Install necessary system packages - fix GPG issues
RUN apt-get clean && rm -rf /var/lib/apt/lists/* && \
    apt-get update --allow-releaseinfo-change && apt-get install -y \
    git \
    curl \
    build-essential \
    unzip \
    xz-utils \
    zip \
    libglu1-mesa \
    clang \
    cmake \
    ninja-build \
    pkg-config \
    libgtk-3-dev \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs=20.11.1-1nodesource1 && \
    npm install -g npm@10.2.4

# Install pyright
RUN npm install -g pyright@1.1.400

# Create a non-root user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Set up Python environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="." \
    VIRTUAL_ENV=/workspaces/nimble_agent/venv

# Install Python tools
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    black \
    ruff \
    mypy \
    pytest>=7.4.3 \
    pytest-asyncio>=0.23.2 \
    coverage \
    pytest-cov \
    virtualenv \
    types-Jinja2==2.11.9 \
    types-PyYAML==6.0.12.12

# Download and install Flutter
ENV FLUTTER_HOME=/usr/local/flutter
ENV PATH=$FLUTTER_HOME/bin:$PATH

RUN git clone https://github.com/flutter/flutter.git $FLUTTER_HOME && \
    cd $FLUTTER_HOME && \
    git checkout stable && \
    flutter precache && \
    chown -R $USERNAME:$USERNAME $FLUTTER_HOME

# Switch to non-root user
USER $USERNAME

# Pre-download Flutter artifacts
RUN flutter doctor

# Set the working directory
WORKDIR /workspace