import importlib
import os
from functools import lru_cache


def _default_runtime_module() -> str:
    return "example.common.config"


@lru_cache(maxsize=1)
def load_runtime_module():
    module_name = os.getenv("ENGINE_RUNTIME_MODULE", _default_runtime_module())
    return importlib.import_module(module_name)


def get_engine():
    return load_runtime_module().engine


def get_whatsapp():
    return load_runtime_module().whatsapp
