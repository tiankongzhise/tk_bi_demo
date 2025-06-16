"""任务调度服务模块

提供异步任务调度、管理和监控功能。
"""

import asyncio
from typing import Dict, List, Optional, Callable, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json
from dataclasses import dataclass, asdict

from sqlalchemy import select, insert, update
from croniter import croniter

from ..core import (
    get_database,
    get_logger,
    TaskException
)
from ..models import (
    TaskLog,
    TaskStatusEnum,
    TaskConfig,
    TaskResult,
    PlatformEnum
)

logger = get_logger(__name__)


class TaskType(Enum):
    """任务类型枚举"""
    DATA_COLLECTION = "data_collection"
    DATA_PROCESSING = "data_processing"
    DATA_CLEANUP = "data_cleanup"
    HEALTH_CHECK = "health_check"
    REPORT_GENERATION = "report_generation"
    SYSTEM_MAINTENANCE = "system_maintenance"


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Task:
    """任务数据类"""
    id: str
    name: str
    task_type: TaskType
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    priority: TaskPriority = TaskPriority.NORMAL
    max_retries: int = 3
    retry_delay: float = 60.0
    timeout: Optional[float] = None
    cron_expression: Optional[str] = None
    platform: Optional[PlatformEnum] = None
    created_at: datetime = None
    scheduled_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class TaskExecution:
    """任务执行记录"""
    task_id: str
    execution_id: str
    status: TaskStatusEnum
    start_time: datetime
    end_time: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    
    def __post_init__(self):
        if self.execution_id is None:
            self.execution_id = str(uuid.uuid4())


