#!/bin/bash
# Cleanup script to remove old files that have been migrated to the new package structure

# List of old files to remove
OLD_FILES=(
  "kernel_client.py"
  "kernel_client_async.py"
  "kernel_client_auth.py"
  "kernel_client_metrics.py"
  "test_client_example.py"
  "test_kernel_client.py"
)

# Verify files were migrated before deleting
echo "Verifying package structure before cleanup..."
if [ ! -f "src/jupyter_kernel_client/core/client.py" ]; then
  echo "Error: Core client file not found. Aborting cleanup."
  exit 1
fi

if [ ! -f "src/jupyter_kernel_client/async_client/client.py" ]; then
  echo "Error: Async client file not found. Aborting cleanup."
  exit 1
fi

if [ ! -f "src/jupyter_kernel_client/auth/auth_client.py" ]; then
  echo "Error: Auth client file not found. Aborting cleanup."
  exit 1
fi

if [ ! -f "src/jupyter_kernel_client/metrics/prometheus.py" ]; then
  echo "Error: Metrics file not found. Aborting cleanup."
  exit 1
fi

if [ ! -f "tests/test_kernel_client.py" ]; then
  echo "Error: Test file not found. Aborting cleanup."
  exit 1
fi

# Delete old files
echo "Removing old files..."
for file in "${OLD_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "Removing $file"
    rm "$file"
  else
    echo "$file already removed"
  fi
done

echo "Cleanup complete." 