"""
Jupyter Kernel Client - A secure and extensible client for Jupyter Enterprise Gateway kernels.

This package provides a client for interacting with Jupyter kernels managed by
Jupyter Enterprise Gateway, with support for containerized execution.

Basic usage:
    from jupyter_kernel_client import GatewayKernelSession

    with GatewayKernelSession(
        "http://localhost:8889", 
        "ws://localhost:8889",
        "python3"
    ) as session:
        result = session.execute("print('Hello, World!')")
        print(result)
"""

__version__ = "0.1.0"

# Core client
from jupyter_kernel_client.core.client import GatewayKernelSession, KernelSessionPool

# Convenience imports for optional components
try:
    from jupyter_kernel_client.async_client.client import AsyncGatewayKernelSession, AsyncKernelSessionPool
except ImportError:
    # async dependencies not installed
    pass

try:
    from jupyter_kernel_client.metrics.prometheus import (
        PrometheusGatewayKernelSession,
        PrometheusKernelSessionPool
    )
except ImportError:
    # prometheus dependencies not installed
    pass

try:
    from jupyter_kernel_client.auth.auth_client import (
        AuthenticatedKernelSession,
        KernelAuthManager
    )
except ImportError:
    # auth dependencies not installed
    pass

# Convenient exports
__all__ = [
    "GatewayKernelSession",
    "KernelSessionPool",
] 