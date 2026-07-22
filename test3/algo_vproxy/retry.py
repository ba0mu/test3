import logging
import time

from thriftpy2.transport import TTransportException

logger = logging.getLogger()  # 获取外部日志记录器


class ExponentialBackoff:
    def __init__(self, min_ms=50):
        self.min_ms = min_ms

    def __call__(self, e):
        return self.calc_wait_ms(e)

    def calc_wait_ms(self, retried_times):
        return self.min_ms * (2 ** (retried_times - 1))


class EulerChecker:
    def __call__(self, e: Exception):
        return self.is_exception_retrievable(e)

    def is_exception_retrievable(self, e: Exception):
        if (
                isinstance(e, TTransportException)
                and e.type == TTransportException.NOT_OPEN
        ):
            return True

        return False


def safe_retry(
        max_tries: int = 3,
        retrievable_check: EulerChecker = EulerChecker(),
        backoff_calc: ExponentialBackoff = ExponentialBackoff(),
):
    """
    作为需要重试的函数装饰器 用法：@safe_retry()
    max_tries: 最大尝试次数，包含第一次的请求
    retrievable_check: 检测是否可重试
    backoff_calc: 计算退避时间
    """

    def wrapper(func):
        def inner(*args, **kwargs):
            def retry_call(retries=0):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if retries >= max_tries - 1:
                        raise

                    if not retrievable_check(e):
                        raise

                    logging.warning(f"Retrying {func.__name__} - Retry #{retries + 1} - Error: {str(e)}")
                    time.sleep(backoff_calc(retries) / 1000)
                    return retry_call(retries + 1)

            return retry_call()

        return inner

    return wrapper
