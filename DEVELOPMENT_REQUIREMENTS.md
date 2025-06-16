# TK BI Demo 开发需求文档

## 1. 项目概述

### 1.1 项目背景
TK BI Demo 是一个多平台广告数据聚合和分析系统，旨在为广告主提供统一的数据视图和分析能力。系统支持多个主流搜索引擎广告平台的数据接入，包括百度、搜狗、360、神马、字节跳动和腾讯等平台。

### 1.2 核心目标
- **数据统一**: 将多个广告平台的数据统一到一个系统中
- **实时同步**: 支持定时和实时的数据同步机制
- **数据分析**: 提供丰富的数据分析和报表功能
- **高可用性**: 确保系统的稳定性和可靠性
- **可扩展性**: 支持新平台的快速接入

### 1.3 技术栈
- **后端**: Python 3.8+, aiohttp, SQLAlchemy
- **数据库**: MySQL 8.0+
- **缓存**: Redis (可选)
- **任务调度**: asyncio + 自定义调度器
- **API**: RESTful API
- **部署**: Docker + Docker Compose

## 2. 系统架构设计

### 2.1 整体架构
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

### 2.2 模块划分

#### 2.2.1 核心模块 (app/core/)
- **配置管理**: 统一的配置加载和管理
- **日志系统**: 结构化日志记录
- **数据库管理**: 数据库连接池和事务管理
- **异常处理**: 统一的异常处理机制

#### 2.2.2 数据模型 (app/models/)
- **数据库模型**: SQLAlchemy ORM模型
- **数据验证模型**: Pydantic模型用于API数据验证
- **枚举定义**: 系统中使用的各种枚举类型

#### 2.2.3 服务层 (app/services/)
- **HTTP客户端**: 统一的HTTP请求管理
- **数据处理器**: 数据清洗、转换和存储
- **任务调度器**: 异步任务管理和调度

#### 2.2.4 适配器层 (app/adapters/)
- **基础适配器**: 定义平台适配器接口
- **平台适配器**: 各个广告平台的具体实现
- **适配器工厂**: 适配器实例管理

#### 2.2.5 API层 (app/api/)
- **路由定义**: RESTful API路由
- **请求处理**: HTTP请求处理逻辑
- **响应格式**: 统一的API响应格式

#### 2.2.6 工具模块 (app/utils/)
- **重试机制**: 网络请求重试
- **数据验证**: 通用数据验证工具
- **日期时间**: 日期时间处理工具
- **加密工具**: 数据加密和签名

## 3. 详细设计规范

### 3.1 模块化设计原则

#### 3.1.1 单一职责原则
- 每个模块只负责一个特定的功能领域
- 模块内部的类和函数都围绕该功能领域设计
- 避免模块间的功能重叠

#### 3.1.2 依赖倒置原则
- 高层模块不依赖低层模块，都依赖抽象
- 使用接口和抽象基类定义模块间的契约
- 通过依赖注入实现模块解耦

#### 3.1.3 开闭原则
- 模块对扩展开放，对修改关闭
- 通过继承和组合实现功能扩展
- 使用配置和插件机制支持动态扩展

### 3.2 通用性设计

#### 3.2.1 配置驱动
```python
# 配置文件结构
class Config:
    # 数据库配置
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    
    # API配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # 平台配置
    PLATFORMS: Dict[str, Dict[str, Any]]
    
    # 任务配置
    TASK_CONCURRENCY: int = 5
    TASK_RETRY_TIMES: int = 3
```

#### 3.2.2 插件化架构
```python
# 平台适配器接口
class BasePlatformAdapter(ABC):
    @abstractmethod
    async def get_report_data(self, **kwargs) -> List[Dict]:
        pass
    
    @abstractmethod
    async def authenticate(self) -> bool:
        pass

# 适配器注册机制
PLATFORM_ADAPTERS = {
    'baidu': BaiduAdapter,
    'sogou': SogouAdapter,
    # 新平台可以直接注册
}
```

### 3.3 可复用性设计

#### 3.3.1 组件化设计
```python
# 可复用的HTTP客户端
class HTTPClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = None
    
    async def request(self, method: str, url: str, **kwargs):
        # 通用的HTTP请求逻辑
        pass

# 可复用的数据处理器
class DataProcessor:
    def __init__(self, validator: DataValidator):
        self.validator = validator
    
    async def process_batch(self, data: List[Dict]) -> ProcessResult:
        # 通用的数据处理逻辑
        pass
```

