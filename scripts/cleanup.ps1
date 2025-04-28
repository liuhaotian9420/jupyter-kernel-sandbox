# PowerShell cleanup script to remove old files that have been migrated to the new package structure

# List of old files to remove
$OldFiles = @(
    "kernel_client.py",
    "kernel_client_async.py",
    "kernel_client_auth.py",
    "kernel_client_metrics.py",
    "test_client_example.py",
    "test_kernel_client.py"
)

# Verify files were migrated before deleting
Write-Host "Verifying package structure before cleanup..."
if (-Not (Test-Path "src/jupyter_kernel_client/core/client.py")) {
    Write-Host "Error: Core client file not found. Aborting cleanup." -ForegroundColor Red
    exit 1
}

if (-Not (Test-Path "src/jupyter_kernel_client/async_client/client.py")) {
    Write-Host "Error: Async client file not found. Aborting cleanup." -ForegroundColor Red
    exit 1
}

if (-Not (Test-Path "src/jupyter_kernel_client/auth/auth_client.py")) {
    Write-Host "Error: Auth client file not found. Aborting cleanup." -ForegroundColor Red
    exit 1
}

if (-Not (Test-Path "src/jupyter_kernel_client/metrics/prometheus.py")) {
    Write-Host "Error: Metrics file not found. Aborting cleanup." -ForegroundColor Red
    exit 1
}

if (-Not (Test-Path "tests/test_kernel_client.py")) {
    Write-Host "Error: Test file not found. Aborting cleanup." -ForegroundColor Red
    exit 1
}

# Delete old files
Write-Host "Removing old files..."
foreach ($file in $OldFiles) {
    if (Test-Path $file) {
        Write-Host "Removing $file"
        Remove-Item $file
    } else {
        Write-Host "$file already removed"
    }
}

Write-Host "Cleanup complete." -ForegroundColor Green 