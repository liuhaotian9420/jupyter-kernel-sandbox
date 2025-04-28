"""
Pytest configuration file.
"""
import sys
import os
import pytest

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Common fixtures for integration tests
@pytest.fixture(scope="session")
def gateway_config():
    """Gateway connection configuration."""
    return {
        "http": "http://localhost:8889",
        "ws": "ws://localhost:8889",
        "kernel_name": "sandbox-python"
    }

@pytest.fixture(scope="session")
def file_server_config():
    """File server connection configuration."""
    return {
        "url": "http://localhost:8080",
        "auth_token": "test-token"
    } 