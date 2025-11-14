#!/bin/bash
# Quick start script for Linux/Mac

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run application
python -m app.main
