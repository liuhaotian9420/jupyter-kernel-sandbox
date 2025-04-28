# jupyter_notebook_config.py
c = get_config()
# Use the RemoteKernelManager instead of the default LocalKernelManager
c.NotebookApp.kernel_manager_class = (
    "enterprise_gateway.services.kernel_manager.RemoteKernelManager"
)
# Point at your Enterprise Gateway
c.RemoteKernelManager.rest_url = "http://enterprise-gateway:8889"
# Allow a bit more time for remote kernels to start
c.RemoteKernelManager.kernel_info_timeout = 60