#### 3.3.2 工具函数库
```python
# 通用工具函数
def retry_async(max_attempts: int = 3, delay: float = 1.0):
    """异步重试装饰器"""
    pass

def validate_date_range(start_date: str, end_date: str) -> bool:
    """日期范围验证"""
    pass

def normalize_platform_data(data: Dict, platform: str) -> Dict:
    """平台数据标准化"""
    pass
```

### 3.4 可扩展性设计

#### 3.4.1 事件驱动架构
```python
# 事件系统
class EventManager:
    def __init__(self):
        self.listeners = defaultdict(list)
    
    def subscribe(self, event_type: str, handler: Callable):
        self.listeners[event_type].append(handler)
    
    async def publish(self, event_type: str, data: Any):
        for handler in self.listeners[event_type]:
            await handler(data)

# 事件定义
class DataSyncEvent:
    platform: str
    status: str
    data_count: int
    timestamp: datetime
```

#### 3.4.2 中间件机制
```python
# API中间件
class APIMiddleware:
    async def process_request(self, request: web.Request) -> Optional[web.Response]:
        pass
    
    async def process_response(self, request: web.Request, response: web.Response) -> web.Response:
        pass

# 数据处理中间件
class DataMiddleware:
    async def before_process(self, data: List[Dict]) -> List[Dict]:
        pass
    
    async def after_process(self, result: ProcessResult) -> ProcessResult:
        pass
```

### 3.5 稳定性设计

#### 3.5.1 错误处理
```python
# 分层异常处理
class TKBIException(Exception):
    """基础异常类"""
    pass

class PlatformAPIException(TKBIException):
    """平台API异常"""
    pass

class DataValidationException(TKBIException):
    """数据验证异常"""
    pass

# 全局异常处理器
async def global_exception_handler(request: web.Request, ex: Exception) -> web.Response:
    logger.error(f"Unhandled exception: {str(ex)}", exc_info=True)
    return web.json_response({
        'error': 'Internal server error',
        'code': 500
    }, status=500)
```

#### 3.5.2 熔断机制
```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func: Callable, *args, **kwargs):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise CircuitBreakerOpenException()
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
```

#### 3.5.3 限流机制
```python
class RateLimiter:
    def __init__(self, rate: int, per: int):
        self.rate = rate  # 请求数量
        self.per = per    # 时间窗口(秒)
        self.tokens = rate
        self.last_update = time.time()
    
    async def acquire(self) -> bool:
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.rate, self.tokens + elapsed * (self.rate / self.per))
        self.last_update = now
        
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
```

### 3.6 可靠性设计

#### 3.6.1 数据一致性
```python
# 事务管理
class TransactionManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def execute_in_transaction(self, operations: List[Callable]):
        async with self.db_manager.transaction() as tx:
            try:
                results = []
                for operation in operations:
                    result = await operation(tx)
                    results.append(result)
                await tx.commit()
                return results
            except Exception:
                await tx.rollback()
                raise

# 数据校验
class DataIntegrityChecker:
    async def check_data_consistency(self, platform: str, date: str) -> bool:
        # 检查数据完整性
        pass
    
    async def repair_data_inconsistency(self, platform: str, date: str):
        # 修复数据不一致
        pass
```

#### 3.6.2 监控和告警
```python
# 健康检查
class HealthChecker:
    def __init__(self):
        self.checks = []
    
    def register_check(self, name: str, check_func: Callable):
        self.checks.append((name, check_func))
    
    async def run_all_checks(self) -> Dict[str, bool]:
        results = {}
        for name, check_func in self.checks:
            try:
                results[name] = await check_func()
            except Exception:
                results[name] = False
        return results

# 性能监控
class PerformanceMonitor:
    def __init__(self):
        self.metrics = defaultdict(list)
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        self.metrics[name].append({
            'value': value,
            'timestamp': time.time(),
            'tags': tags or {}
        })
    
    def get_metrics_summary(self, name: str, time_range: int = 3600) -> Dict:
        # 获取指标摘要
        pass
```

## 4. 数据库设计

### 4.1 表结构设计

