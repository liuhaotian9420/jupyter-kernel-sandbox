#!/usr/bin/env python3
"""
Example demonstrating the usage of Prometheus metrics with the Jupyter Kernel Client.
"""
import time
import threading
from prometheus_client import start_http_server
from jupyter_kernel_client import PrometheusGatewayKernelSession, PrometheusKernelSessionPool


def run_session_example():
    """Example of a single session with metrics."""
    print("=== Single Session with Prometheus Metrics ===")
    
    # Connection parameters
    gateway_http = "http://localhost:8889"
    gateway_ws = "ws://localhost:8889"
    # 默认内核为 python3（非自定义 sandbox 内核）
    kernel_name = "python3"
    
    print(f"Connecting to kernel: {kernel_name}")
    
    # Create a session with metrics
    session = PrometheusGatewayKernelSession(
        gateway_http,
        gateway_ws,
        kernel_name
    )
    
    print("Using session with Prometheus metrics...")
    with session:
        print(f"Connected to kernel with ID: {session.kernel_id}")
        
        # Execute a simple command
        result = session.execute("print('Hello, Prometheus!')")
        print(f"Result: {result}")
        
        # Execute multiple commands with different execution times
        print("Running commands with different execution times...")
        for i in range(1, 4):
            start = time.time()
            result = session.execute(f"import time; time.sleep({i*0.5}); '{i}'")
            print(f"Command {i} result: {result} (took {time.time() - start:.3f}s)")
        
        # Simulate an error to capture in metrics
        try:
            print("Simulating an error...")
            session.execute("raise ValueError('Test error')")
        except RuntimeError as e:
            print(f"Error captured and recorded in metrics: {type(e).__name__}")
    
    print("Session closed successfully and metrics updated")


def run_pool_example():
    """Example of using a kernel session pool with metrics."""
    print("\n=== Session Pool with Prometheus Metrics ===")
    
    # Connection parameters
    gateway_http = "http://localhost:8889"
    gateway_ws = "ws://localhost:8889"
    # 默认内核为 python3（非自定义 sandbox 内核）
    kernel_name = "python3"
    
    # Create a pool with metrics
    pool = PrometheusKernelSessionPool(
        2,
        gateway_http=gateway_http,
        gateway_ws=gateway_ws,
        kernel_name=kernel_name
    )
    
    # Create and start worker threads
    def worker(worker_id):
        print(f"Worker {worker_id} starting")
        session = pool.acquire()
        try:
            print(f"Worker {worker_id} running code")
            result = session.execute(f"'Worker {worker_id} completed'")
            print(f"Worker {worker_id} result: {result}")
            time.sleep(1)  # Simulate work
        finally:
            print(f"Worker {worker_id} returning session")
            pool.release(session)
    
    print("Starting worker threads...")
    threads = []
    for i in range(4):
        thread = threading.Thread(target=worker, args=(i+1,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print("All workers completed - pool metrics have been recorded")
    
    # Clean up
    print("Shutting down the pool...")
    pool.shutdown_all()
    print("Pool shutdown complete")


def main():
    """Run the metrics examples."""
    # Start Prometheus HTTP server
    metrics_port = 8000
    print(f"Starting Prometheus metrics server on port {metrics_port}...")
    start_http_server(metrics_port)
    print(f"Prometheus metrics server running at http://localhost:{metrics_port}")
    
    # Run examples
    run_session_example()
    run_pool_example()
    
    print("\n=== Prometheus Metrics ===")
    print(f"Metrics are available at http://localhost:{metrics_port}/metrics")
    print("Hit CTRL+C to exit, but leave this running to check metrics in a browser")
    print("Example metrics to look for:")
    print("  - kernel_startup_time_seconds")
    print("  - kernel_execution_time_seconds")
    print("  - kernel_execution_total")
    print("  - kernel_active")
    print("  - kernel_pool_size")
    print("  - kernel_retry_total")
    
    # Keep server running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server stopped")


if __name__ == "__main__":
    main() 