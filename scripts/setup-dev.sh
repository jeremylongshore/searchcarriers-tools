#!/usr/bin/env bash
# SearchCarriers Dev Setup
# Goal: clone -> working in < 2 minutes
set -euo pipefail

echo "SearchCarriers Dev Setup"
echo "========================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."
for cmd in python3 pip git; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "ERROR: $cmd is required but not installed"
        exit 1
    fi
done
echo "  python3: $(python3 --version)"
echo "  pip: $(pip --version | cut -d' ' -f1-2)"
echo "  git: $(git --version)"
echo ""

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists"
fi

# Install dependencies using venv pip directly
echo "Installing dependencies..."
.venv/bin/pip install -e ".[dev]" --quiet

# Check for API key
echo ""
if [ -n "${SEARCHCARRIERS_API_KEY:-}" ]; then
    echo "API key: configured"
else
    echo "API key: NOT SET"
    echo "  Set SEARCHCARRIERS_API_KEY in your environment or .env file"
    echo "  Get your key at https://searchcarriers.com/settings/api-tokens"
fi

# Run validation
echo ""
echo "Running validation..."
chmod +x scripts/validate.sh
if ./scripts/validate.sh; then
    echo ""
    echo "========================"
    echo "Setup complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Set SEARCHCARRIERS_API_KEY if not already done"
    echo "  2. Run: pytest -v"
    echo "  3. Try: ./scripts/validate.sh --verbose"
    echo ""
    echo "Activate your venv: source .venv/bin/activate"
else
    echo ""
    echo "Validation found issues - see above"
    exit 1
fi
