from typing import Any, Callable

from bloomerp.celery.utils import is_celery_available


def run_async_or_sync(func:Callable, *args, **kwargs) -> tuple[bool, Any]:
    """Tries to run a function a synchronously, and if that doesn't work, runs it synchronously.

    Args:
        func (Callable): the function to run

    Returns:
        tuple[bool, Any]: 
            - bool: True if the function was run asynchronously, False if it was run synchronously
            - Any: the result of the function call
    """
    if is_celery_available():
        pass
    
    return False, func(*args, **kwargs)
    