"""
Prometheus metrics integration for the Jupyter Kernel Client.
"""
import time
import logging
from typing import Dict, Any, Optional

from prometheus_client import Counter, Histogram, Gauge
from jupyter_kernel_client.core.client import GatewayKernelSession, KernelSessionPool

# Setup Prometheus metrics
KERNEL_STARTUP_TIME = Histogram(
    'kernel_startup_time_seconds', 
    'Time taken to start a kernel',
    ['kernel_type']
)

KERNEL_EXECUTION_TIME = Histogram(
    'kernel_execution_time_seconds', 
    'Time taken to execute code in a kernel',
    ['kernel_type']
)

KERNEL_EXECUTION_COUNT = Counter(
    'kernel_execution_total', 
    'Total number of code executions',
    ['kernel_type', 'status']
)

KERNEL_ACTIVE = Gauge(
    'kernel_active', 
    'Number of currently active kernels',
    ['kernel_type']
)

KERNEL_POOL_SIZE = Gauge(
    'kernel_pool_size', 
    'Current size of the kernel pool',
    ['kernel_type']
)

KERNEL_RETRY_COUNT = Counter(
    'kernel_retry_total', 
    'Total number of retries',
    ['kernel_type', 'operation']
)


class MetricsCollector:
    """Base class for collecting and reporting metrics."""
    
    def __init__(self, kernel_type: str = "python3"):
        self.kernel_type = kernel_type
        
    def record_startup_time(self, duration: float):
        """Record kernel startup time."""
        KERNEL_STARTUP_TIME.labels(kernel_type=self.kernel_type).observe(duration)
        
    def record_execution_time(self, duration: float):
        """Record code execution time."""
        KERNEL_EXECUTION_TIME.labels(kernel_type=self.kernel_type).observe(duration)
        
    def increment_execution_count(self, status: str = "success"):
        """Increment the execution counter."""
        KERNEL_EXECUTION_COUNT.labels(kernel_type=self.kernel_type, status=status).inc()
        
    def set_active_kernels(self, count: int):
        """Set the number of active kernels."""
        KERNEL_ACTIVE.labels(kernel_type=self.kernel_type).set(count)
        
    def set_pool_size(self, size: int):
        """Set the current pool size."""
        KERNEL_POOL_SIZE.labels(kernel_type=self.kernel_type).set(size)
        
    def increment_retry_count(self, operation: str):
        """Increment the retry counter for a specific operation."""
        KERNEL_RETRY_COUNT.labels(kernel_type=self.kernel_type, operation=operation).inc()
        
    def export_metrics(self) -> Dict[str, Any]:
        """Export metrics in a dictionary format."""
        return {
            "kernel_type": self.kernel_type,
            "metrics": {
                "startup_times": KERNEL_STARTUP_TIME.labels(kernel_type=self.kernel_type)._sum.get(),
                "execution_times": KERNEL_EXECUTION_TIME.labels(kernel_type=self.kernel_type)._sum.get(),
                "executions": {
                    "success": KERNEL_EXECUTION_COUNT.labels(kernel_type=self.kernel_type, status="success")._value.get(),
                    "error": KERNEL_EXECUTION_COUNT.labels(kernel_type=self.kernel_type, status="error")._value.get(),
                },
                "active_kernels": KERNEL_ACTIVE.labels(kernel_type=self.kernel_type)._value,
                "pool_size": KERNEL_POOL_SIZE.labels(kernel_type=self.kernel_type)._value,
                "retries": {
                    "startup": KERNEL_RETRY_COUNT.labels(kernel_type=self.kernel_type, operation="startup")._value.get(),
                    "execute": KERNEL_RETRY_COUNT.labels(kernel_type=self.kernel_type, operation="execute")._value.get(),
                }
            }
        }


class PrometheusKernelSessionMixin:
    """
    Mixin to add Prometheus metrics to GatewayKernelSession.
    Add this to your GatewayKernelSession class to enable metrics collection.
    """
    
    def __init__(self, *args, **kwargs):
        self.metrics_collector = MetricsCollector(kwargs.get('kernel_name', 'python3'))
        # Call the parent class's __init__
        super().__init__(*args, **kwargs)
        
    def _start_kernel_with_retries(self):
        """Override to add metrics for kernel startup."""
        start = time.time()
        try:
            super()._start_kernel_with_retries()
            duration = time.time() - start
            self.metrics_collector.record_startup_time(duration)
            self.metrics_collector.set_active_kernels(1)
            return True
        except Exception as e:
            self.metrics_collector.increment_retry_count("startup")
            raise
            
    def execute(self, code, timeout=10):
        """Override to add metrics for code execution."""
        start = time.time()
        try:
            result = super().execute(code, timeout)
            duration = time.time() - start
            self.metrics_collector.record_execution_time(duration)
            self.metrics_collector.increment_execution_count("success")
            return result
        except Exception as e:
            self.metrics_collector.increment_execution_count("error")
            self.metrics_collector.increment_retry_count("execute")
            raise
            
    def shutdown(self):
        """Override to update active kernel count."""
        super().shutdown()
        self.metrics_collector.set_active_kernels(0)
        

class PrometheusKernelPoolMixin:
    """
    Mixin to add Prometheus metrics to KernelSessionPool.
    Add this to your KernelSessionPool class to enable metrics collection.
    """
    
    def __init__(self, size, **session_kwargs):
        self.metrics_collector = MetricsCollector(session_kwargs.get('kernel_name', 'python3'))
        # Call the parent class's __init__
        super().__init__(size, **session_kwargs)
        self.metrics_collector.set_pool_size(size)
        
    def acquire(self):
        """Override to update pool size metric."""
        session = super().acquire()
        self.metrics_collector.set_pool_size(len(self._pool))
        return session
        
    def release(self, sess):
        """Override to update pool size metric."""
        super().release(sess)
        self.metrics_collector.set_pool_size(len(self._pool))


class PrometheusGatewayKernelSession(PrometheusKernelSessionMixin, GatewayKernelSession):
    """GatewayKernelSession with Prometheus metrics."""
    pass


class PrometheusKernelSessionPool(PrometheusKernelPoolMixin, KernelSessionPool):
    """KernelSessionPool with Prometheus metrics."""
    pass


# Usage example
def example_usage():
    """Simple example of using the metrics-enhanced client."""
    from prometheus_client import start_http_server
    
    # Start Prometheus HTTP server
    start_http_server(8000)
    print("Prometheus metrics server started at http://localhost:8000")
      # Create a session with metrics
    session = PrometheusGatewayKernelSession(
        "http://localhost:8889",
        "ws://localhost:8889",
        "python3"
    )
    
    # Use the session
    with session:
        result = session.execute("print('Hello, Prometheus!')")
        print(result)
        
        # Simulate an error
        try:
            session.execute("raise ValueError('Test error')")
        except RuntimeError:
            print("Error captured and metrics recorded")
              # Create a pool with metrics
    pool = PrometheusKernelSessionPool(
        2,
        gateway_http="http://localhost:8889",
        gateway_ws="ws://localhost:8889",
        kernel_name="python3"
    )
    
    # Use the pool
    session = pool.acquire()
    try:
        result = session.execute("print('Hello from monitored pool!')")
        print(result)
    finally:
        pool.release(session)
        
    # Clean up
    pool.shutdown_all()
    
    print("Metrics have been recorded. Check http://localhost:8000/metrics") 