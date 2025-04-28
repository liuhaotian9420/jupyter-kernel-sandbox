# mini-jupyter-sandbox

一个最小化、可扩展且面向生产的 Jupyter Notebook 沙箱环境，利用 [Jupyter Enterprise Gateway](https://jupyter-enterprise-gateway.readthedocs.io/en/latest/) 和 Docker 实现安全、容器化的内核执行。本项目适用于快速原型开发、实验以及在隔离的 Python 环境中安全执行代码。

---

## 目录
- [mini-jupyter-sandbox](#mini-jupyter-sandbox)
  - [目录](#目录)
  - [项目概述](#项目概述)
  - [架构](#架构)
  - [快速开始](#快速开始)
    - [前置条件](#前置条件)
    - [1. 克隆仓库](#1-克隆仓库)
    - [2. 构建并启动环境](#2-构建并启动环境)
    - [3. 停止环境](#3-停止环境)
    - [4. 安装客户端包](#4-安装客户端包)
  - [目录结构](#目录结构)
  - [配置与可扩展性](#配置与可扩展性)
    - [添加更多内核](#添加更多内核)
  - [使用方法](#使用方法)
    - [交互式 Notebook](#交互式-notebook)
    - [编程方式访问](#编程方式访问)
  - [Python 客户端 API](#python-客户端-api)
    - [核心客户端](#核心客户端)
  - [高级特性](#高级特性)
    - [异步客户端](#异步客户端)
    - [Prometheus 监控](#prometheus-监控)
    - [认证](#认证)
  - [开发与测试](#开发与测试)
    - [依赖安装](#依赖安装)
    - [运行测试](#运行测试)
    - [测试环境搭建](#测试环境搭建)
  - [贡献指南](#贡献指南)
  - [许可证](#许可证)

---

## 项目概述
本沙箱为每个内核在独立的 Docker 容器中运行 Jupyter Notebook 环境，实现主机与用户间的隔离。适用于：
- 安全、临时的代码执行
- 教育或培训环境
- 自定义内核的实验
- 通过客户端 API 自动化代码执行
- 扩展以支持更多语言或运行策略

## 架构
- **Jupyter Notebook**：用户界面，支持代码、Markdown 和数据可视化。
- **Enterprise Gateway**：远程内核管理，每个内核在 Docker 容器中启动。
- **自定义 Kernel Spec**：定义沙箱 Python 内核，使用自定义 Docker 镜像。
- **文件服务器**：基于 FastAPI 的 HTTP 服务器，实现主机与容器间的文件共享。
- **共享数据卷**：在容器和服务间持久化文件。
- **Python 客户端 API**：通过 `GatewayKernelSession` 类以编程方式访问内核。

```
[用户] ⟷ [Jupyter Notebook] ⟷ [Enterprise Gateway] ⟷ [沙箱内核 (Docker)]
   ↑                                    ↑
   |                                    |
[Python 客户端] -------------------- [文件服务器]
                        ↑                ↑
                        ↓                ↓
                    [共享数据卷]
```

## 快速开始
### 前置条件
- [Docker](https://docs.docker.com/get-docker/)（含 Compose）
- [Python 3.10+](https://www.python.org/downloads/)
- （可选）[Git](https://git-scm.com/)

### 1. 克隆仓库
```bash
git clone <this-repo-url>
cd mini-jupyter-sandbox
```

### 2. 构建并启动环境
```bash
docker-compose up --build
```
- Jupyter Notebook: http://localhost:8888 （无需 token）
- 文件服务器: http://localhost:8080
- Enterprise Gateway: http://localhost:8889

### 3. 停止环境
```bash
docker-compose down
```

### 4. 安装客户端包
```bash
# 基础用法
pip install -e .

# 含全部特性
pip install -e ".[all]"

# 指定特性
pip install -e ".[async,metrics]"
```

## 目录结构
```
mini-jupyter-sandbox/
├── examples/                  # 客户端使用示例
│   ├── basic_usage.py         # 基础用法
│   ├── async_example.py       # 异步用法
│   ├── metrics_example.py     # Prometheus 监控示例
│   └── auth_example.py        # 认证示例
├── kernels/
│   └── sandbox-python/
│       └── kernel.json        # 沙箱 Python 内核规范
├── file-server/               # FastAPI 文件服务器
│   └── app.py                 # API 实现，含基于 token 的认证
├── shared-data/               # 文件交换的共享卷
├── src/
│   └── jupyter_kernel_client/ # Python 包目录
│       ├── __init__.py        # 包初始化
│       ├── core/              # 核心客户端功能
│       ├── async_client/      # 异步客户端
│       ├── auth/              # 认证模块
│       └── metrics/           # Prometheus 监控模块
├── docker-compose.yaml        # 多服务编排
├── Dockerfile                 # 自定义 Jupyter Notebook 镜像
├── jupyter_notebook_config.py # Notebook 配置（远程内核管理）
├── setup.py                   # 包安装脚本
├── requirements-client.txt    # 客户端依赖
├── requirements-test.txt      # 测试依赖
└── README.md                  # 项目文档
```

## 配置与可扩展性
- **自定义内核**：在 `kernels/sandbox-python/kernel.json` 定义，使用 `myorg/notebook-with-sandbox:latest` 镜像（由 Dockerfile 构建）。
- **Dockerfile**：基于 `jupyter/base-notebook:python-3.10`，安装依赖、添加内核规范并设置权限。
- **Enterprise Gateway**：在 `docker-compose.yaml` 和 `jupyter_notebook_config.py` 配置，支持通过 Docker 启动远程内核。
- **共享数据**：`shared-data` 卷挂载到 notebook 和内核容器，实现文件交换。
- **文件服务器**：基于 FastAPI，支持 HTTP 文件访问和 token 认证。

### 添加更多内核
如需添加其他语言或环境：
1. 在 `kernels/` 下创建新的内核规范。
2. 根据需要更新 Dockerfile 和 `docker-compose.yaml`。
3. 重新构建环境。

## 使用方法
### 交互式 Notebook
- 启动 Jupyter Notebook，选择 **Python 3** 内核（默认内核为 python3，非自定义 sandbox 内核）。
- 所有代码在全新、隔离的 Docker 容器中运行。
- 保存到 `/home/jovyan/shared-data` 的文件可通过文件服务器和内核容器访问。

### 编程方式访问
使用 `GatewayKernelSession` 客户端以编程方式执行内核代码：

```python
from jupyter_kernel_client import GatewayKernelSession

# 创建并使用内核
with GatewayKernelSession(
    "http://localhost:8889",
    "ws://localhost:8889",
    "python3"  # 默认内核为 python3
) as session:
    # 执行代码
    result = session.execute("2 + 2")
    print(result)  # 输出: 4
    
    # 可向共享卷写文件
    result = session.execute("""
        with open('/data/shared/my_output.txt', 'w') as f:
            f.write('Hello from the kernel!')
    """)
```

详见 `examples/basic_usage.py` 获取更完整示例。

> **注意**：本项目默认使用 python3 内核（即 Jupyter 官方 Python 3 内核），而非自定义的 sandbox-python 内核。如需自定义内核，请参考"配置与可扩展性"章节。

## Python 客户端 API
客户端包包含以下组件：

### 核心客户端
核心模块提供标准同步客户端：

```python
class GatewayKernelSession:
    """用于与 Jupyter Enterprise Gateway 内核交互的客户端。"""
    
    def __init__(self, gateway_http, gateway_ws, kernel_name, 
                 launch_env=None, startup_timeout=30,
                 max_retries=3, retry_delay=1.0):
        """初始化内核会话。"""
        
    def execute(self, code, timeout=10):
        """在内核中执行代码并返回结果。"""
```

模块还提供 `KernelSessionPool` 类用于管理多个内核。

## 高级特性

### 异步客户端
支持异步编程，提供异步客户端：

```python
import asyncio
from jupyter_kernel_client import AsyncGatewayKernelSession

async def main():
    async with AsyncGatewayKernelSession(
        "http://localhost:8889",
        "ws://localhost:8889",
        "python3"
    ) as session:
        result = await session.execute("print('Hello, async world!')")
        print(result)

asyncio.run(main())
```

详见 `examples/async_example.py` 获取更完整示例。

### Prometheus 监控
支持 Prometheus 集成以监控内核性能：

```python
from prometheus_client import start_http_server
from jupyter_kernel_client import PrometheusGatewayKernelSession

# 启动 Prometheus HTTP 服务
start_http_server(8000)

# 创建带监控的会话
session = PrometheusGatewayKernelSession(
    "http://localhost:8889",
    "ws://localhost:8889",
    "python3"
)

with session:
    result = session.execute("print('Hello, Prometheus!')")
    print(result)
```

详见 `examples/metrics_example.py` 获取更完整示例。

### 认证
支持安全文件操作的认证集成：

```python
from jupyter_kernel_client import AuthenticatedKernelSession

# 创建认证会话
session = AuthenticatedKernelSession(
    "http://localhost:8889",
    "ws://localhost:8889",
    "python3",
    file_server_url="http://localhost:8080",
    auth_token="your-secret-token"
)

with session:
    # 使用内核写文件
    session.execute_file_op('write', 'test.txt', 
                          content="Hello from authenticated kernel!")
    
    # 上传本地文件到共享目录
    session.upload_to_kernel('local_file.txt')
    
    # 从内核下载文件
    session.download_from_kernel('kernel_output.csv')
```

详见 `examples/auth_example.py` 获取更完整示例。

## 开发与测试
### 依赖安装
安装测试和客户端依赖：
```bash
pip install -e ".[dev]"
```

### 运行测试
```bash
# 若环境未启动，先启动
docker-compose up -d

# 使用测试脚本运行测试
python -m pytest tests/

# 运行指定类别测试
python -m pytest tests/ -k "unit"  # 仅运行单元测试
python -m pytest tests/ -k "integration"  # 仅运行集成测试
```

### 测试环境搭建
提供辅助脚本以搭建测试环境：
```bash
# Linux/macOS
chmod +x test_env.sh
./test_env.sh

# Windows
powershell -ExecutionPolicy Bypass -File test_env.ps1
```

## 贡献指南
欢迎贡献！请：
- Fork 仓库并创建功能分支
- 编写清晰、模块化、文档完善的代码
- 为所有更改添加或更新测试
- 确保所有测试通过后提交 PR
- 提交带有清晰描述的 PR

## 许可证
请在此处指定您的许可证（如 MIT、Apache-2.0）。如未指定，请添加 LICENSE 文件。

---

如有问题或需支持，请提交 issue 或联系维护者。
