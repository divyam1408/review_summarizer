#!/bin/bash

# Define the environment directory name
ENV_DIR="venv"

# Check if python3 is installed
if ! command -v python3 &> /dev/null
then
    echo "Python3 could not be found. Please install python3 first."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$ENV_DIR" ]; then
    echo "Creating virtual environment in ./$ENV_DIR..."
    python3 -m venv $ENV_DIR
else
    echo "Virtual environment already exists in ./$ENV_DIR."
fi

# Activate the virtual environment
source $ENV_DIR/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "Installing requirements from requirements.txt..."
    pip install -r requirements.txt
    echo "Environment setup complete!"
else
    echo "requirements.txt not found!"
fi

echo ""
echo "To activate the environment, run:"
echo "source $ENV_DIR/bin/activate"
