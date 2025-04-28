"""
Main test runner for Jupyter Kernel Client package.
This file runs tests for all modules.
"""
import unittest
import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import tests
from jupyter_kernel_client.core.test_client import TestGatewayKernelSessionMock, TestGatewayKernelSessionIntegration


class TestPackageImports(unittest.TestCase):
    """Test package imports and structure."""
    
    def test_core_imports(self):
        """Test core package imports."""
        from jupyter_kernel_client import GatewayKernelSession, KernelSessionPool
        self.assertTrue(hasattr(GatewayKernelSession, '__enter__'))
        self.assertTrue(hasattr(KernelSessionPool, 'acquire'))


def run_unit_tests():
    """Run all unit tests."""
    unittest.main(argv=['first-arg-is-ignored'], exit=False)


def run_integration_tests():
    """Run integration tests."""
    pytest.main(['-xvs', 'tests/test_kernel_client.py::run_integration_tests'])


def integration_test_suite():
    """Integration test suite to be run by pytest."""
    from jupyter_kernel_client.core.test_client import TestGatewayKernelSessionIntegration
    # Add other integration test classes here as needed
    # from jupyter_kernel_client.async_client.test_client import TestAsyncGatewayKernelSessionIntegration
    # from jupyter_kernel_client.auth.test_auth_client import TestAuthenticatedKernelSessionIntegration
    # from jupyter_kernel_client.metrics.test_prometheus import TestPrometheusMetricsIntegration


if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run tests for Jupyter Kernel Client')
    parser.add_argument('--integration', action='store_true', help='Run integration tests')
    parser.add_argument('--unit', action='store_true', help='Run unit tests')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    args = parser.parse_args()
    
    # Run tests
    if args.integration or args.all:
        print("Running integration tests...")
        run_integration_tests()
    
    if args.unit or args.all or (not args.integration and not args.unit):
        print("Running unit tests...")
        run_unit_tests() 