#### 4.1.1 广告数据表 (ad_data)
```sql
CREATE TABLE ad_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    platform VARCHAR(20) NOT NULL COMMENT '平台名称',
    account_id VARCHAR(50) NOT NULL COMMENT '账户ID',
    campaign_id VARCHAR(50) COMMENT '广告计划ID',
    adgroup_id VARCHAR(50) COMMENT '广告组ID',
    keyword_id VARCHAR(50) COMMENT '关键词ID',
    date DATE NOT NULL COMMENT '数据日期',
    
    -- 基础指标
    impressions INT DEFAULT 0 COMMENT '展现量',
    clicks INT DEFAULT 0 COMMENT '点击量',
    cost DECIMAL(10,2) DEFAULT 0 COMMENT '消费',
    conversions INT DEFAULT 0 COMMENT '转化量',
    
    -- 扩展字段
    extra_data JSON COMMENT '扩展数据',
    
    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 索引
    UNIQUE KEY uk_platform_account_date (platform, account_id, date, campaign_id, adgroup_id, keyword_id),
    KEY idx_platform_date (platform, date),
    KEY idx_account_date (account_id, date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告数据表';
```

#### 4.1.2 任务日志表 (task_logs)
```sql
CREATE TABLE task_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id VARCHAR(50) NOT NULL COMMENT '任务ID',
    task_type VARCHAR(20) NOT NULL COMMENT '任务类型',
    platform VARCHAR(20) COMMENT '平台名称',
    status VARCHAR(20) NOT NULL COMMENT '任务状态',
    
    -- 任务配置
    config JSON COMMENT '任务配置',
    
    -- 执行信息
    start_time TIMESTAMP COMMENT '开始时间',
    end_time TIMESTAMP COMMENT '结束时间',
    duration INT COMMENT '执行时长(秒)',
    
    -- 结果信息
    success_count INT DEFAULT 0 COMMENT '成功数量',
    error_count INT DEFAULT 0 COMMENT '错误数量',
    error_message TEXT COMMENT '错误信息',
    
    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 索引
    KEY idx_task_id (task_id),
    KEY idx_platform_status (platform, status),
    KEY idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务日志表';
```

#### 4.1.3 平台认证表 (platform_auth)
```sql
CREATE TABLE platform_auth (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    platform VARCHAR(20) NOT NULL COMMENT '平台名称',
    account_id VARCHAR(50) NOT NULL COMMENT '账户ID',
    
    -- 认证信息
    access_token TEXT COMMENT '访问令牌',
    refresh_token TEXT COMMENT '刷新令牌',
    token_expires_at TIMESTAMP COMMENT '令牌过期时间',
    
    -- 账户信息
    account_name VARCHAR(100) COMMENT '账户名称',
    account_status VARCHAR(20) COMMENT '账户状态',
    
    -- 配置信息
    api_config JSON COMMENT 'API配置',
    sync_config JSON COMMENT '同步配置',
    
    -- 状态信息
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    last_sync_time TIMESTAMP COMMENT '最后同步时间',
    
    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 索引
    UNIQUE KEY uk_platform_account (platform, account_id),
    KEY idx_platform_active (platform, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='平台认证表';
```

### 4.2 数据分区策略

#### 4.2.1 按日期分区
```sql
-- 广告数据表按月分区
ALTER TABLE ad_data PARTITION BY RANGE (TO_DAYS(date)) (
    PARTITION p202401 VALUES LESS THAN (TO_DAYS('2024-02-01')),
    PARTITION p202402 VALUES LESS THAN (TO_DAYS('2024-03-01')),
    PARTITION p202403 VALUES LESS THAN (TO_DAYS('2024-04-01')),
    -- 继续添加分区...
    PARTITION p_future VALUES LESS THAN MAXVALUE
);
```

#### 4.2.2 数据归档策略
```python
class DataArchiver:
    async def archive_old_data(self, days_to_keep: int = 365):
        """归档旧数据"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # 归档到历史表
        await self.move_to_archive_table(cutoff_date)
        
        # 删除原表数据
        await self.delete_old_data(cutoff_date)
```

## 5. API设计规范

### 5.1 RESTful API设计

#### 5.1.1 URL设计规范
```
# 资源命名
GET    /api/v1/ad-data              # 获取广告数据列表
POST   /api/v1/ad-data              # 创建广告数据
GET    /api/v1/ad-data/{id}         # 获取特定广告数据
PUT    /api/v1/ad-data/{id}         # 更新特定广告数据
DELETE /api/v1/ad-data/{id}         # 删除特定广告数据

# 嵌套资源
GET    /api/v1/platforms/{platform}/accounts     # 获取平台账户列表
POST   /api/v1/platforms/{platform}/sync         # 触发平台数据同步

# 操作资源
POST   /api/v1/tasks/{task_id}/cancel           # 取消任务
POST   /api/v1/ad-data/export                   # 导出数据
```

