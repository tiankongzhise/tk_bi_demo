"""API路由模块

定义所有API端点和路由。
"""

import json
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from aiohttp import web, ClientSession
from aiohttp.web import Request, Response, json_response
from aiohttp_cors import setup as cors_setup, ResourceOptions

from ..core import (
    get_logger,
    get_config,
    get_database_manager,
    DatabaseException,
    PlatformAPIException,
    ValidationException
)
from ..models import (
    PlatformEnum,
    TaskStatusEnum,
    APIResponse,
    AdReportModel,
    TaskConfig,
    HealthCheckResult,
    BatchRequest,
    BatchResponse
)
from ..services import (
    get_http_client_manager,
    get_data_processor,
    get_task_scheduler
)
from ..adapters import get_platform_adapter
from ..utils import (
    validate_ad_data,
    validate_task_config,
    ValidationError,
    parse_date,
    get_date_range,
    get_last_n_days
)

logger = get_logger(__name__)


class APIError(Exception):
    """API错误异常"""
    
    def __init__(self, message: str, status_code: int = 400, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)


def create_error_response(message: str, status_code: int = 400, error_code: str = None) -> Response:
    """创建错误响应
    
    Args:
        message: 错误消息
        status_code: HTTP状态码
        error_code: 错误代码
        
    Returns:
        Response: 错误响应
    """
    response_data = APIResponse(
        success=False,
        message=message,
        error_code=error_code
    )
    return json_response(
        response_data.dict(),
        status=status_code
    )


def create_success_response(data: Any = None, message: str = "操作成功") -> Response:
    """创建成功响应
    
    Args:
        data: 响应数据
        message: 成功消息
        
    Returns:
        Response: 成功响应
    """
    response_data = APIResponse(
        success=True,
        message=message,
        data=data
    )
    return json_response(response_data.dict())


async def error_middleware(request: Request, handler) -> Response:
    """错误处理中间件
    
    Args:
        request: 请求对象
        handler: 处理器
        
    Returns:
        Response: 响应
    """
    try:
        return await handler(request)
    
    except APIError as e:
        logger.warning(
            f"API错误: {e.message}",
            extra={
                "path": request.path,
                "method": request.method,
                "status_code": e.status_code,
                "error_code": e.error_code
            }
        )
        return create_error_response(e.message, e.status_code, e.error_code)
    
    except ValidationError as e:
        logger.warning(
            f"验证错误: {e.message}",
            extra={
                "path": request.path,
                "method": request.method,
                "field": e.field,
                "value": e.value
            }
        )
        return create_error_response(str(e), 400, "VALIDATION_ERROR")
    
    except ValidationException as e:
        logger.warning(
            f"数据验证异常: {e.message}",
            extra={
                "path": request.path,
                "method": request.method,
                "error_code": e.error_code
            }
        )
        return create_error_response(e.message, 400, e.error_code)
    
    except DatabaseException as e:
        logger.error(
            f"数据库异常: {e.message}",
            extra={
                "path": request.path,
                "method": request.method,
                "error_code": e.error_code
            }
        )
        return create_error_response("数据库操作失败", 500, e.error_code)
    
    except PlatformAPIException as e:
        logger.error(
            f"平台API异常: {e.message}",
            extra={
                "path": request.path,
                "method": request.method,
                "platform": e.platform,
                "error_code": e.error_code
            }
        )
        return create_error_response(f"平台API调用失败: {e.message}", 502, e.error_code)
    
    except Exception as e:
        logger.error(
            f"未处理的异常: {str(e)}",
            extra={
                "path": request.path,
                "method": request.method,
                "exception_type": type(e).__name__
            },
            exc_info=True
        )
        return create_error_response("内部服务器错误", 500, "INTERNAL_ERROR")


