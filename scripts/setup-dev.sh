#!/bin/bash
# Setup script for local Airflow development environment using Astro CLI
# Run from project root: ./scripts/setup-dev.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEV_DIR="$PROJECT_ROOT/dev"

echo "🚀 Setting up Mailtrap Airflow Provider dev environment..."
echo "   Project root: $PROJECT_ROOT"
echo "   Dev directory: $DEV_DIR"

# Check if astro CLI is installed
if ! command -v astro &> /dev/null; then
    echo "❌ Astro CLI not found. Install it with: brew install astro"
    exit 1
fi

echo "✅ Astro CLI found: $(astro version)"

# Create dev directory if it doesn't exist
if [ ! -d "$DEV_DIR" ]; then
    echo "📁 Creating dev directory..."
    mkdir -p "$DEV_DIR"
    cd "$DEV_DIR"

    echo "🔧 Initializing Astro project..."
    astro dev init
else
    echo "📁 Dev directory already exists"
    cd "$DEV_DIR"
fi

# Create custom Dockerfile that installs our local provider
echo "📝 Creating custom Dockerfile..."
cat > "$DEV_DIR/Dockerfile" << 'EOF'
FROM quay.io/astronomer/astro-runtime:12.4.0

# Copy the provider source code into the container
COPY --chown=astro:0 provider-src /usr/local/airflow/provider-src

# Install the provider in editable mode
RUN pip install --no-cache-dir -e /usr/local/airflow/provider-src
EOF

# Create a symlink to provider source (Astro will COPY this during build)
echo "🔗 Linking provider source..."
rm -rf "$DEV_DIR/provider-src"
# We copy instead of symlink because Docker COPY doesn't follow symlinks well
cp -r "$PROJECT_ROOT/mailtrap_provider" "$DEV_DIR/provider-src/mailtrap_provider" 2>/dev/null || true
cp "$PROJECT_ROOT/pyproject.toml" "$DEV_DIR/provider-src/" 2>/dev/null || true

# Create the provider-src directory structure if provider doesn't exist yet
if [ ! -d "$DEV_DIR/provider-src/mailtrap_provider" ]; then
    echo "⚠️  Provider not found yet - creating placeholder..."
    mkdir -p "$DEV_DIR/provider-src/mailtrap_provider"

    # Create minimal pyproject.toml for initial setup
    cat > "$DEV_DIR/provider-src/pyproject.toml" << 'PYPROJECT'
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "airflow-provider-mailtrap"
version = "0.0.1"
description = "Apache Airflow provider for Mailtrap"
requires-python = ">=3.9"
dependencies = [
    "apache-airflow>=2.4",
    "mailtrap"
]

[project.entry-points.apache_airflow_provider]
provider_info = "mailtrap_provider.__init__:get_provider_info"

[tool.setuptools.packages.find]
exclude = ["tests*"]
PYPROJECT

    # Create minimal __init__.py
    cat > "$DEV_DIR/provider-src/mailtrap_provider/__init__.py" << 'INITPY'
__version__ = "0.0.1"

def get_provider_info():
    return {
        "package-name": "airflow-provider-mailtrap",
        "name": "Mailtrap",
        "description": "Send emails via Mailtrap.io",
        "connection-types": [{
            "connection-type": "mailtrap",
            "hook-class-name": "mailtrap_provider.hooks.mailtrap.MailtrapHook"
        }],
        "versions": [__version__],
    }
INITPY
fi

# Create example DAG symlink in dags folder
echo "🔗 Linking example DAGs..."
mkdir -p "$DEV_DIR/dags"
# We'll create a simple test DAG for now
cat > "$DEV_DIR/dags/test_mailtrap.py" << 'DAGPY'
"""
Test DAG for Mailtrap provider.
Set the Airflow Variable 'test_email_recipient' before running.
"""
from datetime import datetime
from airflow.decorators import dag, task
from airflow.models import Variable

@dag(
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["mailtrap", "test"],
)
def test_mailtrap_provider():
    """Test DAG to verify Mailtrap provider installation."""

    @task
    def check_provider():
        """Check if provider is installed correctly."""
        from mailtrap_provider import get_provider_info
        info = get_provider_info()
        print(f"✅ Provider installed: {info['name']} v{info['versions'][0]}")
        return info

    check_provider()

test_mailtrap_provider()
DAGPY

# Update requirements.txt to include mailtrap SDK
echo "📝 Updating requirements.txt..."
if ! grep -q "mailtrap" "$DEV_DIR/requirements.txt" 2>/dev/null; then
    echo "mailtrap" >> "$DEV_DIR/requirements.txt"
fi

# Enable connection testing in Airflow (disabled by default for security)
echo "📝 Configuring .env..."
if ! grep -q "AIRFLOW__CORE__TEST_CONNECTION" "$DEV_DIR/.env" 2>/dev/null; then
    echo "AIRFLOW__CORE__TEST_CONNECTION=Enabled" >> "$DEV_DIR/.env"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. cd dev"
echo "   2. astro dev start"
echo "   3. Open http://localhost:8080 (admin/admin)"
echo "   4. Run the 'test_mailtrap_provider' DAG to verify installation"
echo ""
echo "🔄 To rebuild after code changes:"
echo "   cd dev && astro dev restart"
echo ""
echo "📦 To sync provider code changes:"
echo "   ./scripts/sync-provider.sh"

