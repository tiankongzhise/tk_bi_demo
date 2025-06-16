# TK BI Demo - 多平台广告数据聚合系统

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](Dockerfile)
[![API](https://img.shields.io/badge/API-RESTful-orange.svg)](#api-文档)

## 📋 项目简介

TK BI Demo 是一个现代化的多平台广告数据聚合和分析系统，专为广告主提供统一的数据视图和深度分析能力。系统采用模块化架构设计，支持多个主流搜索引擎广告平台的数据接入和实时同步。

### 🎯 核心特性

- **🔗 多平台支持**: 支持百度、搜狗、360、神马、字节跳动、腾讯等主流广告平台
- **⚡ 异步架构**: 基于 aiohttp 和 asyncio 的高性能异步处理
- **🔄 实时同步**: 支持定时和实时的数据同步机制
- **📊 数据分析**: 提供丰富的数据分析和报表功能
- **🛡️ 高可用性**: 完善的错误处理、重试机制和监控告警
- **🔧 易扩展**: 插件化架构，支持新平台的快速接入
- **🐳 容器化**: 完整的 Docker 和 Docker Compose 支持
- **📈 监控完善**: 集成 Prometheus 和 Grafana 监控方案

### 🏗️ 技术架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   Mobile App    │    │  Third Party    │
│                 │    │                 │    │   Integration   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │      API Gateway          │
                    │   (aiohttp + routes)      │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │    Business Logic Layer   │
                    │                           │
                    │  ┌─────────────────────┐  │
                    │  │   Task Scheduler    │  │
                    │  └─────────────────────┘  │
                    │  ┌─────────────────────┐  │
                    │  │  Data Processor     │  │
                    │  └─────────────────────┘  │
                    │  ┌─────────────────────┐  │
                    │  │  Platform Adapters  │  │
                    │  └─────────────────────┘  │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │     Data Access Layer     │
                    │                           │
                    │  ┌─────────────────────┐  │
                    │  │   Database Models   │  │
                    │  └─────────────────────┘  │
                    │  ┌─────────────────────┐  │
                    │  │   HTTP Clients      │  │
                    │  └─────────────────────┘  │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │   External Dependencies   │
                    │                           │
                    │  ┌─────────┐ ┌─────────┐  │
                    │  │  MySQL  │ │  Redis  │  │
                    │  └─────────┘ └─────────┘  │
                    │  ┌─────────────────────┐  │
                    │  │  Ad Platform APIs   │  │
                    │  └─────────────────────┘  │
                    └───────────────────────────┘
```

## 🚀 快速开始

### 环境要求

- Python 3.9+
- MySQL 8.0+
- Redis 6.0+ (可选)
- Docker & Docker Compose (推荐)

### 方式一：Docker 部署（推荐）

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd tk_bi_demo
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，配置数据库和API密钥
   ```

3. **启动服务**
   ```bash
   # 启动基础服务
   docker-compose up -d
   
   # 启动包含监控的完整服务
   docker-compose --profile monitoring up -d
   ```

4. **验证部署**
   ```bash
   # 检查服务状态
   docker-compose ps
   
   # 查看应用日志
   docker-compose logs -f app
   
   # 健康检查
   curl http://localhost:8000/api/v1/health
   ```

### 方式二：本地开发部署

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置数据库**
   ```bash
   # 创建数据库
   mysql -u root -p -e "CREATE DATABASE tkbi_demo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
   
   # 运行数据库迁移
   alembic upgrade head
   ```

3. **启动应用**
   ```bash
   python main.py
   ```
    clicks: int
    cost: float
    date: date
​​4. 性能优化​​
​​并发控制​​
使用asyncio.gather并发请求多个平台API
async def fetch_all_platforms():
    tasks = [platform.fetch_report() for platform in platforms]
    await asyncio.gather(*tasks)
​​连接池配置​​
HTTP连接池：aiohttp.TCPConnector(limit=100)
数据库连接池：asyncmy.create_pool(size=20)
​​5. 错误处理机制​​
错误码	场景	处理方式
1001	API请求超时	自动重试（最多3次）
1002	认证失效	刷新Token后重新请求
2001	数据校验失败	记录错误日志并跳过该条数据
3001	数据库连接异常	中断当前任务，触发告警
​​6. 部署要求​​
​​环境​​：
Docker容器化部署（Python镜像 + MySQL镜像）
​​监控​​：
通过日志服务监控运行状态，关键指标：
API请求成功率（≥95%）
数据入库延迟（≤5分钟）
​​7. 附录​​
​​依赖库清单​​：
aiohttp==3.9.0
sqlalchemy[asyncio]==2.0.25
pydantic==2.5.0
asyncmy==0.2.7
​​数据流示意图​​：
graph LR
  A[调度器] --> B{HTTP服务}
  B --> C[百度API]
  B --> D[搜狗API]
  B --> E[...]
  C --> F[Pydantic数据校验]
  F --> G[MySQL存储]
  G --> H[错误服务/日志]








​​文档审核确认​​：
✅ 技术可行性
✅ 第三方API兼容性
✅ 性能指标达标
✅ 异常处理完整性