async def logging_middleware(request: Request, handler) -> Response:
    """日志记录中间件
    
    Args:
        request: 请求对象
        handler: 处理器
        
    Returns:
        Response: 响应
    """
    start_time = datetime.now()
    
    # 记录请求
    logger.info(
        f"API请求: {request.method} {request.path}",
        extra={
            "method": request.method,
            "path": request.path,
            "query_string": str(request.query_string),
            "remote_addr": request.remote,
            "user_agent": request.headers.get('User-Agent', '')
        }
    )
    
    # 处理请求
    response = await handler(request)
    
    # 计算处理时间
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # 记录响应
    logger.info(
        f"API响应: {request.method} {request.path} - {response.status}",
        extra={
            "method": request.method,
            "path": request.path,
            "status_code": response.status,
            "duration": duration,
            "response_size": len(response.body) if hasattr(response, 'body') else 0
        }
    )
    
    return response


# ==================== 健康检查API ====================

async def health_check(request: Request) -> Response:
    """健康检查
    
    Returns:
        Response: 健康检查结果
    """
    try:
        db_manager = get_database_manager()
        
        # 检查数据库连接
        db_healthy = await db_manager.health_check()
        
        # 检查HTTP客户端
        http_manager = get_http_client_manager()
        http_healthy = len(http_manager.clients) > 0
        
        # 检查任务调度器
        scheduler = get_task_scheduler()
        scheduler_healthy = scheduler.is_running
        
        overall_healthy = db_healthy and http_healthy and scheduler_healthy
        
        result = HealthCheckResult(
            healthy=overall_healthy,
            timestamp=datetime.now(),
            services={
                "database": db_healthy,
                "http_client": http_healthy,
                "task_scheduler": scheduler_healthy
            }
        )
        
        status_code = 200 if overall_healthy else 503
        return json_response(result.dict(), status=status_code)
    
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}", exc_info=True)
        result = HealthCheckResult(
            healthy=False,
            timestamp=datetime.now(),
            error=str(e)
        )
        return json_response(result.dict(), status=503)


# ==================== 广告数据API ====================

async def get_ad_data(request: Request) -> Response:
    """获取广告数据
    
    Query Parameters:
        platform: 平台名称
        account_id: 账户ID（可选）
        campaign_id: 广告计划ID（可选）
        start_date: 开始日期（YYYY-MM-DD）
        end_date: 结束日期（YYYY-MM-DD）
        limit: 限制数量（默认100）
        offset: 偏移量（默认0）
        
    Returns:
        Response: 广告数据列表
    """
    # 解析查询参数
    platform = request.query.get('platform')
    account_id = request.query.get('account_id')
    campaign_id = request.query.get('campaign_id')
    start_date = request.query.get('start_date')
    end_date = request.query.get('end_date')
    limit = int(request.query.get('limit', 100))
    offset = int(request.query.get('offset', 0))
    
    # 验证必填参数
    if not platform:
        raise APIError("缺少platform参数", 400, "MISSING_PARAMETER")
    
    # 验证平台
    try:
        PlatformEnum(platform)
    except ValueError:
        raise APIError(f"不支持的平台: {platform}", 400, "INVALID_PLATFORM")
    
    # 解析日期
    if start_date:
        start_date = parse_date(start_date)
        if not start_date:
            raise APIError("无效的开始日期格式", 400, "INVALID_DATE_FORMAT")
    
    if end_date:
        end_date = parse_date(end_date)
        if not end_date:
            raise APIError("无效的结束日期格式", 400, "INVALID_DATE_FORMAT")
    
    # 获取数据处理器
    data_processor = get_data_processor()
    
    # 构建查询条件
    filters = {"platform": platform}
    if account_id:
        filters["account_id"] = account_id
    if campaign_id:
        filters["campaign_id"] = campaign_id
    if start_date:
        filters["start_date"] = start_date
    if end_date:
        filters["end_date"] = end_date
    
    # 查询数据
    data, total = await data_processor.get_ad_data(
        filters=filters,
        limit=limit,
        offset=offset
    )
    
    return create_success_response({
        "data": data,
        "total": total,
        "limit": limit,
        "offset": offset
    })


