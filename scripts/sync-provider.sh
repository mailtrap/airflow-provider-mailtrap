#!/bin/bash
# Sync provider code to dev environment and restart
# Run from project root: ./scripts/sync-provider.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEV_DIR="$PROJECT_ROOT/dev"

echo "🔄 Syncing provider code to dev environment..."

# Check if dev directory exists
if [ ! -d "$DEV_DIR" ]; then
    echo "❌ Dev directory not found. Run ./scripts/setup-dev.sh first"
    exit 1
fi

# Sync provider source
echo "📦 Copying provider source..."
rm -rf "$DEV_DIR/provider-src/mailtrap_provider"
cp -r "$PROJECT_ROOT/mailtrap_provider" "$DEV_DIR/provider-src/mailtrap_provider"
cp "$PROJECT_ROOT/pyproject.toml" "$DEV_DIR/provider-src/"

# Sync example DAGs if they exist
if [ -d "$PROJECT_ROOT/mailtrap_provider/example_dags" ]; then
    echo "📋 Syncing example DAGs..."
    cp "$PROJECT_ROOT/mailtrap_provider/example_dags/"*.py "$DEV_DIR/dags/" 2>/dev/null || true
fi

echo "✅ Provider code synced!"
echo ""
echo "🔄 Rebuilding Airflow containers..."
cd "$DEV_DIR"
astro dev restart

echo ""
echo "✅ Done! Airflow is restarting with updated provider code."
echo "   Open http://localhost:8080 to test"


