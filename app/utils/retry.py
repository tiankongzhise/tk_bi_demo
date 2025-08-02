import time
import functools
import asyncio
import inspect
import random
from typing import Callable, Optional, Any, Union, Tuple,Coroutine,Type
from tk_base_utils import load_toml
from ..logger import create_logger
logger = create_logger(__name__)


config = load_toml("config.toml")
max_attempts = config.get("max_retry", 3)
delay = config.get("delay", 1)


def retry(
    max_attempts: int = max_attempts,
    delay: Union[float, Callable[[int], float]] = delay,
    exceptions: Union[Tuple[Exception], Exception] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    raise_last: bool = True,
) -> Callable:
    """
    带有完整元数据保留的重试装饰器

    参数:
        max_attempts: 最大尝试次数（包括首次尝试）
        delay: 重试之间的延迟（秒），可以是固定值或接收当前尝试次数的函数
        exceptions: 触发重试的异常类型（单个异常或异常元组）
        on_retry: 重试发生时调用的回调函数（接收当前尝试次数和异常）
        raise_last: 是否在重试耗尽后重新抛出最后一个异常

    返回:
        包装后的函数，带有完整的元数据

    示例:
        @retry(max_attempts=3, delay=2, exceptions=ConnectionError)
        def connect_to_api():
            # 可能会抛出 ConnectionError
            ...
    """
    # 标准化异常类型为元组
    if not isinstance(exceptions, tuple):
        exceptions = (exceptions,)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)  # 保留原函数的元数据
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            attempts = 0

            while attempts < max_attempts:
                attempts += 1
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempts >= max_attempts:
                        break

                    # 计算延迟时间（固定值或动态函数）
                    current_delay = delay(attempts) if callable(delay) else delay

                    # 打印日志或调用回调函数
                    if on_retry:
                        on_retry(attempts, e)
                    logger.warning(
                        f"⚠️ 尝试 {attempts}/{max_attempts} 失败: {type(e).__name__}: {e}"
                    )
                    logger.info(f"⏳ {current_delay:.2f}秒后重试...")

                    # 应用延迟
                    time.sleep(current_delay)

            # 处理重试耗尽情况
            if raise_last and last_exception:
                # 增强异常信息
                if hasattr(last_exception, "add_note"):
                    last_exception.add_note(
                        f"🔄 重试失败: 在 {max_attempts} 次尝试后仍无法成功"
                    )
                logger.error(f"⚠️ 重试失败: 在 {max_attempts} 次尝试后仍无法成功,异常信息:{last_exception}")
                raise last_exception
            logger.error(f"⚠️ 重试失败: 在 {max_attempts} 次尝试后仍无法成功,异常信息:{last_exception}")
            return None  # 或不返回任何值，依情况而定

        return wrapper

    return decorator


def async_retry(
    max_attempts: int = max_attempts,
    delay: Union[float, Callable[[int], float]] = delay,
    exceptions: Union[Tuple[Type[Exception]], Type[Exception]] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], Optional[Coroutine]]] = None,
    raise_last: bool = True,
    jitter: Tuple[float, float] = (0.5, 1.5),
) -> Callable:
    """
    异步函数重试装饰器，保留原函数信息

    参数:
        max_attempts: 最大尝试次数（包括首次尝试）
        delay: 重试延迟（秒）| 接收当前尝试次数的函数返回延迟
        exceptions: 触发重试的异常类型（单个异常或异常元组）
        on_retry: 重试前调用的回调（可以是协程函数，支持第1次重试前的调用）
        raise_last: 是否在重试耗尽后重新抛出最后一个异常
        jitter: 延迟抖动范围（随机因子范围）

    示例:
        @async_retry(max_attempts=3, delay=0.5, exceptions=(ConnectionError,))
        async def fetch_data():
            # 可能失败的操作...
    """
    # 确保exceptions是元组
    if not isinstance(exceptions, tuple):
        exceptions = (exceptions,)

    # 确保jitter是有效范围
    if len(jitter) != 2 or jitter[0] > jitter[1]:
        jitter = (0.5, 1.5)

    def decorator(func: Callable[..., Coroutine]) -> Callable[..., Coroutine]:
        # 使用functools.wraps保留原函数信息
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            attempts = 0
            retry_delay = 0

            while attempts < max_attempts:
                attempts += 1

                try:
                    # 如果是第一次尝试或非重试延迟，直接执行函数
                    if attempts == 1 or retry_delay <= 0:
                        return await func(*args, **kwargs)

                    # 应用延迟
                    await asyncio.sleep(retry_delay)
                    return await func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    # 如果重试次数耗尽，退出循环
                    if attempts >= max_attempts:
                        break

                    # 计算下次重试的延迟（考虑抖动）
                    base_delay = delay(attempts) if callable(delay) else delay
                    jitter_factor = random.uniform(jitter[0], jitter[1])
                    retry_delay = base_delay * jitter_factor

                    # 处理重试回调
                    if on_retry:
                        result = on_retry(attempts, e)
                        # 如果回调返回协程，等待它完成
                        if inspect.iscoroutine(result):
                            await result
                    logger.warning(
                        f"⚠️ 尝试 {attempts}/{max_attempts} 失败: {type(e).__name__}: {e}"
                    )
                    logger.info(f"⏳ {retry_delay:.2f}秒后重试...")
            # 处理重试耗尽后的异常
            if raise_last and last_exception:
                # 添加重试信息到异常（Python 3.11+）
                if hasattr(last_exception, "add_note"):
                    last_exception.add_note(f"🔄 在 {max_attempts} 次尝试后重试失败")
                logger.error(f"⚠️ 重试失败: 在 {max_attempts} 次尝试后仍无法成功,异常信息:{last_exception}")
                raise last_exception

            # 返回None或不抛出异常（如果设置了raise_last=False）
            logger.error(f"⚠️ 重试失败: 在 {max_attempts} 次尝试后仍无法成功,异常信息:{last_exception}")
            return None

        return async_wrapper

    return decorator
