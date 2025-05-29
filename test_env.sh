#!/bin/bash
# Setup a test environment for the Jupyter Kernel Client
# This script:
# 1. Installs the client package in development mode
# 2. Starts the Docker environment if not already running
# 3. Runs basic connectivity tests

set -e  # Exit on error

# Install the package with test dependencies
echo "Installing jupyter-kernel-client with test dependencies..."
pip install -e ".[dev]"

# Check if Docker environment is running
echo "Checking if Docker environment is running..."
GATEWAY_RUNNING=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8889/api || echo "0")

if [ "$GATEWAY_RUNNING" != "200" ]; then
    echo "Starting Docker environment..."
    docker-compose up -d
    
    # Wait for services to be ready
    echo "Waiting for services to start..."
    for i in {1..30}; do
        echo -n "."
        GATEWAY_RUNNING=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8889/api || echo "0")
        if [ "$GATEWAY_RUNNING" == "200" ]; then
            echo "Gateway is ready!"
            break
        fi
        sleep 1
    done
    
    if [ "$GATEWAY_RUNNING" != "200" ]; then
        echo "Error: Could not connect to Gateway"
        exit 1
    fi
else
    echo "Docker environment is already running"
fi

# Run basic connectivity test
echo "Running basic connectivity test..."
python -c "
from jupyter_kernel_client import GatewayKernelSession
try:
    with GatewayKernelSession('http://localhost:8889', 'ws://localhost:8889', 'python3') as session:
        result = session.execute('2+2')
        print(f'Test success! Result: {result}')
except Exception as e:
    print(f'Test failed: {e}')
    exit(1)
"

echo "Test environment is ready!"
echo "Run tests with: python -m pytest tests/" 