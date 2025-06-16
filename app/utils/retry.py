"""重试机制工具模块

提供异步和同步的重试装饰器功能。
"""

import asyncio
import functools
import random
import time
from typing import Callable, Type, Union, Tuple, Any, Optional
from datetime import datetime, timedelta

from ..core import get_logger

logger = get_logger(__name__)


def retry_async(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: bool = True,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    on_retry: Optional[Callable] = None
):
    """异步重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 退避倍数
        jitter: 是否添加随机抖动
        exceptions: 需要重试的异常类型
        on_retry: 重试时的回调函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # 最后一次尝试失败，抛出异常
                        logger.error(
                            f"函数 {func.__name__} 重试{max_attempts}次后仍然失败",
                            extra={
                                "function": func.__name__,
                                "attempts": max_attempts,
                                "final_error": str(e)
                            }
                        )
                        raise e
                    
                    # 计算延迟时间
                    current_delay = delay * (backoff ** attempt)
                    
                    # 添加随机抖动
                    if jitter:
                        current_delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        f"函数 {func.__name__} 第{attempt + 1}次尝试失败，{current_delay:.2f}秒后重试",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_attempts": max_attempts,
                            "delay": current_delay,
                            "error": str(e)
                        }
                    )
                    
                    # 调用重试回调
                    if on_retry:
                        try:
                            if asyncio.iscoroutinefunction(on_retry):
                                await on_retry(attempt + 1, e, current_delay)
                            else:
                                on_retry(attempt + 1, e, current_delay)
                        except Exception as callback_error:
                            logger.error(f"重试回调函数执行失败: {callback_error}")
                    
                    # 等待后重试
                    await asyncio.sleep(current_delay)
                
                except Exception as e:
                    # 不在重试范围内的异常，直接抛出
                    logger.error(
                        f"函数 {func.__name__} 遇到不可重试的异常",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "error": str(e),
                            "error_type": type(e).__name__
                        }
                    )
                    raise e
            
            # 理论上不会到达这里
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def retry_sync(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: bool = True,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    on_retry: Optional[Callable] = None
):
    """同步重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 退避倍数
        jitter: 是否添加随机抖动
        exceptions: 需要重试的异常类型
        on_retry: 重试时的回调函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # 最后一次尝试失败，抛出异常
                        logger.error(
                            f"函数 {func.__name__} 重试{max_attempts}次后仍然失败",
                            extra={
                                "function": func.__name__,
                                "attempts": max_attempts,
                                "final_error": str(e)
                            }
                        )
                        raise e
                    
                    # 计算延迟时间
                    current_delay = delay * (backoff ** attempt)
                    
                    # 添加随机抖动
                    if jitter:
                        current_delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        f"函数 {func.__name__} 第{attempt + 1}次尝试失败，{current_delay:.2f}秒后重试",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_attempts": max_attempts,
                            "delay": current_delay,
                            "error": str(e)
                        }
                    )
                    
                    # 调用重试回调
                    if on_retry:
                        try:
                            on_retry(attempt + 1, e, current_delay)
                        except Exception as callback_error:
                            logger.error(f"重试回调函数执行失败: {callback_error}")
                    
                    # 等待后重试
                    time.sleep(current_delay)
                
                except Exception as e:
                    # 不在重试范围内的异常，直接抛出
                    logger.error(
                        f"函数 {func.__name__} 遇到不可重试的异常",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "error": str(e),
                            "error_type": type(e).__name__
                        }
                    )
                    raise e
            
            # 理论上不会到达这里
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