#### 5.1.2 请求响应格式
```python
# 统一响应格式
class APIResponse:
    success: bool
    data: Optional[Any] = None
    message: str = ""
    code: int = 200
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

# 分页响应格式
class PaginatedResponse:
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

# 错误响应格式
class ErrorResponse:
    error: str
    code: int
    details: Optional[Dict] = None
    timestamp: datetime = Field(default_factory=datetime.now)
```

#### 5.1.3 状态码规范
```python
# HTTP状态码使用规范
HTTP_STATUS_CODES = {
    200: "请求成功",
    201: "创建成功",
    204: "删除成功",
    400: "请求参数错误",
    401: "未授权",
    403: "禁止访问",
    404: "资源不存在",
    409: "资源冲突",
    422: "数据验证失败",
    429: "请求频率限制",
    500: "服务器内部错误",
    502: "网关错误",
    503: "服务不可用"
}
```

### 5.2 API安全设计

#### 5.2.1 认证授权
```python
# JWT认证
class JWTAuth:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def generate_token(self, payload: Dict, expires_in: int = 3600) -> str:
        payload['exp'] = datetime.utcnow() + timedelta(seconds=expires_in)
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict:
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

# API密钥认证
class APIKeyAuth:
    async def authenticate(self, request: web.Request) -> Optional[str]:
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            raise web.HTTPUnauthorized(text="API key required")
        
        # 验证API密钥
        if not await self.validate_api_key(api_key):
            raise web.HTTPUnauthorized(text="Invalid API key")
        
        return api_key
```

#### 5.2.2 请求验证
```python
# 请求签名验证
class RequestSigner:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def sign_request(self, method: str, url: str, body: str, timestamp: str) -> str:
        message = f"{method}\n{url}\n{body}\n{timestamp}"
        return hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def verify_signature(self, request: web.Request) -> bool:
        signature = request.headers.get('X-Signature')
        timestamp = request.headers.get('X-Timestamp')
        
        if not signature or not timestamp:
            return False
        
        # 检查时间戳
        if abs(time.time() - float(timestamp)) > 300:  # 5分钟有效期
            return False
        
        # 验证签名
        expected_signature = self.sign_request(
            request.method,
            str(request.url),
            await request.text(),
            timestamp
        )
        
        return hmac.compare_digest(signature, expected_signature)
```

## 6. 部署和运维

### 6.1 Docker化部署

#### 6.1.1 Dockerfile
```dockerfile
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "main.py"]
```

#### 6.1.2 Docker Compose
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mysql://user:password@db:3306/tkbi
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=tkbi
      - MYSQL_USER=user
      - MYSQL_PASSWORD=password
    volumes:
      - mysql_data:/var/lib/mysql
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "3306:3306"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  mysql_data:
  redis_data:
```

### 6.2 监控和日志

#### 6.2.1 日志配置
```python
# 日志配置
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'json': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter'
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}
```

#### 6.2.2 性能监控
```python
# Prometheus指标
from prometheus_client import Counter, Histogram, Gauge

# 定义指标
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active database connections')
TASK_QUEUE_SIZE = Gauge('task_queue_size', 'Task queue size')

# 中间件收集指标
async def metrics_middleware(request: web.Request, handler):
    start_time = time.time()
    
    try:
        response = await handler(request)
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.path,
            status=response.status
        ).inc()
        return response
    finally:
        REQUEST_DURATION.observe(time.time() - start_time)
```

## 7. 测试策略

### 7.1 单元测试
```python
# 测试配置
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def db_session():
    # 创建测试数据库会话
    pass

@pytest.fixture
def mock_http_client():
    client = AsyncMock()
    client.request.return_value = {
        'status': 200,
        'data': {'success': True}
    }
    return client

# 测试用例示例
class TestBaiduAdapter:
    async def test_get_report_data(self, mock_http_client):
        adapter = BaiduAdapter(http_client=mock_http_client)
        
        result = await adapter.get_report_data(
            start_date='2024-01-01',
            end_date='2024-01-31'
        )
        
        assert result is not None
        assert len(result) > 0
        mock_http_client.request.assert_called_once()
```

### 7.2 集成测试
```python
# API集成测试
class TestAPIIntegration:
    async def test_sync_data_endpoint(self, aiohttp_client, app):
        client = await aiohttp_client(app)
        
        resp = await client.post('/api/v1/sync', json={
            'platform': 'baidu',
            'start_date': '2024-01-01',
            'end_date': '2024-01-31'
        })
        
        assert resp.status == 200
        data = await resp.json()
        assert data['success'] is True
        assert 'task_id' in data['data']
