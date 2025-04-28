"""
Core client module for interacting with Jupyter Enterprise Gateway kernels.
"""
import uuid
import json
import threading
import queue
import time
import logging
from typing import Optional, Dict

import requests
from websocket import create_connection, WebSocketException


class GatewayKernelSession:
    """
    Managed session for interacting with a Jupyter Enterprise Gateway kernel.
    Features:
      - One-time kernel startup
      - Threaded listener for IOPub
      - Retry logic on startup & execute
      - Basic in-memory metrics
      - Clean teardown
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
    ):
        self.gateway_http = gateway_http.rstrip('/')
        self.gateway_ws = gateway_ws.rstrip('/')
        self.kname = kernel_name
        self.launch_env = launch_env or {}
        self.startup_timeout = startup_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.kernel_id: Optional[str] = None
        self.session_id = uuid.uuid4().hex
        self.ws = None

        # metrics
        self.metrics = {
            'startup_times': [],
            'execute_times': [],
            'executions': 0,
        }

        # internal queue and listener
        self._msg_queue = queue.Queue()
        self._listener = None
        self._running = False
        logging.basicConfig(level=logging.INFO)

    def __enter__(self):
        self._start_kernel_with_retries()
        self._connect_ws()
        self._start_listener()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def _start_kernel_with_retries(self):
        for attempt in range(1, self.max_retries + 1):
            start = time.time()
            try:
                payload = {"name": self.kname}
                if self.launch_env:
                    payload['env'] = self.launch_env
                resp = requests.post(
                    f"{self.gateway_http}/api/kernels",
                    json=payload,
                    timeout=self.startup_timeout,
                )
                resp.raise_for_status()
                self.kernel_id = resp.json()['id']
                duration = time.time() - start
                self.metrics['startup_times'].append(duration)
                logging.info(f"Kernel started in {duration:.2f}s (attempt {attempt})")
                return
            except Exception as e:
                logging.warning(f"Startup attempt {attempt} failed: {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    raise

    def _connect_ws(self):
        url = (
            f"{self.gateway_ws}/api/kernels/{self.kernel_id}/channels"
            f"?session_id={self.session_id}"
        )
        self.ws = create_connection(url)
        logging.info(f"WebSocket connected to {url}")

    def _start_listener(self):
        def _listen():
            while self._running:
                try:
                    msg = json.loads(self.ws.recv())
                    self._msg_queue.put(msg)
                except WebSocketException:
                    break
        self._running = True
        self._listener = threading.Thread(target=_listen, daemon=True)
        self._listener.start()

    def execute(self, code: str, timeout: float = 10.0) -> str:
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
        for attempt in range(1, self.max_retries + 1):
            try:
                self.ws.send(json.dumps(payload))
                break
            except WebSocketException as e:
                logging.warning(f"Send attempt {attempt} failed: {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    raise

        output = []
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                msg = self._msg_queue.get(timeout=deadline - time.time())
            except queue.Empty:
                break
            if msg.get('parent_header', {}).get('msg_id') != msg_id:
                continue
            mtype = msg['header']['msg_type']
            if mtype == 'stream':
                output.append(msg['content']['text'])
            elif mtype == 'execute_result':
                output.append(msg['content']['data'].get('text/plain', ''))
                break
            elif mtype == 'error':
                tb = '\n'.join(msg['content']['traceback'])
                raise RuntimeError(f"Kernel error:\n{tb}")
        duration = time.time() - start
        self.metrics['execute_times'].append(duration)
        logging.info(f"Execution took {duration:.2f}s")
        return ''.join(output)

    def shutdown(self):
        self._running = False
        if self.ws:
            try:
                self.ws.close()
            except: pass
        if self.kernel_id:
            try:
                requests.delete(f"{self.gateway_http}/api/kernels/{self.kernel_id}")
            except: pass


class KernelSessionPool:
    """
    A basic pool managing a fixed number of persistent kernel sessions.
    """
    def __init__(self, size, **session_kwargs):
        self._pool = []
        self._lock = threading.Lock()
        for _ in range(size):
            sess = GatewayKernelSession(**session_kwargs)
            sess.__enter__()
            self._pool.append(sess)

    def acquire(self):
        with self._lock:
            return self._pool.pop()

    def release(self, sess):
        with self._lock:
            self._pool.append(sess)

    def shutdown_all(self):
        with self._lock:
            for sess in self._pool:
                sess.shutdown()
            self._pool.clear() 