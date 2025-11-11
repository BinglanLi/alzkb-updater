#!/bin/bash
# Simple script to run AlzKB updater

echo "================================"
echo "AlzKB Updater"
echo "================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Run the updater
echo ""
echo "Running AlzKB updater..."
echo ""
cd src
python main.py "$@"

echo ""
echo "================================"
echo "Update complete!"
echo "================================"