class RetryManager:
    """重试管理器
    
    提供更灵活的重试控制功能。
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        max_delay: float = 60.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff = backoff
        self.max_delay = max_delay
        self.jitter = jitter
        
        # 统计信息
        self.total_attempts = 0
        self.total_successes = 0
        self.total_failures = 0
        self.retry_history = []
    
    async def execute_async(
        self,
        func: Callable,
        *args,
        exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
        **kwargs
    ) -> Any:
        """异步执行函数并重试
        
        Args:
            func: 要执行的函数
            *args: 位置参数
            exceptions: 需要重试的异常类型
            **kwargs: 关键字参数
            
        Returns:
            Any: 函数执行结果
        """
        start_time = datetime.now()
        last_exception = None
        
        for attempt in range(self.max_attempts):
            self.total_attempts += 1
            attempt_start = datetime.now()
            
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # 成功执行
                self.total_successes += 1
                execution_time = (datetime.now() - start_time).total_seconds()
                
                self.retry_history.append({
                    "function": func.__name__,
                    "attempts": attempt + 1,
                    "success": True,
                    "execution_time": execution_time,
                    "timestamp": start_time.isoformat()
                })
                
                logger.debug(
                    f"函数 {func.__name__} 执行成功",
                    extra={
                        "function": func.__name__,
                        "attempts": attempt + 1,
                        "execution_time": execution_time
                    }
                )
                
                return result
            
            except exceptions as e:
                last_exception = e
                attempt_time = (datetime.now() - attempt_start).total_seconds()
                
                if attempt == self.max_attempts - 1:
                    # 最后一次尝试失败
                    self.total_failures += 1
                    total_time = (datetime.now() - start_time).total_seconds()
                    
                    self.retry_history.append({
                        "function": func.__name__,
                        "attempts": self.max_attempts,
                        "success": False,
                        "execution_time": total_time,
                        "error": str(e),
                        "timestamp": start_time.isoformat()
                    })
                    
                    logger.error(
                        f"函数 {func.__name__} 重试{self.max_attempts}次后仍然失败",
                        extra={
                            "function": func.__name__,
                            "attempts": self.max_attempts,
                            "total_time": total_time,
                            "final_error": str(e)
                        }
                    )
                    
                    raise e
                
                # 计算延迟时间
                current_delay = min(
                    self.delay * (self.backoff ** attempt),
                    self.max_delay
                )
                
                # 添加随机抖动
                if self.jitter:
                    current_delay *= (0.5 + random.random() * 0.5)
                
                logger.warning(
                    f"函数 {func.__name__} 第{attempt + 1}次尝试失败，{current_delay:.2f}秒后重试",
                    extra={
                        "function": func.__name__,
                        "attempt": attempt + 1,
                        "max_attempts": self.max_attempts,
                        "delay": current_delay,
                        "attempt_time": attempt_time,
                        "error": str(e)
                    }
                )
                
                # 等待后重试
                await asyncio.sleep(current_delay)
            
            except Exception as e:
                # 不在重试范围内的异常，直接抛出
                self.total_failures += 1
                total_time = (datetime.now() - start_time).total_seconds()
                
                self.retry_history.append({
                    "function": func.__name__,
                    "attempts": attempt + 1,
                    "success": False,
                    "execution_time": total_time,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "timestamp": start_time.isoformat()
                })
                
                logger.error(
                    f"函数 {func.__name__} 遇到不可重试的异常",
                    extra={
                        "function": func.__name__,
                        "attempt": attempt + 1,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
                
                raise e
        
        # 理论上不会到达这里
        if last_exception:
            raise last_exception
    
    def execute_sync(
        self,
        func: Callable,
        *args,
        exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
        **kwargs
    ) -> Any:
        """同步执行函数并重试
        
        Args:
            func: 要执行的函数
            *args: 位置参数
            exceptions: 需要重试的异常类型
            **kwargs: 关键字参数
            
        Returns:
            Any: 函数执行结果
        """
        start_time = datetime.now()
        last_exception = None
        
        for attempt in range(self.max_attempts):
            self.total_attempts += 1
            attempt_start = datetime.now()
            
            try:
                result = func(*args, **kwargs)
                
                # 成功执行
                self.total_successes += 1
                execution_time = (datetime.now() - start_time).total_seconds()
                
                self.retry_history.append({
                    "function": func.__name__,
                    "attempts": attempt + 1,
                    "success": True,
                    "execution_time": execution_time,
                    "timestamp": start_time.isoformat()
                })
                
                return result
            
            except exceptions as e:
                last_exception = e
                attempt_time = (datetime.now() - attempt_start).total_seconds()
                
                if attempt == self.max_attempts - 1:
                    # 最后一次尝试失败
                    self.total_failures += 1
                    total_time = (datetime.now() - start_time).total_seconds()
                    
                    self.retry_history.append({
                        "function": func.__name__,
                        "attempts": self.max_attempts,
                        "success": False,
                        "execution_time": total_time,
                        "error": str(e),
                        "timestamp": start_time.isoformat()
                    })
                    
                    raise e
                
                # 计算延迟时间
                current_delay = min(
                    self.delay * (self.backoff ** attempt),
                    self.max_delay
                )
                
                # 添加随机抖动
                if self.jitter:
                    current_delay *= (0.5 + random.random() * 0.5)
                
                # 等待后重试
                time.sleep(current_delay)
            
            except Exception as e:
                # 不在重试范围内的异常，直接抛出
                self.total_failures += 1
                raise e
        
        # 理论上不会到达这里
        if last_exception:
            raise last_exception
    
    def get_statistics(self) -> dict:
        """获取重试统计信息
        
        Returns:
            dict: 统计信息
        """
        success_rate = (
            (self.total_successes / self.total_attempts * 100)
            if self.total_attempts > 0 else 0
        )
        
        return {
            "total_attempts": self.total_attempts,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "success_rate": success_rate,
            "recent_history": self.retry_history[-10:]  # 最近10次记录
        }
    
    def reset_statistics(self) -> None:
        """重置统计信息"""
        self.total_attempts = 0
        self.total_successes = 0
        self.total_failures = 0
        self.retry_history.clear()


# 全局重试管理器实例
_global_retry_manager = RetryManager()


def get_retry_manager() -> RetryManager:
    """获取全局重试管理器
    
    Returns:
        RetryManager: 重试管理器实例
    """
    return _global_retry_manager