#!/usr/bin/env python3
"""
Example demonstrating authentication with the Jupyter Kernel Client.
"""
import os
import tempfile
from jupyter_kernel_client import AuthenticatedKernelSession, KernelAuthManager


def run_auth_example():
    """Example of using the authenticated kernel client."""
    print("=== Authenticated Session Example ===")
    
    # Connection parameters
    gateway_http = "http://localhost:8889"
    gateway_ws = "ws://localhost:8889"
    # 默认内核为 python3（非自定义 sandbox 内核）
    kernel_name = "python3"
    file_server_url = "http://localhost:8080"
    
    # Create a secure token (in practice, this would be securely managed)
    auth_token = "example-secure-token"
    
    print(f"Connecting to kernel: {kernel_name}")
    print(f"File server: {file_server_url}")
    
    # Create an authenticated session
    session = AuthenticatedKernelSession(
        gateway_http,
        gateway_ws,
        kernel_name,
        file_server_url=file_server_url,
        auth_token=auth_token
    )
    
    with session:
        print(f"Connected to kernel with ID: {session.kernel_id}")
        
        # Use file operation helpers
        print("\nWriting a file using the kernel...")
        result = session.execute_file_op('write', 'test.txt', 
                                        content="Hello from authenticated kernel!")
        print(f"Write result: {result}")
        
        # Read the file back
        print("\nReading the file back...")
        content = session.execute_file_op('read', 'test.txt')
        print(f"File content: {content}")
        
        # Create a local temporary file for upload testing
        print("\nCreating a local file for upload testing...")
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            local_path = f.name
            f.write("This is a local file for testing file uploads")
        
        print(f"Local file created at: {local_path}")
        
        # Upload the file to the shared data directory
        print("\nUploading file to shared directory...")
        upload_success = session.upload_to_kernel(local_path, "uploaded_file.txt")
        if upload_success:
            print("File uploaded successfully")
        else:
            print("File upload failed")
        
        # Verify it's accessible in the kernel
        print("\nVerifying the uploaded file is accessible from the kernel...")
        result = session.execute("with open('/data/shared/uploaded_file.txt') as f: print(f.read())")
        print(f"Uploaded file content: {result}")
        
        # Append to an existing file
        print("\nAppending to the test file...")
        result = session.execute_file_op('append', 'test.txt',
                                        content="\nThis content was appended!")
        print(f"Append result: {result}")
        
        # Read the modified file
        print("\nReading the modified file...")
        content = session.execute_file_op('read', 'test.txt')
        print(f"Modified file content: {content}")
        
        # Download a file from the shared directory
        print("\nDownloading a file from the shared directory...")
        download_path = session.download_from_kernel("test.txt", 
                                                    local_path="downloaded_test.txt")
        if download_path:
            print(f"File downloaded to: {download_path}")
            with open(download_path, 'r') as f:
                local_content = f.read()
            print(f"Local file content: {local_content}")
        else:
            print("File download failed")
        
        # Delete the test files
        print("\nCleaning up...")
        session.execute_file_op('delete', 'test.txt')
        session.auth_manager.delete_file('uploaded_file.txt')
        
        # Remove local temporary files
        if os.path.exists(local_path):
            os.unlink(local_path)
        if download_path and os.path.exists(download_path):
            os.unlink(download_path)
    
    print("\nSession closed successfully")


def run_auth_manager_example():
    """Example of using the KernelAuthManager directly."""
    print("\n=== Auth Manager Example ===")
    
    file_server_url = "http://localhost:8080"
    auth_token = "example-secure-token"
    
    # Create the auth manager
    auth_manager = KernelAuthManager(file_server_url, auth_token)
    
    # Check if the token is valid
    print(f"Checking if token is valid...")
    is_valid = auth_manager.validate_token()
    print(f"Token is valid: {is_valid}")
    
    # Get environment variables for kernels
    env_vars = auth_manager.get_kernel_env()
    print(f"Environment variables for kernels: {env_vars}")
    
    # Get authentication headers
    headers = auth_manager.get_auth_headers()
    print(f"Authentication headers: {headers}")


def main():
    """Run the authentication examples."""
    run_auth_example()
    run_auth_manager_example()


if __name__ == "__main__":
    main() 