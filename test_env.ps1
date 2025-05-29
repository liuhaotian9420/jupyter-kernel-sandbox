# PowerShell script to setup a test environment for the Jupyter Kernel Client
# This script:
# 1. Installs the client package in development mode
# 2. Starts the Docker environment if not already running
# 3. Runs basic connectivity tests

# Install the package with test dependencies
Write-Host "Installing jupyter-kernel-client with test dependencies..."
pip install -e ".[dev]"

# Check if Docker environment is running
Write-Host "Checking if Docker environment is running..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8889/api" -Method GET -UseBasicParsing -ErrorAction SilentlyContinue
    $gatewayRunning = $response.StatusCode -eq 200
} catch {
    $gatewayRunning = $false
}

if (-Not $gatewayRunning) {
    Write-Host "Starting Docker environment..."
    docker-compose up -d
    
    # Wait for services to be ready
    Write-Host "Waiting for services to start..." -NoNewline
    $retries = 30
    for ($i = 1; $i -le $retries; $i++) {
        Write-Host "." -NoNewline
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8889/api" -Method GET -UseBasicParsing -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Host "`nGateway is ready!"
                break
            }
        } catch {
            # Gateway not ready yet
        }
        Start-Sleep -Seconds 1
    }
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8889/api" -Method GET -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -ne 200) {
            Write-Host "`nError: Could not connect to Gateway" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "`nError: Could not connect to Gateway" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Docker environment is already running"
}

# Run basic connectivity test
Write-Host "Running basic connectivity test..."
python -c @"
from jupyter_kernel_client import GatewayKernelSession
try:
    with GatewayKernelSession('http://localhost:8889', 'ws://localhost:8889', 'python3') as session:
        result = session.execute('2+2')
        print(f'Test success! Result: {result}')
except Exception as e:
    print(f'Test failed: {e}')
    exit(1)
"@

Write-Host "Test environment is ready!" -ForegroundColor Green
Write-Host "Run tests with: python -m pytest tests/" 