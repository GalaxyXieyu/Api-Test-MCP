# 简单的加法函数，用于测试
def add(a: int, b: int) -> int:
    """加法函数"""
    return a + b


def subtract(a: int, b: int) -> int:
    """减法函数"""
    return a - b


class Calculator:
    """计算器类"""

    def __init__(self, name: str = "Basic Calculator"):
        self.name = name
        self.history = []

    def multiply(self, a: int, b: int) -> int:
        """乘法"""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result

    def divide(self, a: int, b: int) -> float:
        """除法"""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