class TaskScheduler:
    """任务调度器
    
    提供任务的调度、执行、重试和监控功能。
    """
    
    def __init__(self, max_concurrent_tasks: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.db_manager = get_database()
        
        # 任务存储
        self._tasks: Dict[str, Task] = {}
        self._scheduled_tasks: Dict[str, Task] = {}
        self._running_tasks: Dict[str, TaskExecution] = {}
        
        # 任务队列（按优先级排序）
        self._task_queue: List[Task] = []
        
        # 控制标志
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._worker_tasks: List[asyncio.Task] = []
        
        # 同步锁
        self._queue_lock = asyncio.Lock()
        self._tasks_lock = asyncio.Lock()
    
    async def start(self) -> None:
        """启动任务调度器"""
        if self._running:
            return
        
        self._running = True
        
        # 启动调度器主循环
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        # 启动工作线程
        for i in range(self.max_concurrent_tasks):
            worker_task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self._worker_tasks.append(worker_task)
        
        logger.info(
            "任务调度器已启动",
            extra={
                "max_concurrent_tasks": self.max_concurrent_tasks,
                "worker_count": len(self._worker_tasks)
            }
        )
    
    async def stop(self) -> None:
        """停止任务调度器"""
        if not self._running:
            return
        
        self._running = False
        
        # 停止调度器主循环
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        # 停止所有工作线程
        for worker_task in self._worker_tasks:
            worker_task.cancel()
        
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        
        self._worker_tasks.clear()
        
        logger.info("任务调度器已停止")
    
    async def add_task(
        self,
        name: str,
        func: Callable,
        task_type: TaskType = TaskType.DATA_COLLECTION,
        args: tuple = (),
        kwargs: dict = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        retry_delay: float = 60.0,
        timeout: Optional[float] = None,
        platform: Optional[PlatformEnum] = None,
        scheduled_at: Optional[datetime] = None
    ) -> str:
        """添加一次性任务
        
        Args:
            name: 任务名称
            func: 任务函数
            task_type: 任务类型
            args: 位置参数
            kwargs: 关键字参数
            priority: 优先级
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            timeout: 超时时间（秒）
            platform: 关联平台
            scheduled_at: 计划执行时间
            
        Returns:
            str: 任务ID
        """
        task_id = str(uuid.uuid4())
        
        task = Task(
            id=task_id,
            name=name,
            task_type=task_type,
            func=func,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            platform=platform,
            scheduled_at=scheduled_at
        )
        
        async with self._tasks_lock:
            self._tasks[task_id] = task
        
        # 如果是立即执行的任务，加入队列
        if scheduled_at is None or scheduled_at <= datetime.now():
            await self._enqueue_task(task)
        else:
            # 否则加入计划任务
            self._scheduled_tasks[task_id] = task
        
        logger.info(
            f"任务已添加: {name}",
            extra={
                "task_id": task_id,
                "task_type": task_type.value,
                "priority": priority.value,
                "scheduled_at": scheduled_at.isoformat() if scheduled_at else None
            }
        )
        
        return task_id
    
    async def add_cron_task(
        self,
        name: str,
        func: Callable,
        cron_expression: str,
        task_type: TaskType = TaskType.DATA_COLLECTION,
        args: tuple = (),
        kwargs: dict = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        retry_delay: float = 60.0,
        timeout: Optional[float] = None,
        platform: Optional[PlatformEnum] = None
    ) -> str:
        """添加定时任务
        
        Args:
            name: 任务名称
            func: 任务函数
            cron_expression: Cron表达式
            task_type: 任务类型
            args: 位置参数
            kwargs: 关键字参数
            priority: 优先级
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            timeout: 超时时间（秒）
            platform: 关联平台
            
        Returns:
            str: 任务ID
        """
        # 验证Cron表达式
        try:
            croniter(cron_expression)
        except Exception as e:
            raise TaskException(
                f"无效的Cron表达式: {cron_expression}, 错误: {e}",
                task_id="",
                error_code=3001
            )
        
        task_id = str(uuid.uuid4())
        
        task = Task(
            id=task_id,
            name=name,
            task_type=task_type,
            func=func,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            cron_expression=cron_expression,
            platform=platform
        )
        
        async with self._tasks_lock:
            self._tasks[task_id] = task
            self._scheduled_tasks[task_id] = task
        
        logger.info(
            f"定时任务已添加: {name}",
            extra={
                "task_id": task_id,
                "cron_expression": cron_expression,
                "task_type": task_type.value
            }
        )
        
        return task_id
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功取消
        """
        async with self._tasks_lock:
            # 从任务列表中移除
            if task_id in self._tasks:
                del self._tasks[task_id]
            
            # 从计划任务中移除
            if task_id in self._scheduled_tasks:
                del self._scheduled_tasks[task_id]
            
            # 从队列中移除
            async with self._queue_lock:
                self._task_queue = [t for t in self._task_queue if t.id != task_id]
            
            # 如果任务正在运行，标记为取消
            if task_id in self._running_tasks:
                execution = self._running_tasks[task_id]
                execution.status = TaskStatusEnum.CANCELLED
                execution.end_time = datetime.now()
                
                # 记录到数据库
                await self._log_task_execution(execution)
                
                del self._running_tasks[task_id]
                
                logger.info(f"正在运行的任务已取消: {task_id}")
                return True
        
        logger.info(f"任务已取消: {task_id}")
        return True
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Dict[str, Any]]: 任务状态信息
        """
        # 检查是否在运行中
        if task_id in self._running_tasks:
            execution = self._running_tasks[task_id]
            return {
                "task_id": task_id,
                "status": execution.status.value,
                "start_time": execution.start_time.isoformat(),
                "retry_count": execution.retry_count
            }
        
        # 检查任务是否存在
        if task_id in self._tasks:
            task = self._tasks[task_id]
            
            # 检查是否在队列中
            async with self._queue_lock:
                in_queue = any(t.id == task_id for t in self._task_queue)
            
            if in_queue:
                return {
                    "task_id": task_id,
                    "status": "queued",
                    "created_at": task.created_at.isoformat(),
                    "scheduled_at": task.scheduled_at.isoformat() if task.scheduled_at else None
                }
            
            # 检查是否是计划任务
            if task_id in self._scheduled_tasks:
                return {
                    "task_id": task_id,
                    "status": "scheduled",
                    "created_at": task.created_at.isoformat(),
                    "cron_expression": task.cron_expression
                }
        
        # 从数据库查询历史记录
        try:
            async with self.db_manager.get_session() as session:
                query = select(TaskLog).where(
                    TaskLog.task_id == task_id
                ).order_by(TaskLog.start_time.desc()).limit(1)
                
                result = await session.execute(query)
                log_record = result.scalar_one_or_none()
                
                if log_record:
                    return {
                        "task_id": task_id,
                        "status": log_record.status,
                        "start_time": log_record.start_time.isoformat(),
                        "end_time": log_record.end_time.isoformat() if log_record.end_time else None,
                        "error_message": log_record.error_message
                    }
        
        except Exception as e:
            logger.error(f"查询任务状态失败: {e}")
        
        return None
    
    async def get_task_statistics(self) -> Dict[str, Any]:
        """获取任务统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        async with self._queue_lock:
            queue_size = len(self._task_queue)
        
        running_count = len(self._running_tasks)
        scheduled_count = len(self._scheduled_tasks)
        total_tasks = len(self._tasks)
        
        # 按优先级统计队列
        priority_stats = {}
        async with self._queue_lock:
            for task in self._task_queue:
                priority = task.priority.name
                priority_stats[priority] = priority_stats.get(priority, 0) + 1
        
        return {
            "total_tasks": total_tasks,
            "queued_tasks": queue_size,
            "running_tasks": running_count,
            "scheduled_tasks": scheduled_count,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "priority_distribution": priority_stats,
            "scheduler_running": self._running
        }
    
    async def _scheduler_loop(self) -> None:
        """调度器主循环"""
        logger.info("调度器主循环已启动")
        
        while self._running:
            try:
                await self._check_scheduled_tasks()
                await asyncio.sleep(10)  # 每10秒检查一次
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"调度器循环错误: {e}")
                await asyncio.sleep(5)
        
        logger.info("调度器主循环已停止")
    
    async def _check_scheduled_tasks(self) -> None:
        """检查计划任务"""
        now = datetime.now()
        tasks_to_execute = []
        
        async with self._tasks_lock:
            for task_id, task in list(self._scheduled_tasks.items()):
                should_execute = False
                
                if task.cron_expression:
                    # Cron任务
                    cron = croniter(task.cron_expression, now)
                    next_run = cron.get_prev(datetime)
                    
                    # 检查是否应该在当前时间窗口执行
                    if (now - next_run).total_seconds() < 60:  # 1分钟窗口
                        should_execute = True
                
                elif task.scheduled_at and task.scheduled_at <= now:
                    # 一次性计划任务
                    should_execute = True
                    # 移除一次性计划任务
                    del self._scheduled_tasks[task_id]
                
                if should_execute:
                    tasks_to_execute.append(task)
        
        # 将需要执行的任务加入队列
        for task in tasks_to_execute:
            await self._enqueue_task(task)
    
    async def _enqueue_task(self, task: Task) -> None:
        """将任务加入队列"""
        async with self._queue_lock:
            # 按优先级插入
            inserted = False
            for i, queued_task in enumerate(self._task_queue):
                if task.priority.value > queued_task.priority.value:
                    self._task_queue.insert(i, task)
                    inserted = True
                    break
            
            if not inserted:
                self._task_queue.append(task)
        
        logger.debug(f"任务已加入队列: {task.name} (优先级: {task.priority.name})")
    
    async def _worker_loop(self, worker_name: str) -> None:
        """工作线程循环"""
        logger.debug(f"工作线程已启动: {worker_name}")
        
        while self._running:
            try:
                # 从队列获取任务
                task = await self._dequeue_task()
                if task is None:
                    await asyncio.sleep(1)
                    continue
                
                # 执行任务
                await self._execute_task(task, worker_name)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"工作线程错误 ({worker_name}): {e}")
                await asyncio.sleep(1)
        
        logger.debug(f"工作线程已停止: {worker_name}")
    
    async def _dequeue_task(self) -> Optional[Task]:
        """从队列获取任务"""
        async with self._queue_lock:
            if self._task_queue:
                return self._task_queue.pop(0)
        return None
    
    async def _execute_task(self, task: Task, worker_name: str) -> None:
        """执行任务"""
        execution = TaskExecution(
            task_id=task.id,
            execution_id=str(uuid.uuid4()),
            status=TaskStatusEnum.RUNNING,
            start_time=datetime.now()
        )
        
        # 记录开始执行
        self._running_tasks[task.id] = execution
        
        logger.info(
            f"开始执行任务: {task.name}",
            extra={
                "task_id": task.id,
                "execution_id": execution.execution_id,
                "worker": worker_name,
                "task_type": task.task_type.value
            }
        )
        
        try:
            # 执行任务函数
            if task.timeout:
                result = await asyncio.wait_for(
                    task.func(*task.args, **task.kwargs),
                    timeout=task.timeout
                )
            else:
                result = await task.func(*task.args, **task.kwargs)
            
            # 任务成功完成
            execution.status = TaskStatusEnum.COMPLETED
            execution.result = result
            execution.end_time = datetime.now()
            
            logger.info(
                f"任务执行成功: {task.name}",
                extra={
                    "task_id": task.id,
                    "execution_id": execution.execution_id,
                    "duration": (execution.end_time - execution.start_time).total_seconds()
                }
            )
        
        except asyncio.TimeoutError:
            execution.status = TaskStatusEnum.FAILED
            execution.error = f"任务超时 (>{task.timeout}秒)"
            execution.end_time = datetime.now()
            
            logger.error(
                f"任务执行超时: {task.name}",
                extra={
                    "task_id": task.id,
                    "timeout": task.timeout
                }
            )
        
        except Exception as e:
            execution.status = TaskStatusEnum.FAILED
            execution.error = str(e)
            execution.end_time = datetime.now()
            
            logger.error(
                f"任务执行失败: {task.name}, 错误: {e}",
                extra={
                    "task_id": task.id,
                    "error": str(e)
                }
            )
            
            # 检查是否需要重试
            if execution.retry_count < task.max_retries:
                execution.retry_count += 1
                
                logger.info(
                    f"任务将重试: {task.name} (第{execution.retry_count}次)",
                    extra={
                        "task_id": task.id,
                        "retry_count": execution.retry_count,
                        "max_retries": task.max_retries
                    }
                )
                
                # 延迟后重新加入队列
                await asyncio.sleep(task.retry_delay)
                await self._enqueue_task(task)
        
        finally:
            # 记录执行结果
            await self._log_task_execution(execution)
            
            # 从运行任务中移除
            if task.id in self._running_tasks:
                del self._running_tasks[task.id]
    
    async def _log_task_execution(self, execution: TaskExecution) -> None:
        """记录任务执行日志"""
        try:
            task = self._tasks.get(execution.task_id)
            if not task:
                return
            
            log_data = {
                "task_id": execution.task_id,
                "execution_id": execution.execution_id,
                "task_name": task.name,
                "task_type": task.task_type.value,
                "platform": task.platform.value if task.platform else None,
                "status": execution.status.value,
                "start_time": execution.start_time,
                "end_time": execution.end_time,
                "duration": (
                    (execution.end_time - execution.start_time).total_seconds()
                    if execution.end_time else None
                ),
                "retry_count": execution.retry_count,
                "error_message": execution.error,
                "result_data": (
                    json.dumps(execution.result, default=str, ensure_ascii=False)
                    if execution.result else None
                )
            }
            
            async with self.db_manager.get_session() as session:
                stmt = insert(TaskLog).values(log_data)
                await session.execute(stmt)
                await session.commit()
        
        except Exception as e:
            logger.error(f"记录任务执行日志失败: {e}")


# 全局任务调度器实例
_task_scheduler = None


async def get_task_scheduler() -> TaskScheduler:
    """获取任务调度器实例
    
    Returns:
        TaskScheduler: 任务调度器实例
    """
    global _task_scheduler
    if _task_scheduler is None:
        _task_scheduler = TaskScheduler()
    return _task_scheduler


async def start_scheduler() -> None:
    """启动任务调度器"""
    scheduler = await get_task_scheduler()
    await scheduler.start()


async def stop_scheduler() -> None:
    """停止任务调度器"""
    global _task_scheduler
    if _task_scheduler:
        await _task_scheduler.stop()
        _task_scheduler = None