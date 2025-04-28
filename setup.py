from setuptools import setup, find_packages

setup(
    name="jupyter-kernel-client",
    version="0.1.0",
    description="Secure, containerized Jupyter kernel client with advanced features",
    author="Mini Jupyter Sandbox Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "requests>=2.31.0",
        "websocket-client>=1.6.1",
    ],
    extras_require={
        "async": ["aiohttp>=3.8.5", "websockets>=11.0.3"],
        "metrics": ["prometheus-client>=0.17.1"],
        "all": [
            "aiohttp>=3.8.5", 
            "websockets>=11.0.3", 
            "prometheus-client>=0.17.1"
        ],
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "mock>=5.1.0",
            "black>=23.3.0",
            "isort>=5.12.0",
            "mypy>=1.3.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries",
        "Topic :: Scientific/Engineering",
    ],
) 