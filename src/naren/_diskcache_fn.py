import hashlib
import logging
import pickle
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

_LOGGER = logging.getLogger(__name__)


def _arg_hash(args: Tuple[Any], kwargs: Dict[str, Any]) -> str:
    """
    Generate a hash key from function arguments.

    This function takes the positional and keyword arguments of a function call,
    serializes them using pickle, and then generates an MD5 hash of the serialized data.
    This hash serves as a unique identifier for the specific combination of arguments.

    Args:
        args (Tuple[Any]): A tuple containing all positional arguments.
        kwargs (Dict[str, Any]): A dictionary containing all keyword arguments.

    Returns:
        str: A hexadecimal string representation of the MD5 hash of the arguments.

    Note:
        This function assumes that all arguments are picklable. If any argument cannot
        be pickled, it will raise a TypeError.
    """
    key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()
    return key


def diskcache_fn(
    cache_dir: Optional[Path] | Optional[str] = None,
) -> Callable[..., Any]:
    """
    Decorator for caching function results on disk.

    This decorator caches the result of a function call to disk, allowing subsequent
    calls with the same arguments to retrieve the cached result instead of re-executing
    the function. This can significantly improve performance for expensive computations
    or I/O-bound operations that are called repeatedly with the same inputs.

    Args:
        cache_dir (Optional[Path] | Optional[str], optional): The directory to store
            cache files. If None, uses a temporary directory. If a string is provided,
            it's converted to a Path object. Defaults to None.

    Returns:
        Callable: A decorator function that can be applied to other functions.

    Example:
        @diskcache_fn()
        def expensive_function(x, y):
            # Some expensive computation
            return x + y

    Note:
        The function must be deterministic, pure and function's arguments must be picklable for the caching to work correctly.
    """

    def inner(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Dict[str, Any]) -> Any:
            key = _arg_hash(args, kwargs)

            cache_path: Path
            if cache_dir is None:
                cache_path = Path(tempfile.gettempdir()) / "py_fn_cache"
            elif isinstance(cache_dir, str):
                cache_path = Path(cache_dir)
            else:
                cache_path = cache_dir

            cache_file = cache_path / f"{func.__name__}_{key}.pkl"
            _LOGGER.debug(f"{func.__name__} cache key: {key}")

            if cache_file.exists():
                _LOGGER.debug(
                    f"Loading {func.__name__}({args}, {kwargs}) results from {cache_file}"
                )
                with open(cache_file, "rb") as f:
                    return pickle.load(f)
            else:
                result = func(*args, **kwargs)
                _LOGGER.debug(
                    f"Caching {func.__name__}({args}, {kwargs}) results to {cache_file}"
                )
                cache_path.mkdir(parents=True, exist_ok=True)
                with open(cache_file, "wb") as f:
                    pickle.dump(result, f, protocol=pickle.HIGHEST_PROTOCOL)
            return result

        return wrapper

    return inner