async def sync_ad_data(request: Request) -> Response:
    """同步广告数据
    
    Request Body:
        {
            "platform": "baidu",
            "account_id": "123456",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "campaign_ids": ["campaign1", "campaign2"]  // 可选
        }
        
    Returns:
        Response: 同步结果
    """
    # 解析请求体
    try:
        data = await request.json()
    except Exception:
        raise APIError("无效的JSON格式", 400, "INVALID_JSON")
    
    # 验证必填字段
    required_fields = ['platform', 'account_id', 'start_date', 'end_date']
    for field in required_fields:
        if field not in data:
            raise APIError(f"缺少必填字段: {field}", 400, "MISSING_FIELD")
    
    platform = data['platform']
    account_id = data['account_id']
    start_date = parse_date(data['start_date'])
    end_date = parse_date(data['end_date'])
    campaign_ids = data.get('campaign_ids')
    
    # 验证平台
    try:
        PlatformEnum(platform)
    except ValueError:
        raise APIError(f"不支持的平台: {platform}", 400, "INVALID_PLATFORM")
    
    # 验证日期
    if not start_date or not end_date:
        raise APIError("无效的日期格式", 400, "INVALID_DATE_FORMAT")
    
    if start_date > end_date:
        raise APIError("开始日期不能大于结束日期", 400, "INVALID_DATE_RANGE")
    
    # 获取平台适配器
    adapter = get_platform_adapter(platform)
    if not adapter:
        raise APIError(f"平台 {platform} 适配器未找到", 500, "ADAPTER_NOT_FOUND")
    
    # 获取任务调度器
    scheduler = get_task_scheduler()
    
    # 创建同步任务
    task_config = TaskConfig(
        task_name=f"sync_{platform}_{account_id}_{start_date}_{end_date}",
        platform=platform,
        task_type="data_sync",
        config={
            "account_id": account_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "campaign_ids": campaign_ids
        }
    )
    
    # 添加任务
    task_id = await scheduler.add_task(
        task_config.task_name,
        _sync_ad_data_task,
        platform=platform,
        account_id=account_id,
        start_date=start_date,
        end_date=end_date,
        campaign_ids=campaign_ids
    )
    
    return create_success_response({
        "task_id": task_id,
        "message": "数据同步任务已创建"
    })


async def _sync_ad_data_task(platform: str, account_id: str, start_date: date, end_date: date, campaign_ids: Optional[List[str]] = None):
    """同步广告数据任务
    
    Args:
        platform: 平台名称
        account_id: 账户ID
        start_date: 开始日期
        end_date: 结束日期
        campaign_ids: 广告计划ID列表
    """
    try:
        # 获取平台适配器
        adapter = get_platform_adapter(platform)
        if not adapter:
            raise PlatformAPIException(f"平台 {platform} 适配器未找到", platform)
        
        # 获取数据处理器
        data_processor = get_data_processor()
        
        # 获取日期范围
        date_list = get_date_range(start_date, end_date)
        
        total_processed = 0
        total_errors = 0
        
        for report_date in date_list:
            try:
                # 获取报表数据
                raw_data = await adapter.get_report_data(
                    account_id=account_id,
                    start_date=report_date,
                    end_date=report_date,
                    campaign_ids=campaign_ids
                )
                
                if raw_data:
                    # 处理数据
                    processed_count = await data_processor.process_raw_data(
                        raw_data,
                        platform,
                        report_date
                    )
                    total_processed += processed_count
                    
                    logger.info(
                        f"平台 {platform} 账户 {account_id} 日期 {report_date} 数据同步完成",
                        extra={
                            "platform": platform,
                            "account_id": account_id,
                            "report_date": report_date.isoformat(),
                            "processed_count": processed_count
                        }
                    )
            
            except Exception as e:
                total_errors += 1
                logger.error(
                    f"平台 {platform} 账户 {account_id} 日期 {report_date} 数据同步失败: {str(e)}",
                    extra={
                        "platform": platform,
                        "account_id": account_id,
                        "report_date": report_date.isoformat(),
                        "error": str(e)
                    }
                )
        
        logger.info(
            f"数据同步任务完成",
            extra={
                "platform": platform,
                "account_id": account_id,
                "date_range": f"{start_date} - {end_date}",
                "total_processed": total_processed,
                "total_errors": total_errors
            }
        )
    
    except Exception as e:
        logger.error(
            f"数据同步任务失败: {str(e)}",
            extra={
                "platform": platform,
                "account_id": account_id,
                "date_range": f"{start_date} - {end_date}"
            },
            exc_info=True
        )
        raise


