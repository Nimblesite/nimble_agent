#!/bin/bash

# Exit on any error
set -e

# Ensure script is run from project root
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Must run script from project root"
    exit 1
fi

echo "🚀 Setting up development environment..."

# Skip virtual environment creation in a dev container
# as we want to use the global Python interpreter
echo "📦 Installing in dev container environment..."

# Upgrade pip first
echo "📦 Upgrading pip..."
python -m pip install --upgrade pip

# Install the package in editable mode with dev dependencies first
echo "📦 Installing package in development mode..."
pip install -e ".[dev]"

# Install core requirements first as they're most critical
echo "📦 Installing core requirements..."
pip install -r ai_coding_agent/core/requirements.txt

# Explicitly install type stubs for Jinja2 and PyYAML to fix mypy errors
echo "📦 Installing type stubs for templating libraries..."
pip install types-Jinja2==2.11.9 types-PyYAML==6.0.12.12

# Install CLI requirements
echo "📦 Installing CLI requirements..."
pip install -r ai_coding_agent/cli/requirements.txt

# Install test requirements
echo "📦 Installing test requirements..."
pip install -r ai_coding_agent/tests/requirements.txt
if [ -f "ai_coding_agent/tests/requirements-dev.txt" ]; then
    echo "📦 Installing test development requirements..."
    pip install -r ai_coding_agent/tests/requirements-dev.txt
fi

# Install pytest and pytest-asyncio explicitly to fix import errors
echo "📦 Installing pytest and pytest-asyncio..."
pip install pytest pytest-asyncio

# Setup git config if not already set
if [ -z "$(git config --global user.name)" ]; then
    echo "⚙️ Setting up git config..."
    git config --global user.name "Dev Container"
    git config --global user.email "devcontainer@example.com"
fi

# Create test directories if they don't exist
echo "📁 Creating test directories..."
mkdir -p logs/logs logs/reports

# Setup pyright launcher
mkdir -p venv/bin
cat > venv/bin/pyright << 'EOF'
#!/bin/bash
NODE_BIN=$(which node)
NODE_MODULES=$(npm root -g)
$NODE_BIN $NODE_MODULES/pyright/index.js "$@"
EOF
chmod +x venv/bin/pyright

# Set test environment variables
export PYTHONPATH="."
export PYTEST_ASYNCIO_MODE="auto"
export PYTHONWARNINGS="ignore::RuntimeWarning,ignore::DeprecationWarning"

echo "✅ Setup complete!"