```

### 7.3 性能测试
```python
# 负载测试
import locust
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # 登录获取token
        response = self.client.post('/api/v1/auth/login', json={
            'username': 'test',
            'password': 'test'
        })
        self.token = response.json()['data']['token']
        self.client.headers.update({'Authorization': f'Bearer {self.token}'})
    
    @task(3)
    def get_ad_data(self):
        self.client.get('/api/v1/ad-data?page=1&page_size=20')
    
    @task(1)
    def sync_data(self):
        self.client.post('/api/v1/sync', json={
            'platform': 'baidu',
            'start_date': '2024-01-01',
            'end_date': '2024-01-01'
        })
```

## 8. 开发规范

### 8.1 代码规范

#### 8.1.1 Python代码规范
- 遵循PEP 8代码风格
- 使用类型注解
- 函数和类必须有文档字符串
- 使用有意义的变量和函数名
- 单个函数不超过50行
- 单个文件不超过500行

#### 8.1.2 命名规范
```python
# 类名：大驼峰
class DataProcessor:
    pass

# 函数名：小写+下划线
def process_ad_data():
    pass

# 常量：大写+下划线
MAX_RETRY_TIMES = 3

# 私有属性：下划线开头
class MyClass:
    def __init__(self):
        self._private_attr = None
        self.__very_private_attr = None
```

### 8.2 Git工作流

#### 8.2.1 分支策略
```
main          # 主分支，生产环境代码
├── develop   # 开发分支，集成最新功能
├── feature/* # 功能分支
├── hotfix/*  # 热修复分支
└── release/* # 发布分支
```

#### 8.2.2 提交规范
```
# 提交信息格式
<type>(<scope>): <subject>

<body>

<footer>

# 类型说明
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 重构
test: 测试相关
chore: 构建过程或辅助工具的变动

# 示例
feat(adapter): add sogou platform adapter

Implement sogou platform adapter with following features:
- OAuth2 authentication
- Report data fetching
- Data normalization

Closes #123
```

### 8.3 文档规范

#### 8.3.1 API文档
使用OpenAPI 3.0规范，自动生成API文档：

```python
from aiohttp_swagger3 import SwaggerDocs

# 添加Swagger文档
swagger = SwaggerDocs(app, "/api/docs")

@swagger.auto_doc()
async def get_ad_data(request: web.Request) -> web.Response:
    """
    获取广告数据
    ---
    tags:
      - 广告数据
    parameters:
      - name: platform
        in: query
        required: false
        schema:
          type: string
          enum: [baidu, sogou, qihoo]
        description: 平台名称
    responses:
      200:
        description: 成功返回广告数据
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/APIResponse'
    """
    pass
```

#### 8.3.2 代码文档
```python
def process_ad_data(data: List[Dict[str, Any]], 
                   platform: str,
                   validate: bool = True) -> ProcessResult:
    """处理广告数据
    
    对原始广告数据进行清洗、验证和标准化处理。
    
    Args:
        data: 原始广告数据列表，每个元素为包含广告指标的字典
        platform: 数据来源平台名称，如'baidu'、'sogou'等
        validate: 是否进行数据验证，默认为True
    
    Returns:
        ProcessResult: 处理结果，包含成功数量、失败数量和错误信息
    
    Raises:
        ValidationError: 当数据验证失败时抛出
        ProcessingError: 当数据处理过程中发生错误时抛出
    
    Example:
        >>> data = [{'impressions': 100, 'clicks': 10, 'cost': 50.0}]
        >>> result = process_ad_data(data, 'baidu')
        >>> print(result.success_count)
        1
    """
    pass
```

## 9. 总结

本开发需求文档详细定义了TK BI Demo项目的技术架构、模块设计、开发规范和部署策略。通过模块化、可扩展的设计，确保系统能够稳定可靠地运行，并支持未来的功能扩展和平台接入。

### 9.1 核心优势
- **模块化设计**: 清晰的模块划分，便于开发和维护
- **可扩展性**: 支持新平台的快速接入
- **高可用性**: 完善的错误处理和监控机制
- **标准化**: 统一的开发规范和API设计
- **可测试性**: 完整的测试策略和工具

### 9.2 技术特色
- 异步编程提高并发性能
- 插件化架构支持灵活扩展
- 事件驱动架构提高系统解耦
- 完善的监控和日志系统
- 容器化部署简化运维

### 9.3 后续规划
- 支持更多广告平台接入
- 增加实时数据分析功能
- 优化数据存储和查询性能
- 增加机器学习算法支持
- 完善用户权限管理系统