# ==================== 任务管理API ====================

async def get_tasks(request: Request) -> Response:
    """获取任务列表
    
    Query Parameters:
        status: 任务状态（可选）
        platform: 平台名称（可选）
        limit: 限制数量（默认50）
        offset: 偏移量（默认0）
        
    Returns:
        Response: 任务列表
    """
    # 解析查询参数
    status = request.query.get('status')
    platform = request.query.get('platform')
    limit = int(request.query.get('limit', 50))
    offset = int(request.query.get('offset', 0))
    
    # 验证状态
    if status:
        try:
            TaskStatusEnum(status)
        except ValueError:
            raise APIError(f"无效的任务状态: {status}", 400, "INVALID_STATUS")
    
    # 验证平台
    if platform:
        try:
            PlatformEnum(platform)
        except ValueError:
            raise APIError(f"不支持的平台: {platform}", 400, "INVALID_PLATFORM")
    
    # 获取任务调度器
    scheduler = get_task_scheduler()
    
    # 构建过滤条件
    filters = {}
    if status:
        filters['status'] = status
    if platform:
        filters['platform'] = platform
    
    # 获取任务列表
    tasks, total = await scheduler.get_tasks(
        filters=filters,
        limit=limit,
        offset=offset
    )
    
    return create_success_response({
        "tasks": tasks,
        "total": total,
        "limit": limit,
        "offset": offset
    })


async def get_task(request: Request) -> Response:
    """获取任务详情
    
    Path Parameters:
        task_id: 任务ID
        
    Returns:
        Response: 任务详情
    """
    task_id = request.match_info.get('task_id')
    if not task_id:
        raise APIError("缺少任务ID", 400, "MISSING_TASK_ID")
    
    # 获取任务调度器
    scheduler = get_task_scheduler()
    
    # 获取任务详情
    task = await scheduler.get_task(task_id)
    if not task:
        raise APIError("任务不存在", 404, "TASK_NOT_FOUND")
    
    return create_success_response(task)


async def cancel_task(request: Request) -> Response:
    """取消任务
    
    Path Parameters:
        task_id: 任务ID
        
    Returns:
        Response: 取消结果
    """
    task_id = request.match_info.get('task_id')
    if not task_id:
        raise APIError("缺少任务ID", 400, "MISSING_TASK_ID")
    
    # 获取任务调度器
    scheduler = get_task_scheduler()
    
    # 取消任务
    success = await scheduler.cancel_task(task_id)
    if not success:
        raise APIError("任务取消失败或任务不存在", 400, "CANCEL_FAILED")
    
    return create_success_response({"message": "任务已取消"})


# ==================== 统计API ====================

async def get_statistics(request: Request) -> Response:
    """获取统计信息
    
    Query Parameters:
        platform: 平台名称（可选）
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
        
    Returns:
        Response: 统计信息
    """
    # 解析查询参数
    platform = request.query.get('platform')
    start_date = request.query.get('start_date')
    end_date = request.query.get('end_date')
    
    # 验证平台
    if platform:
        try:
            PlatformEnum(platform)
        except ValueError:
            raise APIError(f"不支持的平台: {platform}", 400, "INVALID_PLATFORM")
    
    # 解析日期
    if start_date:
        start_date = parse_date(start_date)
        if not start_date:
            raise APIError("无效的开始日期格式", 400, "INVALID_DATE_FORMAT")
    
    if end_date:
        end_date = parse_date(end_date)
        if not end_date:
            raise APIError("无效的结束日期格式", 400, "INVALID_DATE_FORMAT")
    
    # 获取数据处理器
    data_processor = get_data_processor()
    
    # 获取统计信息
    stats = await data_processor.get_statistics(
        platform=platform,
        start_date=start_date,
        end_date=end_date
    )
    
    return create_success_response(stats)


