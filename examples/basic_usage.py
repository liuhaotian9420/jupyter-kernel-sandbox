#!/usr/bin/env python3
"""
Basic example demonstrating the usage of the Jupyter Kernel Client.
"""
from jupyter_kernel_client import GatewayKernelSession


def main():
    """
    Basic demonstration of the Jupyter Kernel Client.
    """
    # Connection parameters
    gateway_http = "http://localhost:8889"
    gateway_ws = "ws://localhost:8889"
    kernel_name = "sandbox-python"
    
    print(f"Connecting to kernel: {kernel_name}")
    print(f"Gateway: {gateway_http}")
    
    # Create and use a kernel session
    with GatewayKernelSession(
        gateway_http,
        gateway_ws,
        kernel_name
    ) as session:
        print(f"Connected to kernel with ID: {session.kernel_id}")
        
        # Execute a simple command
        result = session.execute("print('Hello, world!')")
        print(f"Result: {result}")
        
        # Execute code that returns a value
        result = session.execute("2 + 2")
        print(f"2 + 2 = {result}")
        
        # Execute multiple lines of code
        code = """
import numpy as np
import matplotlib.pyplot as plt

# Create some data
x = np.linspace(0, 10, 100)
y = np.sin(x)

# Return the result
f'Created array with shape {y.shape}'
"""
        result = session.execute(code)
        print(f"Result: {result}")
        
        # Write to a file in the shared directory
        write_code = """
with open('/data/shared/example_output.txt', 'w') as f:
    f.write('This file was created by the kernel!')
    
'File created successfully'
"""
        result = session.execute(write_code)
        print(f"File write result: {result}")
        
        # Error handling demonstration
        try:
            session.execute("1/0")  # This will raise a ZeroDivisionError
        except RuntimeError as e:
            print(f"Caught exception from kernel: {type(e).__name__}")
            print(f"Error message: {str(e)[:100]}...")
    
    print("Session closed successfully")
    
    # Display metric information
    print("\nMetrics:")
    print(f"Executions: {session.metrics['executions']}")
    print(f"Average execution time: {sum(session.metrics['execute_times']) / len(session.metrics['execute_times']):.3f} seconds")
    print(f"Startup time: {session.metrics['startup_times'][0]:.3f} seconds")


if __name__ == "__main__":
    main() 