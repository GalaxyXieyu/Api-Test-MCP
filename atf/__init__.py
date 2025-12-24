"""API Test Framework
自动化测试框架主包

使用延迟导入，避免在导入 atf 包时加载所有依赖。
"""

from importlib import import_module

__version__ = '1.0.0'
__package_name__ = 'atf'

__all__ = [
    "Globals",
    "ConfigManager",
    "LogManager",
    "RequestHandler",
    "VariableResolver",
    "AssertHandler",
    "LoginHandler",
    "CaseGenerator",
    "run_tests",
]

_LAZY_IMPORTS = {
    "Globals": "atf.core.globals",
    "ConfigManager": "atf.core.config_manager",
    "LogManager": "atf.core.log_manager",
    "RequestHandler": "atf.core.request_handler",
    "VariableResolver": "atf.core.variable_resolver",
    "AssertHandler": "atf.core.assert_handler",
    "LoginHandler": "atf.core.login_handler",
    "CaseGenerator": "atf.case_generator",
    "run_tests": "atf.runner",
}


def __getattr__(name):
    module_path = _LAZY_IMPORTS.get(name)
    if not module_path:
        raise AttributeError(f"module 'atf' has no attribute '{name}'")
    module = import_module(module_path)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(list(globals().keys()) + list(_LAZY_IMPORTS.keys()))
