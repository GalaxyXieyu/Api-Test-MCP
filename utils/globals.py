# @time:    2024-08-16
# @author:  xiaoqq

import threading

class Globals:
    """
    全局变量管理，线程安全
    """
    _instance = None
    _lock = threading.Lock()
    _data = {}

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Globals, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_data(cls):
        with cls._lock:
            return cls._data.copy()

    @classmethod
    def set(cls, key, value):
        with cls._lock:
            # 仅在数据发生变化时才进行设置
            if cls._data.get(key) != value:
                cls._data[key] = value

    @classmethod
    def get(cls, key):
        with cls._lock:
            return cls._data.get(key)

    @classmethod
    def update(cls, key, sub_key, sub_value):
        with cls._lock:
            if key in cls._data:
                if isinstance(cls._data[key], dict):
                    cls._data[key][sub_key] = sub_value
                else:
                    raise ValueError(f"Cannot update non-dict item in Globals: {key}")
            else:
                raise KeyError(f"Key {key} not found in Globals")

    @classmethod
    def clear(cls):
        with cls._lock:
            cls._data.clear()