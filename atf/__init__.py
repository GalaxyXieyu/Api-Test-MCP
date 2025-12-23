# API Test Framework
# 自动化测试框架主包

from .core.globals import Globals
from .core.config_manager import ConfigManager
from .core.log_manager import LogManager
from .core.request_handler import RequestHandler
from .core.variable_resolver import VariableResolver
from .core.assert_handler import AssertHandler
from .core.login_handler import LoginHandler
from .case_generator import CaseGenerator
from .runner import run_tests

__version__ = '1.0.0'
__package_name__ = 'atf'
__all__ = [
    'Globals',
    'ConfigManager',
    'LogManager',
    'RequestHandler',
    'VariableResolver',
    'AssertHandler',
    'LoginHandler',
    'CaseGenerator',
    'run_tests',
]
