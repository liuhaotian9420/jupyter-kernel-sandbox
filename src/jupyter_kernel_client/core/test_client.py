import unittest
from unittest.mock import patch, MagicMock
import json
import pytest
import requests
from websocket import WebSocketException

from jupyter_kernel_client.core.client import GatewayKernelSession

class TestGatewayKernelSessionMock(unittest.TestCase):
    """Unit tests for GatewayKernelSession using mocks."""
    
    def setUp(self):
        self.gateway_http = "http://localhost:8889"
        self.gateway_ws = "ws://localhost:8889"
        self.kernel_name = "sandbox-python"
        self.session = None
    
    @patch('jupyter_kernel_client.core.client.requests.post')
    @patch('jupyter_kernel_client.core.client.create_connection')
    def test_start_kernel(self, mock_ws, mock_post):
        """Test kernel startup with mocked responses."""
        # Configure mocks
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "test-kernel-id"}
        mock_post.return_value = mock_response
        
        # Create session and test kernel start
        session = GatewayKernelSession(
            self.gateway_http, 
            self.gateway_ws,
            self.kernel_name
        )
        session._start_kernel_with_retries()
        
        # Assertions
        mock_post.assert_called_once()
        self.assertEqual(session.kernel_id, "test-kernel-id")
    
    @patch('jupyter_kernel_client.core.client.requests.post')
    @patch('jupyter_kernel_client.core.client.create_connection')
    @patch('jupyter_kernel_client.core.client.requests.delete')
    def test_context_manager(self, mock_delete, mock_ws, mock_post):
        """Test session lifecycle using context manager."""
        # Configure mocks
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "test-kernel-id"}
        mock_post.return_value = mock_response
        mock_ws.return_value = MagicMock()
        
        # Use context manager
        with GatewayKernelSession(
            self.gateway_http, 
            self.gateway_ws,
            self.kernel_name
        ) as session:
            self.assertEqual(session.kernel_id, "test-kernel-id")
            self.assertTrue(session._running)
        
        # Verify shutdown was called
        mock_delete.assert_called_once()
    
    @patch('jupyter_kernel_client.core.client.requests.post')
    @patch('jupyter_kernel_client.core.client.create_connection')
    def test_execute_success(self, mock_ws, mock_post):
        """Test code execution with successful result."""
        # Configure mocks
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "test-kernel-id"}
        mock_post.return_value = mock_response
        
        mock_socket = MagicMock()
        # Configure the websocket to return a valid result message
        def mock_recv():
            return json.dumps({
                "header": {"msg_type": "execute_result"},
                "parent_header": {"msg_id": "any-id"},  # Will be replaced in the test
                "content": {"data": {"text/plain": "Hello World"}}
            })
        mock_socket.recv = mock_recv
        mock_ws.return_value = mock_socket
        
        # Create session and override the queue behavior
        session = GatewayKernelSession(
            self.gateway_http, 
            self.gateway_ws,
            self.kernel_name
        )
        session._start_kernel_with_retries()
        session._connect_ws()
        
        # Patch the queue to insert our mock message
        def put_mock_msg(msg_id):
            session._msg_queue.put({
                "header": {"msg_type": "execute_result"},
                "parent_header": {"msg_id": msg_id},
                "content": {"data": {"text/plain": "Hello World"}}
            })
        
        with patch.object(session.ws, 'send', side_effect=lambda msg: put_mock_msg(json.loads(msg)["header"]["msg_id"])):
            result = session.execute("print('Hello World')", timeout=1)
            self.assertEqual(result, "Hello World")


@pytest.mark.integration
class TestGatewayKernelSessionIntegration:
    """Integration tests that connect to a real Enterprise Gateway."""
    
    @pytest.fixture(scope="module")
    def gateway_config(self):
        """Fixture for gateway connection details."""
        return {
            "http": "http://localhost:8889",
            "ws": "ws://localhost:8889",
            "kernel_name": "sandbox-python"
        }
    
    @pytest.fixture(autouse=True)
    def check_gateway_available(self, gateway_config):
        """Skip tests if gateway is not available."""
        try:
            requests.get(f"{gateway_config['http']}/api", timeout=2)
        except requests.exceptions.RequestException:
            pytest.skip("Enterprise Gateway not available")
    
    def test_kernel_lifecycle(self, gateway_config):
        """Test full kernel lifecycle: start, execute, shutdown."""
        with GatewayKernelSession(
            gateway_config["http"],
            gateway_config["ws"],
            gateway_config["kernel_name"]
        ) as session:
            assert session.kernel_id is not None
            
            # Simple code execution
            result = session.execute("2 + 2")
            assert "4" in result
            
            # Test environment variables
            result = session.execute("import os; os.environ.get('FILE_SERVER_URL')")
            assert "file-server" in result.lower() or "8080" in result
    
    def test_error_handling(self, gateway_config):
        """Test error handling in code execution."""
        with GatewayKernelSession(
            gateway_config["http"],
            gateway_config["ws"],
            gateway_config["kernel_name"]
        ) as session:
            with pytest.raises(RuntimeError) as excinfo:
                session.execute("raise ValueError('Test error')")
            assert "ValueError" in str(excinfo.value)


if __name__ == "__main__":
    # Run unit tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
    # To run integration tests:
    # pytest -xvs src/jupyter_kernel_client/core/test_client.py::TestGatewayKernelSessionIntegration 