# ==================== 批量操作API ====================

async def batch_operation(request: Request) -> Response:
    """批量操作
    
    Request Body:
        {
            "operation": "sync" | "delete" | "export",
            "items": [
                {
                    "platform": "baidu",
                    "account_id": "123456",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31"
                }
            ]
        }
        
    Returns:
        Response: 批量操作结果
    """
    # 解析请求体
    try:
        data = await request.json()
        batch_request = BatchRequest(**data)
    except Exception as e:
        raise APIError(f"无效的请求格式: {str(e)}", 400, "INVALID_REQUEST")
    
    # 获取任务调度器
    scheduler = get_task_scheduler()
    
    results = []
    
    for item in batch_request.items:
        try:
            if batch_request.operation == "sync":
                # 创建同步任务
                task_id = await scheduler.add_task(
                    f"batch_sync_{item.get('platform')}_{item.get('account_id')}",
                    _sync_ad_data_task,
                    **item
                )
                results.append({
                    "item": item,
                    "success": True,
                    "task_id": task_id
                })
            
            elif batch_request.operation == "delete":
                # 删除数据
                data_processor = get_data_processor()
                deleted_count = await data_processor.delete_data(item)
                results.append({
                    "item": item,
                    "success": True,
                    "deleted_count": deleted_count
                })
            
            elif batch_request.operation == "export":
                # 导出数据
                data_processor = get_data_processor()
                export_url = await data_processor.export_data(item)
                results.append({
                    "item": item,
                    "success": True,
                    "export_url": export_url
                })
            
            else:
                results.append({
                    "item": item,
                    "success": False,
                    "error": f"不支持的操作: {batch_request.operation}"
                })
        
        except Exception as e:
            results.append({
                "item": item,
                "success": False,
                "error": str(e)
            })
    
    # 统计结果
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    
    response = BatchResponse(
        operation=batch_request.operation,
        total_count=total_count,
        success_count=success_count,
        results=results
    )
    
    return create_success_response(response.dict())


# ==================== 路由配置 ====================

def setup_routes(app: web.Application) -> None:
    """设置路由
    
    Args:
        app: aiohttp应用实例
    """
    # 健康检查
    app.router.add_get('/health', health_check)
    
    # 广告数据API
    app.router.add_get('/api/v1/ad-data', get_ad_data)
    app.router.add_post('/api/v1/ad-data/sync', sync_ad_data)
    
    # 任务管理API
    app.router.add_get('/api/v1/tasks', get_tasks)
    app.router.add_get('/api/v1/tasks/{task_id}', get_task)
    app.router.add_delete('/api/v1/tasks/{task_id}', cancel_task)
    
    # 统计API
    app.router.add_get('/api/v1/statistics', get_statistics)
    
    # 批量操作API
    app.router.add_post('/api/v1/batch', batch_operation)


def create_app() -> web.Application:
    """创建aiohttp应用
    
    Returns:
        web.Application: aiohttp应用实例
    """
    # 创建应用
    app = web.Application(
        middlewares=[
            logging_middleware,
            error_middleware
        ]
    )
    
    # 设置路由
    setup_routes(app)
    
    # 设置CORS
    cors = cors_setup(app, defaults={
        "*": ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })
    
    # 为所有路由添加CORS
    for route in list(app.router.routes()):
        cors.add(route)
    
    logger.info("API应用创建完成")
    return app