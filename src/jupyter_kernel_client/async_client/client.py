"""
Asynchronous client module for interacting with Jupyter Enterprise Gateway kernels.
"""
import uuid
import json
import asyncio
import time
import logging
from typing import Optional, Dict, List, Any

import aiohttp
import websockets


class AsyncGatewayKernelSession:
    """
    Asynchronous managed session for interacting with a Jupyter Enterprise Gateway kernel.
    
    Features:
      - One-time kernel startup
      - Async listener for IOPub
      - Retry logic on startup & execute
      - Basic in-memory metrics
      - Clean teardown
      - Optional token-based auth
    """
    def __init__(
        self,
        gateway_http: str,
        gateway_ws: str,
        kernel_name: str,
        launch_env: Optional[Dict[str, str]] = None,
        startup_timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        auth_token: Optional[str] = None,
    ):
        self.gateway_http = gateway_http.rstrip('/')
        self.gateway_ws = gateway_ws.rstrip('/')
        self.kname = kernel_name
        self.launch_env = launch_env or {}
        self.startup_timeout = startup_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.auth_token = auth_token

        self.kernel_id: Optional[str] = None
        self.session_id = uuid.uuid4().hex
        self.ws = None

        # Metrics
        self.metrics = {
            'startup_times': [],
            'execute_times': [],
            'executions': 0,
        }

        # Async message handling
        self._msg_queue = asyncio.Queue()
        self._listener_task = None
        self._running = False
        logging.basicConfig(level=logging.INFO)
        self._http_session = None

    async def __aenter__(self):
        await self._start_kernel_with_retries()
        await self._connect_ws()
        self._start_listener()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown()

    async def _start_kernel_with_retries(self):
        """Start a kernel with retry logic."""
        self._http_session = aiohttp.ClientSession()
        for attempt in range(1, self.max_retries + 1):
            start = time.time()
            try:
                payload = {"name": self.kname}
                if self.launch_env:
                    payload['env'] = self.launch_env

                headers = {}
                if self.auth_token:
                    headers["Authorization"] = f"Token {self.auth_token}"

                async with self._http_session.post(
                    f"{self.gateway_http}/api/kernels",
                    json=payload,
                    headers=headers,
                    timeout=self.startup_timeout,
                ) as resp:
                    resp.raise_for_status()
                    response_data = await resp.json()
                    self.kernel_id = response_data['id']
                    duration = time.time() - start
                    self.metrics['startup_times'].append(duration)
                    logging.info(f"Kernel started in {duration:.2f}s (attempt {attempt})")
                    return
            except Exception as e:
                logging.warning(f"Startup attempt {attempt} failed: {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise

    async def _connect_ws(self):
        """Connect to kernel WebSocket."""
        url = (
            f"{self.gateway_ws}/api/kernels/{self.kernel_id}/channels"
            f"?session_id={self.session_id}"
        )
        
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Token {self.auth_token}"
            
        self.ws = await websockets.connect(url, extra_headers=headers)
        logging.info(f"WebSocket connected to {url}")

    def _start_listener(self):
        """Start the async WebSocket listener."""
        self._running = True
        self._listener_task = asyncio.create_task(self._listen())

    async def _listen(self):
        """Listen for WebSocket messages in a separate task."""
        while self._running:
            try:
                message = await self.ws.recv()
                msg = json.loads(message)
                await self._msg_queue.put(msg)
            except (websockets.exceptions.ConnectionClosed, 
                    websockets.exceptions.ConnectionClosedError):
                break
            except Exception as e:
                logging.error(f"Listener error: {e}")
                break

    async def execute(self, code: str, timeout: float = 10.0) -> str:
        """Execute code in the kernel with retry logic."""
        if not self.ws:
            raise RuntimeError("WebSocket not open")
            
        start = time.time()
        self.metrics['executions'] += 1
        msg_id = uuid.uuid4().hex
        
        header = {
            'msg_id': msg_id,
            'session': self.session_id,
            'msg_type': 'execute_request',
            'version': '5.0',
        }
        
        payload = {
            'header': header,
            'parent_header': {},
            'metadata': {},
            'channel': 'shell',
            'content': {'code': code, 'silent': False},
        }
        
        # Send with retry
        for attempt in range(1, self.max_retries + 1):
            try:
                await self.ws.send(json.dumps(payload))
                break
            except websockets.exceptions.WebSocketException as e:
                logging.warning(f"Send attempt {attempt} failed: {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise RuntimeError(f"Failed to send message after {self.max_retries} attempts")

        # Wait for responses
        output = []
        future_time = time.time() + timeout
        
        while time.time() < future_time:
            try:
                # Create a timeout for queue.get
                msg = await asyncio.wait_for(
                    self._msg_queue.get(), 
                    timeout=max(0.1, future_time - time.time())
                )
            except asyncio.TimeoutError:
                # No message received in time
                continue
                
            # Check if this is the response to our execute request
            if msg.get('parent_header', {}).get('msg_id') != msg_id:
                continue
                
            msg_type = msg['header']['msg_type']
            
            if msg_type == 'stream':
                output.append(msg['content']['text'])
            elif msg_type == 'execute_result':
                data = msg['content']['data']
                output.append(data.get('text/plain', ''))
                break
            elif msg_type == 'error':
                tb = '\n'.join(msg['content']['traceback'])
                raise RuntimeError(f"Kernel error:\n{tb}")
                
        duration = time.time() - start
        self.metrics['execute_times'].append(duration)
        logging.info(f"Execution took {duration:.2f}s")
        
        return ''.join(output)

    async def shutdown(self):
        """Clean up resources."""
        self._running = False
        
        # Cancel listener task
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        
        # Close WebSocket
        if self.ws:
            try:
                await self.ws.close()
            except:
                pass
        
        # Delete kernel
        if self.kernel_id and self._http_session:
            try:
                headers = {}
                if self.auth_token:
                    headers["Authorization"] = f"Token {self.auth_token}"
                    
                async with self._http_session.delete(
                    f"{self.gateway_http}/api/kernels/{self.kernel_id}",
                    headers=headers
                ) as resp:
                    pass
            except:
                pass
                
        # Close HTTP session
        if self._http_session:
            await self._http_session.close()


class AsyncKernelSessionPool:
    """
    A basic pool managing a fixed number of persistent asynchronous kernel sessions.
    """
    def __init__(self, size: int, **session_kwargs):
        self._pool: List[AsyncGatewayKernelSession] = []
        self._lock = asyncio.Lock()
        self._size = size
        self._session_kwargs = session_kwargs
        self._initialized = False
        
    async def initialize(self):
        """Initialize the pool with kernel sessions."""
        if self._initialized:
            return
            
        async with self._lock:
            for _ in range(self._size):
                sess = AsyncGatewayKernelSession(**self._session_kwargs)
                await sess.__aenter__()
                self._pool.append(sess)
            self._initialized = True
            
    async def acquire(self) -> AsyncGatewayKernelSession:
        """Get a session from the pool."""
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            if not self._pool:
                # Create a new session if pool is empty
                sess = AsyncGatewayKernelSession(**self._session_kwargs)
                await sess.__aenter__()
                return sess
            return self._pool.pop()
            
    async def release(self, sess: AsyncGatewayKernelSession):
        """Return a session to the pool."""
        async with self._lock:
            self._pool.append(sess)
            
    async def shutdown_all(self):
        """Clean up all sessions in the pool."""
        async with self._lock:
            for sess in self._pool:
                await sess.shutdown()
            self._pool.clear()
            self._initialized = False


# Example usage
async def example_usage():
    """Simple example of using the async client."""
    # Single session example
    async with AsyncGatewayKernelSession(
        "http://localhost:8889",
        "ws://localhost:8889",
        "sandbox-python"
    ) as session:
        result = await session.execute("print('Hello, async world!')")
        print(result)
        
    # Pool example
    pool = AsyncKernelSessionPool(2, 
        gateway_http="http://localhost:8889",
        gateway_ws="ws://localhost:8889",
        kernel_name="sandbox-python"
    )
    
    # Initialize pool
    await pool.initialize()
    
    # Use a session from the pool
    session = await pool.acquire()
    try:
        result = await session.execute("print('Hello from pool!')")
        print(result)
    finally:
        await pool.release(session)
        
    # Clean up
    await pool.shutdown_all() 