#!/usr/bin/env python3
"""
Example demonstrating the usage of the asynchronous Jupyter Kernel Client.
"""
import asyncio
from jupyter_kernel_client import AsyncGatewayKernelSession, AsyncKernelSessionPool


async def single_session_example():
    """Example of using a single async session."""
    print("=== Single Session Example ===")
    
    # Connection parameters
    gateway_http = "http://localhost:8889"
    gateway_ws = "ws://localhost:8889"
    # 默认内核为 python3（非自定义 sandbox 内核）
    kernel_name = "python3"
    
    print(f"Connecting to kernel: {kernel_name}")
    
    # Create and use a kernel session with async context manager
    async with AsyncGatewayKernelSession(
        gateway_http,
        gateway_ws,
        kernel_name
    ) as session:
        print(f"Connected to kernel with ID: {session.kernel_id}")
        
        # Execute a simple command
        result = await session.execute("print('Hello, async world!')")
        print(f"Result: {result}")
        
        # Execute code concurrently
        tasks = [
            session.execute("import time; time.sleep(1); '1'"),
            session.execute("import time; time.sleep(0.5); '2'"),
            session.execute("import time; time.sleep(0.2); '3'")
        ]
        
        # Wait for all tasks to complete
        print("Running concurrent code execution...")
        start_time = asyncio.get_event_loop().time()
        results = await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()
        
        print(f"Results: {results}")
        print(f"Concurrent execution time: {end_time - start_time:.3f} seconds")
        print("If this was sequential, it would take about 1.7 seconds")
    
    print("Session closed successfully")


async def pool_example():
    """Example of using a kernel session pool."""
    print("\n=== Session Pool Example ===")
    
    # Connection parameters
    gateway_http = "http://localhost:8889"
    gateway_ws = "ws://localhost:8889"
    # 默认内核为 python3（非自定义 sandbox 内核）
    kernel_name = "python3"
    
    # Create a pool with 2 kernels
    pool = AsyncKernelSessionPool(
        2,
        gateway_http=gateway_http,
        gateway_ws=gateway_ws,
        kernel_name=kernel_name
    )
    
    # Initialize the pool (starts the kernels)
    print("Initializing kernel pool...")
    await pool.initialize()
    print("Pool initialized")
    
    # Define a task that uses a session from the pool
    async def run_task(task_id):
        print(f"Task {task_id}: Getting session from pool")
        session = await pool.acquire()
        try:
            print(f"Task {task_id}: Running code")
            result = await session.execute(f"'Task {task_id} completed'")
            print(f"Task {task_id} result: {result}")
            
            # Simulate some work with the session
            await asyncio.sleep(1)
            return result
        finally:
            print(f"Task {task_id}: Returning session to pool")
            await pool.release(session)
    
    # Run multiple tasks concurrently
    print("Running multiple tasks using the pool...")
    start_time = asyncio.get_event_loop().time()
    results = await asyncio.gather(
        run_task(1),
        run_task(2),
        run_task(3),
        run_task(4)
    )
    end_time = asyncio.get_event_loop().time()
    
    print(f"All tasks completed with results: {results}")
    print(f"Total time with pool (4 tasks): {end_time - start_time:.3f} seconds")
    
    # Clean up
    print("Shutting down the pool...")
    await pool.shutdown_all()
    print("Pool shutdown complete")


async def main():
    """Run all examples."""
    await single_session_example()
    await pool_example()


if __name__ == "__main__":
    asyncio.run(main()) 