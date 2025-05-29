"""
Authentication module for interacting with the FastAPI-based file server.
"""
import os
import requests
from typing import Optional, Dict, Any
from urllib.parse import urljoin

from jupyter_kernel_client.core.client import GatewayKernelSession


class KernelAuthManager:
    """
    Manages authentication between kernel clients and the FastAPI file server.
    
    Features:
    - Token acquisition from the file server
    - Token validation
    - Environment variable integration for kernels
    """
    
    def __init__(
        self, 
        file_server_url: str = "http://file-server:8080", 
        auth_token: Optional[str] = None
    ):
        self.file_server_url = file_server_url.rstrip('/')
        self._auth_token = auth_token or os.environ.get("WRITE_TOKEN")
        
    @property
    def auth_token(self) -> Optional[str]:
        """Get the current authentication token."""
        return self._auth_token
        
    def set_token(self, token: str):
        """Manually set the authentication token."""
        self._auth_token = token
        
    def get_auth_headers(self) -> Dict[str, str]:
        """Get headers with authentication token."""
        headers = {}
        if self._auth_token:
            headers["token"] = self._auth_token
        return headers
        
    def validate_token(self) -> bool:
        """
        Validate the token against the file server.
        Returns True if token is valid.
        """
        if not self._auth_token:
            return False
            
        try:
            # Try to list files - this will fail if token is invalid
            response = requests.get(
                urljoin(self.file_server_url, "/list"),
                headers=self.get_auth_headers()
            )
            return response.status_code == 200
        except Exception:
            return False
            
    def get_kernel_env(self) -> Dict[str, str]:
        """
        Get environment variables to pass to kernels.
        """
        env = {
            "FILE_SERVER_URL": self.file_server_url
        }
        
        if self._auth_token:
            env["WRITE_TOKEN"] = self._auth_token
            
        return env
        
    def upload_file(self, filepath: str, filename: Optional[str] = None) -> bool:
        """
        Upload a file to the file server using token authentication.
        
        Args:
            filepath: Path to the file to upload
            filename: Optional name for the uploaded file (defaults to basename)
            
        Returns:
            True if upload was successful
        """
        if not self._auth_token:
            raise ValueError("No authentication token available")
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
            
        try:
            filename = filename or os.path.basename(filepath)
            
            with open(filepath, 'rb') as f:
                files = {'file': (filename, f)}
                response = requests.post(
                    urljoin(self.file_server_url, "/upload"),
                    headers=self.get_auth_headers(),
                    files=files
                )
                
            return response.status_code == 200
        except Exception as e:
            print(f"Error uploading file: {e}")
            return False
            
    def download_file(self, remote_filename: str, local_path: Optional[str] = None) -> Optional[str]:
        """
        Download a file from the file server.
        
        Args:
            remote_filename: Name of the file to download
            local_path: Optional path where to save the file (defaults to current dir)
            
        Returns:
            Path to the downloaded file or None if failed
        """
        try:
            response = requests.get(
                urljoin(self.file_server_url, f"/read/{remote_filename}"),
                # No token needed for read operations
            )
            
            if response.status_code != 200:
                return None
                
            local_path = local_path or os.path.join(os.getcwd(), remote_filename)
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
                
            return local_path
        except Exception as e:
            print(f"Error downloading file: {e}")
            return None
            
    def delete_file(self, filename: str) -> bool:
        """
        Delete a file from the file server.
        
        Args:
            filename: Name of the file to delete
            
        Returns:
            True if delete was successful
        """
        if not self._auth_token:
            raise ValueError("No authentication token available")
            
        try:
            response = requests.delete(
                urljoin(self.file_server_url, f"/delete/{filename}"),
                headers=self.get_auth_headers()
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False


class AuthenticatedKernelSession(GatewayKernelSession):
    """
    Extended GatewayKernelSession with file server authentication.
    """
    
    def __init__(
        self,
        gateway_http: str,
        gateway_ws: str,
        kernel_name: str,
        file_server_url: str = "http://file-server:8080", 
        auth_token: Optional[str] = None,
        **kwargs
    ):
        # Create auth manager
        self.auth_manager = KernelAuthManager(file_server_url, auth_token)
        
        # Add auth token to the kernel environment
        launch_env = kwargs.get('launch_env', {})
        launch_env.update(self.auth_manager.get_kernel_env())
        kwargs['launch_env'] = launch_env
        
        # Initialize the base class
        super().__init__(gateway_http, gateway_ws, kernel_name, **kwargs)
        
    def upload_to_kernel(self, filepath: str, filename: Optional[str] = None) -> bool:
        """
        Upload a file where the kernel can access it.
        """
        return self.auth_manager.upload_file(filepath, filename)
        
    def download_from_kernel(self, remote_filename: str, local_path: Optional[str] = None) -> Optional[str]:
        """
        Download a file that was created by the kernel.
        """
        return self.auth_manager.download_file(remote_filename, local_path)
        
    def execute_file_op(self, operation: str, filename: str, **kwargs) -> str:
        """
        Execute code in the kernel with file operations.
        Helper method to make file operations in the kernel easier.
        
        Args:
            operation: One of 'read', 'write', 'append', 'delete'
            filename: Name of the file in the shared data directory
            
        Additional kwargs:
            content: Content to write (for write/append operations)
            
        Returns:
            Result of execution
        """
        filepath = f"/data/shared/{filename}"
        
        if operation == 'read':
            code = f"""
with open('{filepath}', 'r') as f:
    content = f.read()
content
            """
        elif operation == 'write':
            content = kwargs.get('content', '')
            code = f"""
with open('{filepath}', 'w') as f:
    f.write('''{content}''')
'File written successfully'
            """
        elif operation == 'append':
            content = kwargs.get('content', '')
            code = f"""
with open('{filepath}', 'a') as f:
    f.write('''{content}''')
'Content appended successfully'
            """
        elif operation == 'delete':
            code = f"""
import os
os.remove('{filepath}')
'File deleted successfully'
            """
        else:
            raise ValueError(f"Unknown operation: {operation}")
            
        return self.execute(code)


# Example usage
def example_usage():
    """Simple example of using the authenticated client."""
    # Example authentication token (would normally be securely managed)
    AUTH_TOKEN = "s3cr3t-token"
      # Create an authenticated session
    session = AuthenticatedKernelSession(
        "http://localhost:8889",
        "ws://localhost:8889",
        "python3",
        file_server_url="http://localhost:8080",
        auth_token=AUTH_TOKEN
    )
    
    with session:
        # Write a file using the kernel
        session.execute_file_op('write', 'test.txt', content="Hello from authenticated kernel!")
        
        # Read the file back
        content = session.execute_file_op('read', 'test.txt')
        print(f"File content: {content}")
        
        # Upload a local file to the shared directory
        with open('local_test.txt', 'w') as f:
            f.write("This is a local file")
        
        session.upload_to_kernel('local_test.txt')
        
        # Verify it's accessible in the kernel
        result = session.execute("with open('/data/shared/local_test.txt') as f: print(f.read())")
        print(f"Uploaded file content: {result}")
        
        # Delete the test files
        session.execute_file_op('delete', 'test.txt')
        session.auth_manager.delete_file('local_test.txt') 